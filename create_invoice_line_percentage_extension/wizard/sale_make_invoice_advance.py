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

    _columns = {
        'line_percent': fields.float('Installment', digits=(16, 10),
            help="The % of installment to be used to calculate the quantity to invoice"),        
        'line_amount': fields.float('Installment Amount', digits_compute=dp.get_precision('Account'),
            help="The amount of installment, to be converted into line percentage"),
    }

    def onchange_line_amount(self, cr, uid, ids, line_amount, context=None):
        order_id = context.get('active_id', False)
        model = context.get('active_model', False)
        if order_id:
            order = self.pool.get(model).browse(cr, uid, order_id, context=context)
            line_percent = order.amount_net and (line_amount / order.amount_net * 100) or 0.0
            return {'value': {'line_percent': line_percent}}
        return False
    
sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
