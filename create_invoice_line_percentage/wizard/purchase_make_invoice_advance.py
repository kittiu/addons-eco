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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class purchase_advance_payment_inv(osv.osv_memory):

    _inherit = "purchase.advance.payment.inv"
    _columns = {
        'line_percent': fields.float('Installment', digits_compute=dp.get_precision('Account'),
            help="The % of installment to be used to calculate the quantity to invoice"),
    }

    def create_invoices(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        # Additional case, Line Percentage
        if wizard.line_percent:
            # Getting PO Line IDs of this PO
            purchase_obj = self.pool.get('purchase.order')
            purchase_ids = context.get('active_ids', [])
            order = purchase_obj.browse(cr, uid, purchase_ids[0])
            order_line_ids = []
            # For Deposit, check the deposit percent must either
            #  1) Make whole amount 100%
            #  2) Make whole amount left off equal to deposit amount (for the next invoice not become negative)
            if order.advance_type == 'deposit':
                percent_deposit = (order.amount_deposit / order.amount_net) * 100
                percent_after = (order.invoiced_rate + wizard.line_percent)
                if not (percent_after >= 100.00) and not (percent_deposit + percent_after <= 100):
                    raise osv.except_osv(_('Amount Error!'),
                            _('This percentage will make negative amount in the next invoice.'))

            for order_line in order.order_line:
                order_line_ids.append(order_line.id)
            # Assign them into active_ids
            context.update({'active_ids': order_line_ids})
            context.update({'line_percent': wizard.line_percent})
            purchase_order_line_make_invoice_obj = self.pool.get('purchase.order.line_invoice')
            res = purchase_order_line_make_invoice_obj.makeInvoices(cr, uid, ids, context=context)
            if not context.get('open_invoices', False):
                return {'type': 'ir.actions.act_window_close'}
            return res

        return super(purchase_advance_payment_inv, self).create_invoices(cr, uid, ids, context=context)

purchase_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
