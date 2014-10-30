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

class expense_vatinfo(osv.osv_memory):

    """HR Expense VAT Info"""
    
    _name = "expense.vatinfo"
    _description = "HR Expense VAT Info"
    
    def _get_currency_id(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).expense_id.currency_id.id or False
    
    def _get_vatinfo_date(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_date or False
    
    def _get_vatinfo_number(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_number or False

    def _get_vatinfo_supplier_name(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_supplier_name or False

    def _get_vatinfo_tin(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_tin or False

    def _get_vatinfo_branch(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_branch or False

    def _get_vatinfo_base_amount(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_base_amount or False

    def _get_vatinfo_tax_id(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_tax_id.id or False

    def _get_vatinfo_tax_amount(self, cr, uid, context=None):
        return self.pool.get('hr.expense.line').browse(cr, uid, context['active_id']).vatinfo_tax_amount or False
            
    _columns = {
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'vatinfo_date': fields.date('Date', required=True, help='This date will be used as Tax Invoice Date in VAT Report'),
        'vatinfo_number': fields.char('Number', required=True, size=64, help='Number Tax Invoice'),
        'vatinfo_supplier_name': fields.char('Supplier', required=True, size=128, help='Name of Organization to pay Tax'),
        'vatinfo_tin': fields.char('Tax ID', required=True, size=64),
        'vatinfo_branch': fields.char('Branch No.', required=True, size=64),
        'vatinfo_base_amount': fields.float('Base', required=True, digits_compute=dp.get_precision('Account')),
        'vatinfo_tax_id': fields.many2one('account.tax', 'Tax', domain=[('type_tax_use','=','purchase'), ('is_wht','=',False)], required=True, ),
        'vatinfo_tax_amount': fields.float('VAT', required=True, digits_compute=dp.get_precision('Account')),
    }
    
    _defaults = {
         'currency_id': _get_currency_id,
         'vatinfo_date': _get_vatinfo_date,
         'vatinfo_number': _get_vatinfo_number,
         'vatinfo_supplier_name': _get_vatinfo_supplier_name,
         'vatinfo_tin': _get_vatinfo_tin,
         'vatinfo_branch': _get_vatinfo_branch,
         'vatinfo_base_amount': _get_vatinfo_base_amount,
         'vatinfo_tax_id': _get_vatinfo_tax_id,
         'vatinfo_tax_amount': _get_vatinfo_tax_amount,
    }
    
    def do_add_vatinfo(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        expense_line_obj = self.pool.get('hr.expense.line')
        line_ids = context['active_ids']
        for data in self.browse(cr, uid, ids):
            expense_line_obj.action_add_vatinfo(cr, uid, line_ids, data,
                             context=context)
        return {'type': 'ir.actions.client',
                'tag': 'reload'}   

    def onchange_vat(self, cr, uid, ids, vatinfo_tax_id, vatinfo_base_amount, vatinfo_tax_amount, context=None):
        res = {}
        if vatinfo_tax_id:
            change_field = context.get('change_field', False)
            vatinfo_tax = self.pool.get('account.tax').browse(cr, uid, vatinfo_tax_id)
            if vatinfo_tax and vatinfo_tax.type == 'percent':
                tax_percent = vatinfo_tax.amount or 0.0
                if change_field in ['tax_id','base_amt']: 
                    res['vatinfo_tax_amount'] = round(tax_percent * vatinfo_base_amount, 2)
                if change_field == 'tax_amt':
                    res['vatinfo_base_amount'] = round(vatinfo_tax_amount / tax_percent, 2)
        return {'value': res}
    
expense_vatinfo()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
