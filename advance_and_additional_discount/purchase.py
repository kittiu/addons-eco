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


class purchase_order(AdditionalDiscountable, osv.osv):

    _inherit = "purchase.order"
    _description = "Purchase Order"

    _tax_column = 'taxes_id'
    _line_column = 'order_line'

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            tot = 0.0
            for invoice in purchase.invoice_ids:
                if invoice.state not in ('cancel'):
                #if invoice.state not in ('draft', 'cancel'):
                    # Do not add amount, it this is a deposit/advance
                    #tot += not invoice.is_deposit and not invoice.is_advance and invoice.amount_net  # kittiu: we use amount_net instead of amount_untaxed
                    # We change from amount_net back to amount_untaxed again, due to case #2059 (may need to double check)
                    tot += not invoice.is_deposit and not invoice.is_advance and invoice.amount_untaxed  # kittiu: we use amount_net instead of amount_untaxed
            if purchase.amount_untaxed:
                res[purchase.id] = tot * 100.0 / purchase.amount_untaxed   # <-- changed back to untaxed
            else:
                res[purchase.id] = 0.0
        return res

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        res = {}
        deposit_invoiced = self._deposit_invoiced(cursor, user, ids, name, arg, context=context)
        for purchase in self.browse(cursor, user, ids, context=context):
            invoiced = False
            if purchase.invoiced_rate >= 100.00 and deposit_invoiced[purchase.id]:
                invoiced = True
            res[purchase.id] = invoiced
        return res

    def _deposit_invoiced(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            tot = 0.0
            for invoice in purchase.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    tot += invoice.amount_deposit
            if purchase.amount_deposit > 0.0:
                res[purchase.id] = False
                if tot >= purchase.amount_deposit:
                    res[purchase.id] = True
            else:
                res[purchase.id] = True
        return res

    def _num_invoice(self, cursor, user, ids, name, args, context=None):

        '''Return the amount still to pay regarding all the payment orders'''
        if not ids:
            return {}
        res = dict.fromkeys(ids, False)

        cursor.execute('SELECT rel.purchase_id, count(rel.purchase_id) ' \
                'FROM purchase_invoice_rel AS rel, account_invoice AS inv ' + \
                'WHERE rel.invoice_id = inv.id AND inv.state <> \'cancel\' And rel.purchase_id in (%s) group by rel.purchase_id' % ','.join(str(x) for x in ids))
        invs = cursor.fetchall()

        for inv in invs:
            res[inv[0]] = inv[1]
        return res

    def _amount_all(self, *args, **kwargs):
        return self._amount_all_generic(purchase_order, *args, **kwargs)

    _columns = {
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
        'invoiced': fields.function(_invoiced, string='Invoice Received', type='boolean', help="It indicates that an invoice has been paid"),
        'add_disc': fields.float('Additional Discount(%)', digits_compute=dp.get_precision('Additional Discount'),
                                 states={'confirmed': [('readonly', True)],
                                         'approved': [('readonly', True)],
                                         'done': [('readonly', True)]}),
        'add_disc_amt': fields.function(_amount_all, method=True, store=True, multi='sums',
                                        digits_compute=dp.get_precision('Account'),
                                        string='Additional Disc Amt',
                                        help="The additional discount on untaxed amount."),
        'amount_net': fields.function(_amount_all, method=True, store=True, multi='sums',
                                      digits_compute=dp.get_precision('Account'),
                                      string='Net Amount',
                                      help="The amount after additional discount."),
        'amount_untaxed': fields.function(_amount_all, method=True, store=True, multi="sums",
                                          digits_compute=dp.get_precision('Purchase Price'),
                                          string='Untaxed Amount',
                                          help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, method=True, store=True, multi="sums",
                                      digits_compute=dp.get_precision('Purchase Price'),
                                      string='Taxes',
                                      help="The tax amount"),
        'amount_total': fields.function(_amount_all, method=True, store=True, multi="sums",
                                     digits_compute=dp.get_precision('Purchase Price'),
                                     string='Total',
                                     help="The total amount"),
        # Advance Feature
        'num_invoice': fields.function(_num_invoice, string="Number invoices created", store=True),
        'advance_type': fields.selection([('advance', 'Advance on 1st Invoice'), ('deposit', 'Deposit on 1st Invoice')], 'Advance Type',
                                         required=False, help="Deposit: Deducted full amount on the next invoice. Advance: Deducted in percentage on all following invoices."),
        'advance_percentage': fields.float('Advance (%)', digits=(16, 6), required=False, readonly=True),
        'amount_deposit': fields.float('Deposit Amount', readonly=True, digits_compute=dp.get_precision('Account')),
    }
    _defaults = {
        'add_disc': 0.0,
    }

    def action_invoice_create(self, cr, uid, ids, context=None):
        """Add a discount in the invoice after creation, and recompute the total
        """
        inv_obj = self.pool.get('account.invoice')
        for order in self.browse(cr, uid, ids, context):
            # create the invoice
            inv_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context)
            # modify the invoice
            inv_obj.write(cr, uid, [inv_id], {'add_disc': order.add_disc or 0.0}, context)
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)
            res = inv_id
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'advance_type': False,
            'amount_deposit': False,
            'advance_percentage': False,
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context=context)

    def _check_tax(self, cr, uid, ids, context=None):
        # loop through each lines, check if tax different.
        if not isinstance(ids, types.ListType):  # Make it a list
            ids = [ids]
        orders = self.browse(cr, uid, ids, context=context)
        for order in orders:
            if order.advance_type in ['advance', 'deposit']:
                i = 0
                tax_ids = []
                for line in order.order_line:
                    next_line_tax_id = [x.id for x in line.taxes_id]
                    if i > 0 and set(tax_ids) != set(next_line_tax_id):
                        raise osv.except_osv(
                            _('Advance/Deposit!'),
                            _('You cannot create lines with different taxes!'))
                    tax_ids = next_line_tax_id
                    i += 1
        return True

    def write(self, cr, uid, ids, vals, context=None):
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        self._check_tax(cr, uid, ids, context=context)
        return res

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
