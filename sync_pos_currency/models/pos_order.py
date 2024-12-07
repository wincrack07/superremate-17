# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_multi_currency = fields.Boolean(related='config_id.multi_currency_payment', readonly=False)

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        result = super(PosOrder, self)._payment_fields(order,ui_paymentline)
        if ui_paymentline.get('currency_amount_total'):
            result.update({
                'selected_currency_rate': ui_paymentline.get('selected_currency_rate'),
                'selected_currency_symbol': ui_paymentline.get('selected_currency_symbol'),
                'currency_amount_total': ui_paymentline.get('currency_amount_total')
            })
        else:
            result.update({
                'currency_amount_total': ui_paymentline['amount'] or 0.0,
                'selected_currency_symbol': order.pricelist_id.currency_id.symbol
            })
        return result

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        prec_acc = order.pricelist_id.currency_id.decimal_places
        order_bank_statement_lines = self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
        order_bank_statement_lines.unlink()
        for payments in pos_order['statement_ids']:
            order.add_payment(self._payment_fields(order, payments[2]))

        order.amount_paid = sum(order.payment_ids.mapped('amount'))

        if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_payment_method = pos_session.payment_method_ids.filtered('is_cash_count')[:1]
            if not cash_payment_method:
                raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
            return_payment_vals = {
                'name': _('return'),
                'pos_order_id': order.id,
                'amount': -pos_order['amount_return'],
                'currency_amount_total': -pos_order['amount_return'],
                'selected_currency_symbol': order.pricelist_id.currency_id.symbol,
                'payment_date': fields.Datetime.now(),
                'payment_method_id': cash_payment_method.id,
                'is_change': True,
            }
            order.add_payment(return_payment_vals)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'check_from_pos' in self.env.context:
            res = super(ResCurrency, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
            for curr in res:
                currency_obj = self.browse([curr.get('id')])
                curr.update({
                    'rate': curr.get('inverse_rate'),
                    'inverse_rate': curr.get('rate'),
                })
            return res
        #     tag_ids = self._name_search('')
        #     domain = expression.AND([domain, [('id', 'in', tag_ids)]])
        #     return self.arrange_tag_list_by_id(super().search_read(domain=domain, fields=fields, offset=offset, limit=limit), tag_ids)
        return super(ResCurrency, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)