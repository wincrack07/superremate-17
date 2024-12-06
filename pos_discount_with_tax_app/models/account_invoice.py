# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
import psycopg2
import pytz
from odoo import api, fields, models, _, Command
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
import odoo.addons.decimal_precision as dp
from collections import defaultdict
from odoo.tools.misc import formatLang
from odoo.tools import frozendict, formatLang, format_date, float_is_zero, float_compare


_logger = logging.getLogger(__name__)


class AccountInvoiceInherit(models.Model):
	_inherit = "account.move"

	pos_order_id = fields.Many2one('pos.order',string="POS order" ,readonly=True)
	order_discount = fields.Float("Discount",default=0.0 ,readonly=True)
	is_created_from_pos = fields.Boolean("Is Created From POS" ,readonly=True)
	discount_on = fields.Char('Discount On' ,readonly=True)


class AccountInvoiceLineInherit(models.Model):
	_inherit = "account.move.line"

	pos_order_id = fields.Many2one('pos.order',string="POS order" ,readonly=True)
	pos_order_line_id = fields.Many2one('pos.order.line',string="POS order Line" ,readonly=True)
	orderline_discount_type = fields.Char('Discount Type' ,readonly=True)
	is_created_from_pos = fields.Boolean("Is Created From POS" ,readonly=True)

	@api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
	def _compute_totals(self):
		for line in self:
			if line.display_type != 'product':
				line.price_total = line.price_subtotal = False
			# Compute 'price_subtotal'.
			line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))

			if line.orderline_discount_type  == "fixed":
				line_discount_price_unit = line.price_unit - line.discount
			
			subtotal = line.quantity * line_discount_price_unit

			# Compute 'price_total'.
			if line.tax_ids:
				taxes_res = line.tax_ids.compute_all(
					line_discount_price_unit,
					quantity=line.quantity,
					currency=line.currency_id,
					product=line.product_id,
					partner=line.partner_id,
					is_refund=line.is_refund,
				)
				line.price_subtotal = taxes_res['total_excluded']
				line.price_total = taxes_res['total_included']
			else:
				line.price_total = line.price_subtotal = subtotal

	@api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
	def _compute_all_tax(self):
		for line in self:
			sign = line.move_id.direction_sign
			if line.display_type == 'product' and line.move_id.is_invoice(True):
				amount_currency = sign * line.price_unit * (1 - line.discount / 100)
				amount = sign * line.price_unit / line.currency_rate * (1 - line.discount / 100)

				if line.orderline_discount_type  == "fixed":
					amount_currency = sign * line.price_unit - line.discount
					amount = sign * line.price_unit / line.currency_rate - line.discount

				handle_price_include = True
				quantity = line.quantity
			else:
				amount_currency = line.amount_currency
				amount = line.balance
				handle_price_include = False
				quantity = 1
			compute_all_currency = line.tax_ids.compute_all(
				amount_currency,
				currency=line.currency_id,
				quantity=quantity,
				product=line.product_id,
				partner=line.move_id.partner_id or line.partner_id,
				is_refund=line.is_refund,
				handle_price_include=handle_price_include,
				include_caba_tags=line.move_id.always_tax_exigible,
				fixed_multiplicator=sign,
			)
			rate = line.amount_currency / line.balance if line.balance else 1
			line.compute_all_tax_dirty = True
			line.compute_all_tax = {
				frozendict({
					'tax_repartition_line_id': tax['tax_repartition_line_id'],
					'group_tax_id': tax['group'] and tax['group'].id or False,
					'account_id': tax['account_id'] or line.account_id.id,
					'currency_id': line.currency_id.id,
					'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
					'tax_ids': [(6, 0, tax['tax_ids'])],
					'tax_tag_ids': [(6, 0, tax['tag_ids'])],
					'partner_id': line.move_id.partner_id.id or line.partner_id.id,
					'move_id': line.move_id.id,
				}): {
					'name': tax['name'],
					'balance': tax['amount'] / rate,
					'amount_currency': tax['amount'],
					'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
				}
				for tax in compute_all_currency['taxes']
				if tax['amount']
			}
			if not line.tax_repartition_line_id:
				line.compute_all_tax[frozendict({'id': line.id})] = {
					'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
				}



class AccountTax(models.Model):
	_inherit = "account.tax"

	@api.model
	def _compute_taxes_for_single_line(self, base_line, handle_price_include=True, include_caba_tags=False, early_pay_discount_computation=None, early_pay_discount_percentage=None):
		orig_price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))
		if base_line.get('record',False):
			line = base_line.get('record',False)
			if line.orderline_discount_type  == "fixed":
				orig_price_unit_after_discount = base_line['price_unit'] - base_line['discount'] 

		price_unit_after_discount = orig_price_unit_after_discount
		taxes = base_line['taxes']._origin
		currency = base_line['currency'] or self.env.company.currency_id
		rate = base_line['rate']

		if early_pay_discount_computation in ('included', 'excluded'):
			remaining_part_to_consider = (100 - early_pay_discount_percentage) / 100.0
			price_unit_after_discount = remaining_part_to_consider * price_unit_after_discount

		if taxes:

			if handle_price_include is None:
				manage_price_include = bool(base_line['handle_price_include'])
			else:
				manage_price_include = handle_price_include

			taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
				price_unit_after_discount,
				currency=currency,
				quantity=base_line['quantity'],
				product=base_line['product'],
				partner=base_line['partner'],
				is_refund=base_line['is_refund'],
				handle_price_include=manage_price_include,
				include_caba_tags=include_caba_tags,
			)

			to_update_vals = {
				'tax_tag_ids': [Command.set(taxes_res['base_tags'])],
				'price_subtotal': taxes_res['total_excluded'],
				'price_total': taxes_res['total_included'],
			}

			if early_pay_discount_computation == 'excluded':
				new_taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
					orig_price_unit_after_discount,
					currency=currency,
					quantity=base_line['quantity'],
					product=base_line['product'],
					partner=base_line['partner'],
					is_refund=base_line['is_refund'],
					handle_price_include=manage_price_include,
					include_caba_tags=include_caba_tags,
				)
				for tax_res, new_taxes_res in zip(taxes_res['taxes'], new_taxes_res['taxes']):
					delta_tax = new_taxes_res['amount'] - tax_res['amount']
					tax_res['amount'] += delta_tax
					to_update_vals['price_total'] += delta_tax

			tax_values_list = []
			for tax_res in taxes_res['taxes']:
				tax_rep = self.env['account.tax.repartition.line'].browse(tax_res['tax_repartition_line_id'])
				tax_values_list.append({
					**tax_res,
					'tax_repartition_line': tax_rep,
					'base_amount_currency': tax_res['base'],
					'base_amount': currency.round(tax_res['base'] / rate),
					'tax_amount_currency': tax_res['amount'],
					'tax_amount': currency.round(tax_res['amount'] / rate),
				})

		else:
			price_subtotal = currency.round(price_unit_after_discount * base_line['quantity'])
			to_update_vals = {
				'tax_tag_ids': [Command.clear()],
				'price_subtotal': price_subtotal,
				'price_total': price_subtotal,
			}
			tax_values_list = []

		return to_update_vals, tax_values_list

	@api.model
	def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
		""" Compute the tax totals details for the business documents.
		:param base_lines:  A list of python dictionaries created using the '_convert_to_tax_base_line_dict' method.
		:param currency:    The currency set on the business document.
		:param tax_lines:   Optional list of python dictionaries created using the '_convert_to_tax_line_dict' method.
							If specified, the taxes will be recomputed using them instead of recomputing the taxes on
							the provided base lines.
		:return: A dictionary in the following form:
			{
				'amount_total':                 The total amount to be displayed on the document, including every total
												types.
				'amount_untaxed':               The untaxed amount to be displayed on the document.
				'formatted_amount_total':       Same as amount_total, but as a string formatted accordingly with
												partner's locale.
				'formatted_amount_untaxed':     Same as amount_untaxed, but as a string formatted accordingly with
												partner's locale.
				'groups_by_subtotals':          A dictionary formed liked {'subtotal': groups_data}
												Where total_type is a subtotal name defined on a tax group, or the
												default one: 'Untaxed Amount'.
												And groups_data is a list of dict in the following form:
					{
						'tax_group_name':                   The name of the tax groups this total is made for.
						'tax_group_amount':                 The total tax amount in this tax group.
						'tax_group_base_amount':            The base amount for this tax group.
						'formatted_tax_group_amount':       Same as tax_group_amount, but as a string formatted accordingly
															with partner's locale.
						'formatted_tax_group_base_amount':  Same as tax_group_base_amount, but as a string formatted
															accordingly with partner's locale.
						'tax_group_id':                     The id of the tax group corresponding to this dict.
					}
				'subtotals':                    A list of dictionaries in the following form, one for each subtotal in
												'groups_by_subtotals' keys.
					{
						'name':                             The name of the subtotal
						'amount':                           The total amount for this subtotal, summing all the tax groups
															belonging to preceding subtotals and the base amount
						'formatted_amount':                 Same as amount, but as a string formatted accordingly with
															partner's locale.
					}
				'subtotals_order':              A list of keys of `groups_by_subtotals` defining the order in which it needs
												to be displayed
			}
		"""

		# ==== Compute the taxes ====

		line = False
		if base_lines and base_lines[0] and  base_lines[0].get('record',False):
			line = base_lines[0].get('record',False)

		order_discount = 0
		if line :
			order_discount = line.move_id.order_discount


		to_process = []
		for base_line in base_lines:
			to_update_vals, tax_values_list = self._compute_taxes_for_single_line(base_line)
			to_process.append((base_line, to_update_vals, tax_values_list))

		def grouping_key_generator(base_line, tax_values):
			source_tax = tax_values['tax_repartition_line'].tax_id
			return {'tax_group': source_tax.tax_group_id}

		global_tax_details = self._aggregate_taxes(to_process, grouping_key_generator=grouping_key_generator)

		tax_group_vals_list = []
		for tax_detail in global_tax_details['tax_details'].values():
			tax_group_vals = {
				'tax_group': tax_detail['tax_group'],
				'base_amount': tax_detail['base_amount_currency'],
				'tax_amount': tax_detail['tax_amount_currency'],
			}

			# Handle a manual edition of tax lines.
			if tax_lines is not None:
				matched_tax_lines = [
					x
					for x in tax_lines
					if (x['group_tax'] or x['tax_repartition_line'].tax_id).tax_group_id == tax_detail['tax_group']
				]
				if matched_tax_lines:
					tax_group_vals['tax_amount'] = sum(x['tax_amount'] for x in matched_tax_lines)

			tax_group_vals_list.append(tax_group_vals)

		tax_group_vals_list = sorted(tax_group_vals_list, key=lambda x: (x['tax_group'].sequence, x['tax_group'].id))

		# ==== Partition the tax group values by subtotals ====

		amount_untaxed = global_tax_details['base_amount_currency']
		amount_tax = 0.0

		subtotal_order = {}
		groups_by_subtotal = defaultdict(list)
		for tax_group_vals in tax_group_vals_list:
			tax_group = tax_group_vals['tax_group']

			subtotal_title = tax_group.preceding_subtotal or _("Untaxed Amount")
			sequence = tax_group.sequence

			subtotal_order[subtotal_title] = min(subtotal_order.get(subtotal_title, float('inf')), sequence)
			groups_by_subtotal[subtotal_title].append({
				'group_key': tax_group.id,
				'tax_group_id': tax_group.id,
				'tax_group_name': tax_group.name,
				'tax_group_amount': tax_group_vals['tax_amount'],
				'tax_group_base_amount': tax_group_vals['base_amount'],
				'formatted_tax_group_amount': formatLang(self.env, tax_group_vals['tax_amount'], currency_obj=currency),
				'formatted_tax_group_base_amount': formatLang(self.env, tax_group_vals['base_amount'], currency_obj=currency),
			})

		# ==== Build the final result ====

		subtotals = []
		for subtotal_title in sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]):
			amount_total = amount_untaxed + amount_tax
			subtotals.append({
				'name': subtotal_title,
				'amount': amount_total,
				'formatted_amount': formatLang(self.env, amount_total, currency_obj=currency),
			})
			amount_tax += sum(x['tax_group_amount'] for x in groups_by_subtotal[subtotal_title])

		amount_total = amount_untaxed + amount_tax

		display_tax_base = (len(global_tax_details['tax_details']) == 1 and tax_group_vals_list[0]['base_amount'] != amount_untaxed) \
			or len(global_tax_details['tax_details']) > 1

		return {
			'amount_untaxed': currency.round(amount_untaxed) if currency else amount_untaxed,
			'amount_total': currency.round(amount_total) if currency else amount_total,
			'formatted_amount_total': formatLang(self.env, amount_total, currency_obj=currency),
			'formatted_amount_untaxed': formatLang(self.env, amount_untaxed, currency_obj=currency),
			'groups_by_subtotal': groups_by_subtotal,
			'subtotals': subtotals,
			'subtotals_order': sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]),
			'display_tax_base': display_tax_base,
			'order_discount' : formatLang(self.env, order_discount, currency_obj=currency),
		}

	
			
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   