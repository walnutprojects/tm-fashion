# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import fields, models, api, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError


class PosSession(models.Model):
    _inherit = "pos.session"

    def _accumulate_commission_amounts(self):
        # Accumulate the commission amounts for each payment method
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        payment_method_commissions = defaultdict(amounts)
        currency_rounding = self.currency_id.rounding
        for order in self.order_ids:
            for payment in order.payment_ids:
                if payment.amount > 0:
                    payment_method_id = payment.payment_method_id
                    commission_type = payment_method_id.commission_type
                    commission = payment_method_id.commission
                    if commission_type and commission:
                        amount = commission_type == 'fixed' and commission or payment.amount * commission / 100
                        if float_is_zero(amount, precision_rounding=currency_rounding):
                            continue
                        date = payment.payment_date
                        payment_method = payment.payment_method_id
                        payment_method_commissions[payment_method] = self._update_amounts(
                            payment_method_commissions[payment_method],
                            {'amount': amount}, date)

        return payment_method_commissions

    def _get_payment_commission_vals(self, payment_method, amount, amount_converted):
        if not payment_method.commission_account_id:
            raise ValidationError(_('Please configure commission account in the payment method !'))
        partial_vals = {
            'account_id': payment_method.commission_account_id.id,
            'move_id': self.commission_move_id.id,
            'partner_id': False,
            'name': '%s - %s Commission' % (self.name, payment_method.name),
        }
        return self._debit_amounts(partial_vals, amount, amount_converted)

    def _get_payment_commission_counterpart_vals(self, payment_method, amount, amount_converted):
        outstanding_account = payment_method.outstanding_account_id or self.company_id.account_journal_payment_debit_account_id
        partial_vals = {
            'account_id': outstanding_account.id,
            'move_id': self.commission_move_id.id,
            'partner_id': False,
            'name': '%s - %s Commission CR' % (self.name, payment_method.name),
        }
        return self._credit_amounts(partial_vals, amount, amount_converted)

    # NOTE: add sudo for move and move line creation to bypass rule: Purchase User Account Move / Line
    def _create_payment_commission_move_lines(self, data):
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
        vals = []
        for payment_method, amounts in data.items():
            vals.append(self._get_payment_commission_counterpart_vals(payment_method, amounts['amount'],
                                                                      amounts['amount_converted']))
            vals.append(
                self._get_payment_commission_vals(payment_method, amounts['amount'], amounts['amount_converted']))
        MoveLine.sudo().create(vals)
        return data

    def _create_payment_commission_moves(self):
        """ Create payment commission account.move and account.move.line records for this session."""
        journal = self.config_id.commission_journal_id
        if not journal:
            raise ValidationError(_('Please configure commission journal in the point of sale configuration.'))
        account_move = self.env['account.move'].with_context(default_journal_id=journal.id).sudo().create({
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'{self.name} - Payment Commissions',
        })
        self.write({'commission_move_id': account_move.id})

        data = self._accumulate_commission_amounts()
        data = self._create_payment_commission_move_lines(data)
        if account_move.line_ids:
            account_move.sudo().with_company(self.company_id)._post()
        return data

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)
        if self.move_id and self.move_id.line_ids:
            if 'account_analytic_id' in self.config_id._fields:
                self.with_context(pos_analytic=self.config_id.account_analytic_id.id)._create_payment_commission_moves()
            else:
                self._create_payment_commission_moves()
            if not self.commission_move_id.line_ids:
                self.commission_move_id.sudo().unlink()
        return res

    def _get_related_account_moves(self):
        res = super(PosSession, self)._get_related_account_moves()
        return res | self.commission_move_id

    def _create_stock_output_lines(self, data):
        return data

    def _accumulate_amounts(self, data):
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables_bank` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
        split_receivables_bank = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        split_receivables_pay_later = defaultdict(amounts)
        combine_receivables_bank = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        combine_receivables_pay_later = defaultdict(amounts)
        combine_invoice_receivables = defaultdict(amounts)
        split_invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the order's invoice payment moves for reconciliation
        # These receivable lines are reconciled to the corresponding invoice receivable lines
        # of this session's move_id.
        combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
        pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
        currency_rounding = self.currency_id.rounding
        for order in self.order_ids:
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                amount = payment.amount
                if float_is_zero(amount, precision_rounding=currency_rounding):
                    continue
                date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = payment.payment_method_id.split_transactions
                payment_type = payment_method.type

                # If not pay_later, we create the receivable vals for both invoiced and uninvoiced orders.
                #   Separate the split and aggregated payments.
                # Moreover, if the order is invoiced, we create the pos receivable vals that will balance the
                # pos receivable lines from the invoice payments.
                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = self._update_amounts(combine_receivables_cash[payment_method], {'amount': amount}, date)
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = self._update_amounts(combine_receivables_bank[payment_method], {'amount': amount}, date)

                    # Create the vals to create the pos receivables that will balance the pos receivables from invoice payment moves.
                    if order_is_invoiced:
                        if is_split_payment:
                            split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount}, order.date_order)
                        else:
                            combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount}, order.date_order)

                # If pay_later, we create the receivable lines.
                #   if split, with partner
                #   Otherwise, it's aggregated (combined)
                # But only do if order is *not* invoiced because no account move is created for pay later invoice payments.
                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = self._update_amounts(split_receivables_pay_later[payment], {'amount': amount}, date)
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = self._update_amounts(combine_receivables_pay_later[payment_method], {'amount': amount}, date)

            if not order_is_invoiced:
                order_taxes = defaultdict(tax_amounts)
                for order_line in order.lines:
                    line = self._prepare_line(order_line)
                    # Combine sales/refund lines
                    sale_key = (
                        # account
                        line['income_account_id'],
                        # sign
                        -1 if line['amount'] < 0 else 1,
                        # for taxes
                        tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
                        line['base_tags'],
                    )
                    sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
                    # Combine tax lines
                    for tax in line['taxes']:
                        tax_key = (tax['account_id'] or line['income_account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
                        order_taxes[tax_key] = self._update_amounts(
                            order_taxes[tax_key],
                            {'amount': tax['amount'], 'base_amount': tax['base']},
                            tax['date_order'],
                            round=not rounded_globally
                        )
                for tax_key, amounts in order_taxes.items():
                    if rounded_globally:
                        amounts = self._round_amounts(amounts)
                    for amount_key, amount in amounts.items():
                        taxes[tax_key][amount_key] += amount

                # if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
                #     # Combine stock lines
                #     stock_moves = self.env['stock.move'].sudo().search([
                #         ('picking_id', 'in', order.picking_ids.ids),
                #         ('company_id.anglo_saxon_accounting', '=', True),
                #         ('product_id.categ_id.property_valuation', '=', 'real_time')
                #     ])
                #     for move in stock_moves:
                #         exp_key = move.product_id._get_product_accounts()['expense']
                #         out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                #         amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
                #         stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                #         if move.location_id.usage == 'customer':
                #             stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                #         else:
                #             stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

                if self.config_id.cash_rounding:
                    diff = order.amount_paid - order.amount_total
                    rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

                # Increasing current partner's customer_rank
                partners = (order.partner_id | order.partner_id.commercial_partner_id)
                partners._increase_rank('customer_rank')

        # if self.company_id.anglo_saxon_accounting:
        #     global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
        #     if global_session_pickings:
        #         stock_moves = self.env['stock.move'].sudo().search([
        #             ('picking_id', 'in', global_session_pickings.ids),
        #             ('company_id.anglo_saxon_accounting', '=', True),
        #             ('product_id.categ_id.property_valuation', '=', 'real_time'),
        #         ])
        #         for move in stock_moves:
        #             exp_key = move.product_id._get_product_accounts()['expense']
        #             out_key = move.product_id.categ_id.property_stock_account_output_categ_id
        #             amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
        #             stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        #             if move.location_id.usage == 'customer':
        #                 stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        #             else:
        #                 stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

        data.update({
            'taxes':                               taxes,
            'sales':                               sales,
            'stock_expense':                       stock_expense,
            'split_receivables_bank':              split_receivables_bank,
            'combine_receivables_bank':            combine_receivables_bank,
            'split_receivables_cash':              split_receivables_cash,
            'combine_receivables_cash':            combine_receivables_cash,
            'combine_invoice_receivables':         combine_invoice_receivables,
            'split_receivables_pay_later':         split_receivables_pay_later,
            'combine_receivables_pay_later':       combine_receivables_pay_later,
            # 'stock_return':                        stock_return,
            # 'stock_output':                        stock_output,
            'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
            'rounding_difference':                 rounding_difference,
            'MoveLine':                            MoveLine,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
        })
        return data

    def _reconcile_account_move_lines(self, data):
        # reconcile cash receivable lines
        split_cash_statement_lines = data.get('split_cash_statement_lines')
        combine_cash_statement_lines = data.get('combine_cash_statement_lines')
        split_cash_receivable_lines = data.get('split_cash_receivable_lines')
        combine_cash_receivable_lines = data.get('combine_cash_receivable_lines')
        combine_inv_payment_receivable_lines = data.get('combine_inv_payment_receivable_lines')
        split_inv_payment_receivable_lines = data.get('split_inv_payment_receivable_lines')
        combine_invoice_receivable_lines = data.get('combine_invoice_receivable_lines')
        split_invoice_receivable_lines = data.get('split_invoice_receivable_lines')
        stock_output_lines = data.get('stock_output_lines')
        payment_method_to_receivable_lines = data.get('payment_method_to_receivable_lines')
        payment_to_receivable_lines = data.get('payment_to_receivable_lines')

        for statement in self.statement_ids:
            if not self.config_id.cash_control:
                statement.write({'balance_end_real': statement.balance_end})
            statement.button_post()
            all_lines = (
                  split_cash_statement_lines[statement]
                | combine_cash_statement_lines[statement]
                | split_cash_receivable_lines[statement]
                | combine_cash_receivable_lines[statement]
            )
            accounts = all_lines.mapped('account_id')
            lines_by_account = [all_lines.filtered(lambda l: l.account_id == account and not l.reconciled) for account in accounts if account.reconcile]
            for lines in lines_by_account:
                lines.reconcile()
            # We try to validate the statement after the reconciliation is done
            # because validating the statement requires each statement line to be
            # reconciled.
            # Furthermore, if the validation failed, which is caused by unreconciled
            # cash difference statement line, we just ignore that. Leaving the statement
            # not yet validated. Manual reconciliation and validation should be made
            # by the user in the accounting app.
            try:
                statement.button_validate()
            except UserError:
                pass

        for payment_method, lines in payment_method_to_receivable_lines.items():
            receivable_account = self._get_receivable_account(payment_method)
            if receivable_account.reconcile:
                lines.filtered(lambda line: not line.reconciled).reconcile()

        for payment, lines in payment_to_receivable_lines.items():
            if payment.partner_id.property_account_receivable_id.reconcile:
                lines.filtered(lambda line: not line.reconciled).reconcile()

        # Reconcile invoice payments' receivable lines. But we only do when the account is reconcilable.
        # Though `account_default_pos_receivable_account_id` should be of type receivable, there is currently
        # no constraint for it. Therefore, it is possible to put set a non-reconcilable account to it.
        if self.company_id.account_default_pos_receivable_account_id.reconcile:
            for payment_method in combine_inv_payment_receivable_lines:
                lines = combine_inv_payment_receivable_lines[payment_method] | combine_invoice_receivable_lines.get(payment_method, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).reconcile()

            for payment in split_inv_payment_receivable_lines:
                lines = split_inv_payment_receivable_lines[payment] | split_invoice_receivable_lines.get(payment, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).reconcile()

        # reconcile stock output lines
        # pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
        # pickings |= self.order_ids.filtered(lambda o: not o.is_invoiced).mapped('picking_ids')
        # stock_moves = self.env['stock.move'].search([('picking_id', 'in', pickings.ids)])
        # stock_account_move_lines = self.env['account.move'].search([('stock_move_id', 'in', stock_moves.ids)]).mapped('line_ids')
        # for account_id in stock_output_lines:
        #     ( stock_output_lines[account_id]
        #     | stock_account_move_lines.filtered(lambda aml: aml.account_id == account_id)
        #     ).filtered(lambda aml: not aml.reconciled).reconcile()
        return data

    commission_move_id = fields.Many2one('account.move', string='Payment Commission Journal Entry')
