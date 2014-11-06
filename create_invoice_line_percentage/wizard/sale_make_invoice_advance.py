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


class sale_advance_payment_inv(osv.osv_memory):
    _inherit = "sale.advance.payment.inv"

    def _get_advance_payment_method(self, cr, uid, context=None):
        res = super(sale_advance_payment_inv, self)._get_advance_payment_method(cr, uid, context=context)
        if context.get('active_model', False) == 'sale.order':
            sale_id = context.get('active_id', False)
            if sale_id:
                sale = self.pool.get('sale.order').browse(cr, uid, sale_id)
                # Advance option not available when, There are at least 1 non-cancelled invoice created
                num_valid_invoice = 0
                for i in sale.invoice_ids:
                    if i.state not in ['cancel']:
                        num_valid_invoice += 1
                if sale.order_policy == 'manual' and (num_valid_invoice or not context.get('advance_type', False)):
                    res.append(('line_percentage', 'Line Percentage'))
        return res

    _columns = {
        'line_percent': fields.float('Installment', digits_compute=dp.get_precision('Account'),
            help="The % of installment to be used to calculate the quantity to invoice"),
        'advance_payment_method': fields.selection(_get_advance_payment_method,
            'What do you want to invoice?', required=True,
            help="""Use All to create the final invoice.
                Use Percentage to invoice a percentage of the total amount.
                Use Line Percentage to invoice a percentage of lines from Sales Order.
                Use Fixed Price to invoice a specific amount in advance.
                Use Some Order Lines to invoice a selection of the sales order lines."""),
    }

    def create_invoices(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        # Additional case, Line Percentage
        if wizard.advance_payment_method == 'line_percentage':
            if not wizard.line_percent:
                raise osv.except_osv(_('Warning!'), _('You did not specify installment!'))
            # Getting Sale Order Line IDs of this SO
            sale_obj = self.pool.get('sale.order')
            sale_ids = context.get('active_ids', [])
            order = sale_obj.browse(cr, uid, sale_ids[0])
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
            sale_order_line_make_invoice_obj = self.pool.get('sale.order.line.make.invoice')
            res = sale_order_line_make_invoice_obj.make_invoices(cr, uid, ids, context=context)
            # Update retention
            if wizard.retention > 0.0:
                sale_obj.write(cr, uid, sale_ids, {'retention_percentage': wizard.retention})
                if res.get('res_id', False):
                    self.pool.get('account.invoice').write(cr, uid, [res.get('res_id')], {'is_retention': True})
            # Update invoice
            if res.get('res_id'):
                self.pool.get('account.invoice').button_compute(cr, uid, [res.get('res_id')], context=context)
            return res
        else:
            return super(sale_advance_payment_inv, self).create_invoices(cr, uid, ids, context=context)

sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
