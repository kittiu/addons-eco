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


class hr_expense_expense(osv.osv):
    
    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.total_net_amount
            res[expense.id] = total
        return res
    
    _inherit = 'hr.expense.expense'
    
    _columns = {
        'number': fields.char('Expense Number', size=128, required=False, readonly=True),   
        'amount': fields.function(_amount, string='Total Amount', digits_compute=dp.get_precision('Account')),
    }
        
    def create(self, cr, uid, vals, context=None):
        vals['number'] = self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice') or '/'
        return super(hr_expense_expense, self).create(cr, uid, vals, context=context)    

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
                raise osv.except_osv(_('Error!'), _('VAT and WHT Tax is not defined.\nPlease go to Account module configuration and assign them!'))
            # VAT
            if line.tax_amount:
                vat = tax_obj.browse(cr, uid, input_vat_tax_id)
                vat_tax = {
                             'type':'tax',
                             'name':vat.name,
                             'price_unit': line.tax_amount,
                             'quantity': 1,
                             'price':  line.tax_amount * vat.base_sign or 0.0,
                             'account_id': vat.account_collected_id and vat.account_collected_id.id,
                             'tax_code_id': vat.tax_code_id and vat.tax_code_id.id,
                             'tax_amount': line.tax_amount or 0.0
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
    
    def action_receipt_create(self, cr, uid, ids, context=None):
        res = super(hr_expense_expense, self).action_receipt_create(cr, uid, ids, context=context)
        # Write expense's number to account_move
        move_obj = self.pool.get('account.move')
        for expense in self.browse(cr, uid, ids):
            move_obj.write(cr, uid, [expense.account_move_id.id], {'name': expense.number})
        return res    

hr_expense_expense()

class hr_expense_line(osv.osv):

    _inherit = 'hr.expense.line'
    
    def onchange_tax_id(self, cr, uid, ids, tax_id, wht_tax_id, unit_amount, unit_quantity, context=None):
        res = {}
        tax = self.pool.get('account.tax').browse(cr, uid, tax_id, context)
        wht = self.pool.get('account.tax').browse(cr, uid, wht_tax_id, context)
        tax_percent = 0.0
        wht_percent = 0.0
        if tax_id and tax.type == 'percent':
            tax_percent = tax.amount or 0.0  
            res.update({'tax_amount': tax_percent * unit_amount * unit_quantity})
        if wht_tax_id and wht.type == 'percent':
            wht_percent = wht.amount or 0.0
            res.update({'wht_amount': -wht_percent * unit_amount * unit_quantity})
        return {'value': res}  
    
    def _net_amount(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
        cr.execute("SELECT l.id,COALESCE(SUM(l.unit_amount*l.unit_quantity+tax_amount+wht_amount),0) AS amount FROM hr_expense_line l WHERE id IN %s GROUP BY l.id ",(tuple(ids),))
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
        'tax_id': fields.many2one('account.tax', 'Tax', domain=[('type_tax_use','=',('purchase')), ('is_wht','=',False)], required=False),
        'tax_amount': fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), required=False),
        'wht_tax_id': fields.many2one('account.tax', 'WHT', domain=[('type_tax_use','=',('purchase')), ('is_wht','=',True)], required=False),
        'wht_amount': fields.float('WHT Amount', digits_compute=dp.get_precision('Account'), required=False),
        'total_net_amount': fields.function(_net_amount, string='Net Total', digits_compute=dp.get_precision('Account')),
    }
    
hr_expense_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
