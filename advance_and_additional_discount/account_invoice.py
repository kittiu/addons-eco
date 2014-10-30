# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from common import AdditionalDiscountable
from openerp.tools.translate import _


class account_invoice(AdditionalDiscountable, osv.Model):

    _inherit = "account.invoice"
    _description = 'Invoice'
    _line_column = 'invoice_line'
    _tax_column = 'invoice_line_tax_id'

    def record_currency(self, record):
        """Return currency browse record from an invoice record (override)."""
        return record.currency_id

    def _amount_all(self, *args, **kwargs):
        return self._amount_invoice_generic(account_invoice, *args, **kwargs)

    def _get_invoice_line(self, cr, uid, ids, context=None):
        """copy pasted from account_invoice"""
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        """copy pasted from account_invoice"""
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
            'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
              },
              multi='all'),
            'add_disc': fields.float('Additional Discount(%)', digits_compute=dp.get_precision('Additional Discount'), readonly=True, states={'draft': [('readonly', False)]}),
            'add_disc_amt': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Additional Disc Amt',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="The additional discount on untaxed amount."),
            'amount_net': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Net Amount',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="The amount after additional discount."),
            # Advance
            'is_advance': fields.boolean('Advance'),
            'amount_advance': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Advance Amt',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="The advance amount to be deducted according to original percentage"),
            # Deposit
            'is_deposit': fields.boolean('Deposit'),
            'amount_deposit': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Deposit Amt',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="The deposit amount to be deducted in the second invoice according to original deposit"),

            'amount_beforetax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Before Taxes',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="Net amount after advance amount deduction"),
            # --
            'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
              },
              multi='all'),
            # Retention
            'is_retention': fields.boolean('Retention'),
            'amount_retention': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Retention Amt',
                store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="The amount to be retained according to retention percentage"),
            'amount_beforeretention': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Before Retention',
                store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
                  }, multi='all', help="Net amount after retention deduction"),

            'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
              store={
                  'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'add_disc'], 20),
                  'account.invoice.tax': (_get_invoice_tax, None, 20),
                  'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
              },
              multi='all'),
    }

    _defaults = {
       'add_disc': 0.0,
       'is_advance': False,
       'is_deposit': False,
       'is_retention': False
    }

    # For refund case, we also copy the Additional Discount. The rest are not copied yet.
    # To copy, we will need to set the relation between refund with SO. This is yet to decide.
    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        invoice_data = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        invoice_data.update({
            'add_disc': invoice.add_disc
        })
        return invoice_data

    def _reset_delivery_2binvoiced(self, cr, uid, ids, module_name, context=None):
        picking_pool = self.pool.get('stock.picking')
        picking_ids = picking_pool.search(cr, uid, [('invoice_ids', 'in', ids)], context)
        picking_obj = picking_pool.browse(cr, uid, picking_ids, context)
        order_id_name = (module_name == 'sale.order' and 'sale_id' or 'purchase_id')
        order_policy = (module_name == 'sale.order' and 'order_policy' or 'invoice_method')

        for picking in  picking_obj:
            if picking[order_id_name][order_policy] == 'picking':
                picking_pool.write(cr, uid, picking.id, {'invoice_state': '2binvoiced'}, context)
        return True

    def _reset_advance_type(self, cr, uid, ids, module_name, context=None):
        sale_obj = self.pool.get(module_name)

        sale_ids = sale_obj.search(cr, uid, [('invoice_ids', 'in', ids)])
        res = sale_obj._num_invoice(cr, uid, sale_ids, 'num_invoice', None, context)
        res = dict((key, value) for key, value in res.iteritems() if value > 1)

        if res:
            res = sale_obj.read(cr, uid, sale_ids, ['name'], context)
            raise osv.except_osv(
                            _('Advance/Deposit!'),
                            _('Unable to cancel this invoice.!\n First cancel all Invoice related to %s' % ','.join(x['name'] for x in res)))

        inv_ids = self.search(cr, uid, [('id', 'in', ids), ('is_deposit', '=', True)], context)
        if inv_ids:
            sale_ids = sale_obj.search(cr, uid, [('invoice_ids', 'in', inv_ids)])
            if sale_ids:
                sale_obj.write(cr, uid, sale_ids, {'amount_deposit': False})

        inv_ids = self.search(cr, uid, [('id', 'in', ids), ('is_advance', '=', True)], context)
        if inv_ids:
            sale_ids = sale_obj.search(cr, uid, [('invoice_ids', 'in', inv_ids)])
            if sale_ids:
                sale_obj.write(cr, uid, sale_ids, {'advance_amount': False})

    def action_cancel(self, cr, uid, ids, context=None):
        #Purchase
        inv_ids = self.search(cr, uid, [('type', '=', 'in_invoice'), ('id', 'in', ids), '|', ('is_deposit', '=', True),\
                                         ('is_advance', '=', True)], context)
        if inv_ids:
            self._reset_advance_type(cr, uid, ids, 'purchase.order', context)

        #Sale Order
        inv_ids = self.search(cr, uid, [('type', '=', 'out_invoice'), ('id', 'in', ids), '|', ('is_deposit', '=', True),\
                                        ('is_advance', '=', True)], context)
        if inv_ids:
            self._reset_advance_type(cr, uid, ids, 'sale.order', context)

        #Reset invoice_state in delivery order is 2binvoiced
        self._reset_delivery_2binvoiced(cr, uid, ids, 'sale.order', context)
        self._reset_delivery_2binvoiced(cr, uid, ids, 'purchase.order', context)
        super(account_invoice, self).action_cancel(cr, uid, ids, context)
        return True

account_invoice()


class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'

    _columns = {
        'is_advance': fields.boolean('Advance'),
        'is_deposit': fields.boolean('Deposit'),
    }

    _defaults = {
        'is_advance': False,
        'is_deposit': False,
    }

    # kittiu: also dr/cr advance, force creating new move_line
    def move_line_get(self, cr, uid, invoice_id, context=None):

        res = super(account_invoice_line, self).move_line_get(cr, uid, invoice_id, context=context)
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)

        if inv.add_disc_amt > 0.0:
            sign = -1
            #sign = inv.type in ('out_invoice','in_invoice') and -1 or 1
            # account code for advance
            prop = inv.type in ('out_invoice', 'out_refund') \
                        and self.pool.get('ir.property').get(cr, uid, 'property_account_add_disc_customer', 'res.partner', context=context) \
                        or self.pool.get('ir.property').get(cr, uid, 'property_account_add_disc_supplier', 'res.partner', context=context)
            prop_id = prop and prop.id or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)

            res.append({
                'type': 'src',
                'name': _('Additional Discount'),
                'price_unit': sign * inv.add_disc_amt,
                'quantity': 1,
                'price': sign * inv.add_disc_amt,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })

        if inv.amount_advance > 0.0:
            sign = -1
            #sign = inv.type in ('out_invoice','in_invoice') and -1 or 1
            # account code for advance
            prop = inv.type in ('out_invoice', 'out_refund') \
                        and self.pool.get('ir.property').get(cr, uid, 'property_account_advance_customer', 'res.partner', context=context) \
                        or self.pool.get('ir.property').get(cr, uid, 'property_account_advance_supplier', 'res.partner', context=context)
            prop_id = prop and prop.id or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)
            res.append({
                'type': 'src',
                'name': _('Advance Amount'),
                'price_unit': sign * inv.amount_advance,
                'quantity': 1,
                'price': sign * inv.amount_advance,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })

        if inv.amount_deposit > 0.0:
            sign = -1
            #sign = inv.type in ('out_invoice','in_invoice') and -1 or 1
            # account code for advance
            prop = inv.type in ('out_invoice', 'out_refund') \
                        and self.pool.get('ir.property').get(cr, uid, 'property_account_deposit_customer', 'res.partner', context=context) \
                        or self.pool.get('ir.property').get(cr, uid, 'property_account_deposit_supplier', 'res.partner', context=context)

            prop_id = prop and prop.id or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)

            res.append({
                'type': 'src',
                'name': _('Deposit Amount'),
                'price_unit': sign * inv.amount_deposit,
                'quantity': 1,
                'price': sign * inv.amount_deposit,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })

        if inv.amount_retention > 0.0:
            sign = -1
            #sign = inv.type in ('out_invoice','in_invoice') and -1 or 1
            # account code for advance
            prop = inv.type in ('out_invoice', 'out_refund') \
                        and self.pool.get('ir.property').get(cr, uid, 'property_account_retention_customer', 'res.partner', context=context) \
                        or self.pool.get('ir.property').get(cr, uid, 'property_account_retention_supplier', 'res.partner', context=context)
            prop_id = prop and prop.id or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)

            res.append({
                'type': 'src',
                'name': _('Retention Amount'),
                'price_unit': sign * inv.amount_retention,
                'quantity': 1,
                'price': sign * inv.amount_retention,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })

        return res
account_invoice_line()


class account_invoice_tax(osv.Model):

    _inherit = 'account.invoice.tax'

    def compute(self, cr, uid, invoice_id, context=None):
        invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        order_ids = invoice.sale_order_ids or invoice.purchase_order_ids
        # Percent Additional Discount
        add_disc = invoice.add_disc
        # Percent Advance
        advance = not invoice.is_advance and order_ids and (order_ids[0].advance_percentage) or 0.0
        # Percent Deposit
        deposit_amount = not invoice.is_deposit and invoice.amount_deposit or 0.0
        deposit = order_ids and invoice.amount_net and (deposit_amount / (invoice.amount_net) * 100) or 0.0
        tax_grouped = super(account_invoice_tax, self).compute_ex(cr, uid, invoice_id, add_disc, advance, deposit, context)

        return tax_grouped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
