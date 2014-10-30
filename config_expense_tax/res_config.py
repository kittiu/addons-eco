# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class account_config_settings(osv.osv_memory):
    
    _inherit = 'account.config.settings'
    
    _columns = {
        'property_expense_input_vat_tax': fields.many2one('account.tax', 'Input VAT', domain="[('type_tax_use', '=', 'purchase')]"),
        'property_expense_personal_wht_tax': fields.many2one('account.tax', 'Personal WHT', domain="[('type_tax_use', '=', 'purchase')]"),
        'property_expense_company_wht_tax': fields.many2one('account.tax', 'Company WHT', domain="[('type_tax_use', '=', 'purchase')]"),
    }    
    
    def set_default_expense_tax(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids)[0]
        property_obj = self.pool.get('ir.property')
        field_obj = self.pool.get('ir.model.fields')
        todo_list = [
            ('property_expense_input_vat_tax','product.product','account.tax'),
            ('property_expense_personal_wht_tax','product.product','account.tax'),
            ('property_expense_company_wht_tax','product.product','account.tax'),   
        ]
        for record in todo_list:
            tax = getattr(wizard, record[0])
            value = tax and 'account.tax,' + str(tax.id) or False
            if value:
                field = field_obj.search(cr, uid, [('name', '=', record[0]),('model', '=', record[1]),('relation', '=', record[2])], context=context)
                vals = {
                    'name': record[0],
                    'company_id': False,
                    'fields_id': field[0],
                    'value': value,
                }            
                property_ids = property_obj.search(cr, uid, [('name','=', record[0])], context=context)
                if property_ids:
                    #the property exist: modify it
                    property_obj.write(cr, uid, property_ids, vals, context=context)
                else:
                    #create the property
                    property_obj.create(cr, uid, vals, context=context)
        return True        
        
    def get_default_expense_tax(self, cr, uid, fields, context=None):
        ir_property_obj = self.pool.get('ir.property')
        todo_list = [
            ('property_expense_input_vat_tax','product.product'),
            ('property_expense_personal_wht_tax','product.product'),
            ('property_expense_company_wht_tax','product.product'),      
        ]
        res = {}
        for record in todo_list:
            prop = ir_property_obj.get(cr, uid,
                        record[0], record[1], context=context)
            tax_id = prop and prop.id or False
            res.update({record[0]: tax_id})
        return res   
    
account_config_settings()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
