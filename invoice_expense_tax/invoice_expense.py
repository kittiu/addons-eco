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
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp


class invoice_expense_expense(osv.osv):
    
    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.total_net_amount
            res[expense.id] = total
        return res
    
    _inherit = 'invoice.expense.expense'
    
    _columns = {
            'amount': fields.function(_amount, string='Total Amount', digits_compute=dp.get_precision('Account')),
    }

    def move_line_get(self, cr, uid, expense_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        if context is None:
            context = {}
        exp = self.browse(cr, uid, expense_id, context=context)

        for line in exp.line_ids:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            
            # Calculate VAT and WHT, getting it from config window.
            input_vat_tax_id = line.product_id.property_expense_input_vat_tax.id
            personal_wht_tax_id = line.product_id.property_expense_personal_wht_tax.id
            company_wht_tax_id = line.product_id.property_expense_company_wht_tax.id
            
            if not (input_vat_tax_id and personal_wht_tax_id and company_wht_tax_id):
                raise osv.except_osv(_('Error!'), _('VAT and WHT Tax is not defined.\nPlease go to Accounting module configuration and assign them!'))
            # VAT
            if line.vat_amount:
                vat = tax_obj.browse(cr, uid, input_vat_tax_id)
                vat_tax = {
                             'type':'tax',
                             'name':vat.name,
                             'price_unit': line.vat_amount,
                             'quantity': 1,
                             'price':  line.vat_amount * vat.base_sign or 0.0,
                             'account_id': vat.account_collected_id and vat.account_collected_id.id,
                             'tax_code_id': vat.tax_code_id and vat.tax_code_id.id,
                             'tax_amount': line.vat_amount or 0.0
                }
                res.append(vat_tax)
            # WHT
            if line.wht_amount:
                wht_tax_id = line.supplier_type == 'personal' and personal_wht_tax_id or company_wht_tax_id
                wht = tax_obj.browse(cr, uid, wht_tax_id)
                wht_tax = {
                             'type':'tax',
                             'name':wht.name,
                             'price_unit': line.wht_amount,
                             'quantity': 1,
                             'price':  line.wht_amount * wht.base_sign or 0.0,
                             'account_id': wht.account_collected_id and wht.account_collected_id.id,
                             'tax_code_id': wht.tax_code_id and wht.tax_code_id.id,
                             'tax_amount': line.wht_amount or 0.0
                }
                res.append(wht_tax)                        
        return res

invoice_expense_expense()

class invoice_expense_line(osv.osv):

    _inherit = 'invoice.expense.line'
    
    def _net_amount(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
        cr.execute("SELECT l.id,COALESCE(SUM(l.unit_amount*l.unit_quantity+vat_amount+wht_amount),0) AS amount FROM invoice_expense_line l WHERE id IN %s GROUP BY l.id ",(tuple(ids),))
        res = dict(cr.fetchall())
        return res
    
    _columns = {
        'supplier_name': fields.char('Supplier', size=64, required=False),
        'supplier_type': fields.selection([
                    ('personal', 'Personal'),
                    ('company', 'Company')
                    ], 'Type', required=False),      
        'vat': fields.char('Tax ID', size=64),
        'branch': fields.char('Branch ID', size=64),
        'vat_amount': fields.float('VAT', digits_compute=dp.get_precision('Account'), required=False),
        'wht_amount': fields.float('WHT', digits_compute=dp.get_precision('Account'), required=False),
        'total_net_amount': fields.function(_net_amount, string='Net Total', digits_compute=dp.get_precision('Account')),
    }
    
invoice_expense_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
