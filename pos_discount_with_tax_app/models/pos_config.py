# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class AccountInherit(models.Model):
	_inherit = 'account.account'
	
	discount_account = fields.Boolean('Discount Account')


class PosConfigInherit(models.Model):
	_inherit = 'pos.config'
	
	allow_order_disc = fields.Boolean('Allow Order Discount')
	order_discount_on = fields.Selection([('taxed', "Taxed Amount"), ('untaxed', "Untaxed Amount")],
										  string='Order Discount On', default='taxed')
	acc_account_id = fields.Many2one('account.account', 'Discount Account',
									 domain=[('account_type', '=', 'expense'), ('discount_account', '=', True)])
	disc_product_id = fields.Many2one("product.product", string="Discount Product",
									  domain=[('type', '=', 'service'), ('available_in_pos', '=', True)])


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	allow_order_disc = fields.Boolean(related='pos_config_id.allow_order_disc', readonly=False)
	order_discount_on = fields.Selection(related='pos_config_id.order_discount_on', readonly=False)
	acc_account_id = fields.Many2one(related='pos_config_id.acc_account_id', readonly=False,
									 domain=[('account_type', '=', 'expense'), ('discount_account', '=', True)])
	disc_product_id = fields.Many2one(related='pos_config_id.disc_product_id', readonly=False,
									  domain=[('type', '=', 'service'), ('available_in_pos', '=', True)])




class PosSession(models.Model):
	_inherit='pos.session'

	@api.model
	def discount_line_move_line_get(self,data):
		res = []
		account_id = False
		value = 0.0
		for order in self.order_ids:
			if order.discount_on == 'order':
				if order.order_discount:
					if order.config_id.acc_account_id:
						account_id = order.config_id.acc_account_id.id
					value += order.order_discount

		if account_id:
			disc_data = {
				'name': 'Order Discount',
				'debit': value,
				'move_id': self.move_id.id,
				'account_id': account_id or False,
				
			}
			MoveLine = data.get('MoveLine')
			MoveLine.create(disc_data)
		return data

	def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
		""" Create account.move and account.move.line records for this session.

		Side-effects include:
			- setting self.move_id to the created account.move record
			- creating and validating account.bank.statement for cash payments
			- reconciling cash receivable lines, invoice receivable lines and stock output lines
		"""
		journal = self.config_id.journal_id
		# Passing default_journal_id for the calculation of default currency of account move
		# See _get_default_currency in the account/account_move.py.
		account_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
			'journal_id': journal.id,
			'date': fields.Date.context_today(self),
			'ref': self.name,
		})
		self.write({'move_id': account_move.id})

		data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
		data = self._accumulate_amounts(data)
		data = self._create_non_reconciliable_move_lines(data)
		data = self._create_bank_payment_moves(data)
		data = self._create_pay_later_receivable_lines(data)
		data = self._create_cash_statement_lines_and_cash_move_lines(data)
		data = self._create_invoice_receivable_lines(data)
		data = self._create_stock_output_lines(data)
		data = self.discount_line_move_line_get(data)

		if balancing_account and amount_to_balance:
			data = self._create_balancing_line(data, balancing_account, amount_to_balance)

		return data

	def _prepare_line(self, order_line):
		""" Derive from order_line the order date, income account, amount and taxes information.

		These information will be used in accumulating the amounts for sales and tax lines.
		"""
		def get_income_account(order_line):
			product = order_line.product_id
			income_account = product.with_company(order_line.company_id)._get_product_accounts()['income']
			if not income_account:
				raise UserError(_('Please define income account for this product: "%s" (id:%d).')
								% (product.name, product.id))
			return order_line.order_id.fiscal_position_id.map_account(income_account)

		tax_ids = order_line.tax_ids_after_fiscal_position\
					.filtered(lambda t: t.company_id.id == order_line.order_id.company_id.id)
		sign = -1 if order_line.qty >= 0 else 1
		
		price = sign * order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
		
		if order_line.orderline_discount_type != 'percentage':
			price = sign * (order_line.price_unit - order_line.discount)
		
		# The 'is_refund' parameter is used to compute the tax tags. Ultimately, the tags are part
		# of the key used for summing taxes. Since the POS UI doesn't support the tags, inconsistencies
		# may arise in 'Round Globally'.
		check_refund = lambda x: x.qty * x.price_unit < 0
		is_refund = check_refund(order_line)
		tax_data = tax_ids.compute_all(price_unit=price, quantity=abs(order_line.qty), currency=self.currency_id, is_refund=is_refund, fixed_multiplicator=sign)
		taxes = tax_data['taxes']
		# For Cash based taxes, use the account from the repartition line immediately as it has been paid already
		for tax in taxes:
			tax_rep = self.env['account.tax.repartition.line'].browse(tax['tax_repartition_line_id'])
			tax['account_id'] = tax_rep.account_id.id
		date_order = order_line.order_id.date_order
		taxes = [{'date_order': date_order, **tax} for tax in taxes]
		return {
			'date_order': order_line.order_id.date_order,
			'income_account_id': get_income_account(order_line).id,
			'amount': order_line.price_subtotal,
			'taxes': taxes,
			'base_tags': tuple(tax_data['base_tags']),
		}