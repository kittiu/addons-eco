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

import time
from lxml import etree

from openerp.osv import fields, osv

class sale_order_line(osv.osv):
    
    # Get UOM within the same category of the selected product
#    def _get_product_uom_category_id(self, cr, uid, ids, field_name, arg, context=None):
#        result = {}
#        for line in self.browse(cr, uid, ids, context=context):
#            result[line.id] = (line.product_id.uom_id.category_id.id)
#        return result
    
    _inherit = "sale.order.line"
    _columns = {
        'product_uom_category_id':fields.integer("Product UOM Category ID"),
    }
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id,
                                                                lang, update_tax, date_order, packaging, fiscal_position, flag, context)

        product_obj = self.pool.get('product.product').browse(cr, uid, product, context=context)
        if product_obj.id:
            res['value'].update({'product_uom_category_id':product_obj.uom_id.category_id.id})

        return res    
    
sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
