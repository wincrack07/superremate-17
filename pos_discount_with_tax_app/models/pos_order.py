# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class PosOrderLineInherit(models.Model):
	_inherit = 'pos.order.line'

	orderline_discount_type = fields.Char('Discount Type')
	is_line_discount = fields.Boolean("IS Line Discount")

	@api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
	def _compute_amount_line_all(self):
		for line in self:
			fpos = line.order_id.fiscal_position_id
			tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids)
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			if line.orderline_discount_type == "fixed":
				price = line.price_unit - line.discount
			taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id)
			return {
				'price_subtotal_incl': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
				'taxes': taxes['taxes']
			}


class PosOrderInherit(models.Model):
	_inherit = 'pos.order'

	order_discount =  fields.Float(string='Order Discount', default = 0.0, readonly=True)
	order_discount_type = fields.Char('Order Discount Type')
	discount_on = fields.Char('Discount On')

	@api.model
	def _amount_line_tax(self, line, fiscal_position_id):
		taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
		taxes = fiscal_position_id.map_tax(taxes)
		if line.orderline_discount_type == 'percentage':
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
		else:
			price = line.price_unit - line.discount
		taxes = taxes.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)['taxes']
		return sum(tax.get('amount', 0.0) for tax in taxes)

	@api.model
	def _order_fields(self, ui_order):
		res = super(PosOrderInherit, self)._order_fields(ui_order)
		if 'discount_on' in ui_order :
			res['discount_on'] =  ui_order['discount_on']
		if 'discount_order' in ui_order :
			res['order_discount'] =  ui_order['discount_order']
		if 'order_discount_type' in ui_order :
			res['order_discount_type'] =  ui_order['order_discount_type']
		return res

	def _prepare_discount_invoice_line(self):
		return {
			'product_id': self.config_id.disc_product_id.id,
			'quantity': 1,
			'discount': 0,
			'price_unit': -self.order_discount,
			'name':  self.config_id.disc_product_id.display_name,
			'tax_ids': [(6, 0,[])],
			'product_uom_id': self.config_id.disc_product_id.uom_id.id,
		}

	def _prepare_invoice_vals(self):
		res = super(PosOrderInherit, self)._prepare_invoice_vals()
		res.update({
			'pos_order_id' : self.id,
			'order_discount': self.order_discount,
			'is_created_from_pos' : True,
			'discount_on' : self.discount_on,
		}) 
		if self.order_discount > 0 :
			disc_line = self._prepare_discount_invoice_line()
			inv_lines = res.get('invoice_line_ids')
			inv_lines.append((0, None, disc_line))
			res.update({
				'invoice_line_ids' : inv_lines,
			}) 
		return res

	def _prepare_invoice_line(self, order_line):
		res = super(PosOrderInherit, self)._prepare_invoice_line(order_line)
		res.update({
			'pos_order_id' : self.id,
			'pos_order_line_id' : order_line.id,
			'orderline_discount_type' : order_line.orderline_discount_type ,
			'is_created_from_pos' : True,
		}) 
		return res


	@api.model
	def _process_order(self, order, draft, existing_order):
		"""Create or update an pos.order from a given dictionary.

		:param dict order: dictionary representing the order.
		:param bool draft: Indicate that the pos_order is not validated yet.
		:param existing_order: order to be updated or False.
		:type existing_order: pos.order.
		:returns: id of created/updated pos.order
		:rtype: int
		"""
		order = order['data']
		pos_session = self.env['pos.session'].browse(order['pos_session_id'])
		if pos_session.state == 'closing_control' or pos_session.state == 'closed':
			order['pos_session_id'] = self._get_valid_session(order).id

		pos_order = False
		if not existing_order:
			pos_order = self.create(self._order_fields(order))
		else:
			pos_order = existing_order
			pos_order.lines.unlink()
			order['user_id'] = pos_order.user_id.id
			pos_order.write(self._order_fields(order))

		pos_order = pos_order.with_company(pos_order.company_id)
		self = self.with_company(pos_order.company_id)
		self._process_payment_lines(order, pos_order, pos_session, draft)

		if not draft:
			try:
				pos_order.action_pos_order_paid()
			except psycopg2.DatabaseError:
				# do not hide transactional errors, the order(s) won't be saved!
				raise
			except Exception as e:
				_logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
			pos_order._create_order_picking()
			pos_order._compute_total_cost_in_real_time()

		if pos_order.to_invoice and pos_order.state == 'paid':
			pos_order._generate_pos_order_invoice()
			if pos_order.discount_on == 'orderlines':
				invoice = pos_order.account_move
				for line in invoice.invoice_line_ids:
					pos_line = line.pos_order_line_id
					if pos_line and pos_line.orderline_discount_type == "fixed":
						line.write({'price_unit': pos_line.price_unit})
		return pos_order.id