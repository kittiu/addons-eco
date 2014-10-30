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

from datetime import datetime, timedelta
import types
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class purchase_order(osv.osv):

    _inherit = 'purchase.order'
    _columns = {
        'hr_expense_ok': fields.boolean('Expense', states={'draft':[('readonly',False)]}, help="If selected, the Product will list only Product marked as Expense"),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        # If hr_expense_ok, check whether all the lines' products are marked as Expense.
        if not isinstance(ids, types.ListType): # Ensure it is a list before proceeding.
            ids = [ids]
        for order in self.browse(cr, uid, ids, context=context):
            if order.hr_expense_ok or False: # If Expense
                for line in order.order_line:
                    if not (line.product_id.hr_expense_ok or False):
                        raise osv.except_osv(_('Only product expense is allowed'), _('Expense field is checked, all product must be of type Expense!'))
            else:
                for line in order.order_line:
                    if line.product_id.hr_expense_ok or False:
                        raise osv.except_osv(_('Only product item is allowed'), _('Expense field is not checked, all product must not be of type Expense!'))

        return res

purchase_order()

class purchase_order_line(osv.osv):

    _inherit = 'purchase.order.line'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', domain="[('purchase_ok', '=', True),('hr_expense_ok','=',parent.hr_expense_ok)]", change_default=True),
    }

purchase_order_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
