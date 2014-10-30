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

#class product_category(osv.osv):
#    
#    _inherit = "product.category"
#    _columns = {
#        'product_cat_code': fields.char('Category Code', size=3, help="Cateory Code Max Size = 3 characters"),
#    }
#
#product_category()

class product_product(osv.osv):

    
    def _dynamic_product_code(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for p in self.browse(cr, uid, ids, context=context):
            # <product_cat_code>-<product_code>-<partner_code>-<product_sub_code>
            # Sample of Dynamic Product Code
            #  * 081-MV6001-571-01, 081-MV6001-571-02
            #  * 000-MV6001-000-00
            dynamic_product_code = ""
#            dynamic_product_code += (p.categ_id and p.categ_id.product_cat_code <> "") and p.categ_id.product_cat_code or "000"
#            dynamic_product_code += "-"
            dynamic_product_code += p.product_main_code and p.product_main_code or "00000"
            dynamic_product_code += "/"
            dynamic_product_code += (p.partner_id and p.partner_id.partner_code <> "") and p.partner_id.partner_code or "MH"
#             dynamic_product_code += "/"
#             dynamic_product_code += p.product_sub_code and p.product_sub_code or "00"

            res[p.id] = dynamic_product_code
        return res

    _inherit = "product.product"
    _order = 'name_template'
    _columns = {
        'default_code': fields.function(_dynamic_product_code, type='char', store=True, string='Internal Reference'),
        'product_main_code': fields.char('Main Code', size=20, required=True, help="Main Code Max Size = 10 characters"),
        #'product_sub_code': fields.char('Sub Code', size=2, help="Sub Code Max Size = 2 characters"),
        'partner_id': fields.many2one('res.partner', 'Product Customer'),
    }

    _sql_constraints = [
        #('product_code_uniq', 'unique(product_main_code, product_sub_code)', 'Main Code + Sub Code must be unique!'),
        ('product_code_uniq', 'unique(product_main_code)', 'Main Code + Sub Code must be unique!'),
    ]    
product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
