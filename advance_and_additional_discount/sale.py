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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from common import AdditionalDiscountable
import types


class sale_order(AdditionalDiscountable, osv.osv):

    _inherit = 'sale.order'
    _tax_column = 'tax_id'
    _line_column = 'order_line'

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('cancel'):
                #if invoice.state not in ('draft', 'cancel'):
                    # Do not add amount, it this is a deposit/advance
                    #tot += not invoice.is_deposit and not invoice.is_advance and invoice.amount_net  # kittiu: we use amount_net instead of amount_untaxed
                    # We change from amount_net back to amount_untaxed again, due to case #2059 (may need to double check)
                    tot += not invoice.is_deposit and not invoice.is_advance and invoice.amount_untaxed
            if tot:
                res[sale.id] = min(100.0, round(tot * 100.0 / (sale.amount_untaxed or 1.00)))  # <-- changed back to untaxed
            else:
                res[sale.id] = 0.0
        return res

    def _num_invoice(self, cursor, user, ids, name, args, context=None):
        '''Return the amount still to pay regarding all the payment orders'''
        if not ids:
            return {}
        res = dict.fromkeys(ids, False)

        cursor.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel, account_invoice AS inv ' + \
                'WHERE rel.invoice_id = inv.id AND inv.state <> \'cancel\' And rel.order_id in (%s)' % ','.join(str(x) for x in ids))
        invs = cursor.fetchall()

        for inv in invs:
            res[inv[0]] += 1
        return res

    def _amount_all(self, *args, **kwargs):
        return self._amount_all_generic(sale_order, *args, **kwargs)

    def _get_amount_retained(self, cr, uid, ids, field_names, arg, context=None):
        if context is None:
            context = {}

        res = {}
        currency_obj = self.pool.get('res.currency')
        sale_obj = self.pool.get('sale.order')

        # Account Retention
        prop = self.pool.get('ir.property').get(cr, uid, 'property_account_retention_customer', 'res.partner', context=context)
        prop_id = prop and prop.id or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, False, prop_id)
        if not account_id:
            for id in ids:
                res[id] = 0.0
        else:
            for id in ids:
                order = sale_obj.browse(cr, uid, id)
                cr.execute("""select sum(l.debit-l.credit) as amount_debit
                                from account_move_line l
                                inner join
                                (select order_id, move_id from account_invoice inv
                                inner join sale_order_invoice_rel rel
                                on inv.id = rel.invoice_id and order_id = %s) inv
                                on inv.move_id = l.move_id
                                where state = 'valid'
                                and account_id = %s
                                group by order_id
                              """, (order.id, account_id))
                amount_debit = cr.rowcount and cr.fetchone()[0] or 0.0
                amount = currency_obj.compute(cr, uid, order.company_id.currency_id.id, order.pricelist_id.currency_id.id, amount_debit)
                res[order.id] = amount

        return res

    _columns = {
            'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced Ratio', type='float'),
            # Additional Discount Feature
            'add_disc': fields.float('Additional Discount(%)', digits_compute=dp.get_precision('Additional Discount'), readonly=True, states={'draft': [('readonly', False)]}),
            'add_disc_amt': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Additional Disc Amt',
                                            store=True, multi='sums', help="The additional discount on untaxed amount."),
            'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                                              store=True, multi='sums', help="The amount without tax."),
            'amount_net': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Net Amount',
                                              store=True, multi='sums', help="The amount after additional discount."),
            'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Taxes',
                                          store=True, multi='sums', help="The tax amount."),
            'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                                            store=True, multi='sums', help="The total amount."),
            # Advance Feature
            'num_invoice': fields.function(_num_invoice, string="Number invoices created", store=False),
            'advance_type': fields.selection([('advance', 'Advance on 1st Invoice'), ('deposit', 'Deposit on 1st Invoice')], 'Advance Type',
                                             required=False, help="Deposit: Deducted full amount on the next invoice. Advance: Deducted in percentage on all following invoices."),
            'advance_percentage': fields.float('Advance (%)', digits=(16, 6), required=False, readonly=True),
            'amount_deposit': fields.float('Deposit Amount', readonly=True, digits_compute=dp.get_precision('Account')),
            # Retention Feature
            'retention_percentage': fields.float('Retention (%)', digits=(16, 6), required=False, readonly=True),
            'amount_retained': fields.function(_get_amount_retained, string='Retained Amount', type='float', readonly=True, digits_compute=dp.get_precision('Account'))
            #'amount_retained': fields.float('Retained Amount',readonly=True, digits_compute=dp.get_precision('Account'))

        }

    _defaults = {
            'add_disc': 0.0,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'advance_type': False,
            'amount_deposit': False,
            'advance_percentage': False,
            'retention_percentage': False,
        })
        return super(sale_order, self).copy(cr, uid, id, default, context=context)

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice=False, context=None):
        """Add a discount in the invoice after creation, and recompute the total
        """
        order = self.browse(cr, uid, ids[0], context=context)
        inv_obj = self.pool.get('account.invoice')
        # create the invoice
        inv_id = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_invoice, context=context)
        # modify the invoice
        inv_obj.write(cr, uid, [inv_id], {'add_disc': order.add_disc or 0.0,
                                          'name': order.client_order_ref or ''},
                                          context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        results = invoice_line_obj.read(cr, uid, lines, ['id', 'is_advance', 'is_deposit'])
        for result in results:
            if result['is_advance']:  # If created for advance, remove it.
                lines.remove(result['id'])
            if result['is_deposit']:  # If created for deposit, remove it.
                lines.remove(result['id'])

        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        return res

    def _check_tax(self, cr, uid, ids, context=None):
        # For Advance or Deposit case, loop through each lines, check if tax different.
        if not isinstance(ids, types.ListType):  # Make it a list
            ids = [ids]
        orders = self.browse(cr, uid, ids, context=context)
        for order in orders:
            if order.advance_type in ['advance', 'deposit']:
                i = 0
                tax_ids = []
                for line in order.order_line:
                    next_line_tax_id = [x.id for x in line.tax_id]
                    if i > 0 and set(tax_ids) != set(next_line_tax_id):
                        raise osv.except_osv(
                            _('Advance/Deposit!'),
                            _('You cannot create lines with different taxes!'))
                    tax_ids = next_line_tax_id
                    i += 1
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        self._check_tax(cr, uid, ids, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
