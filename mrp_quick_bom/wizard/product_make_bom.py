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

class product_make_bom(osv.osv_memory):
    _name = "product.make.bom"
    _description = "Product Make BOM"
    _columns = {
        'product_name': fields.char('Product Name', size=128, required=True),
        'product_categ_id': fields.many2one('product.category', 'Category', required=True, readonly=False),        
        'product_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, readonly=False),        
        'type': fields.selection([('product','Stockable Product'),('consu', 'Consumable'),('service','Service')], 'Product Type', required=True, help="Consumable: Will not imply stock management for this product. \nStockable product: Will imply stock management for this product."),
        'procure_method': fields.selection([('make_to_stock','Make to Stock'),('make_to_order','Make to Order')], 'Procurement Method', required=True, help="Make to Stock: When needed, the product is taken from the stock or we wait for replenishment. \nMake to Order: When needed, the product is purchased or produced."),
        'supply_method': fields.selection([('produce','Manufacture'),('buy','Buy')], 'Supply Method', required=True, help="Manufacture: When procuring the product, a manufacturing order or a task will be generated, depending on the product type. \nBuy: When procuring the product, a purchase order will be generated."),
        'valuation':fields.selection([('manual_periodic', 'Periodical (manual)'),
                                        ('real_time','Real Time (automated)'),], 'Inventory Valuation',
                                        help="If real-time valuation is enabled for a product, the system will automatically write journal entries corresponding to stock moves." \
                                             "The inventory variation account set on the product category will represent the current inventory value, and the stock input and stock output account will hold the counterpart moves for incoming and outgoing products."
                                        , required=True),        
    }
    _defaults = {
        'type': 'product',
        'procure_method': 'make_to_order',
        'supply_method': 'produce',
        'valuation': 'manual_periodic',    }

    def make_bom(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        mrp_obj = self.pool.get('mrp.bom')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
    
        data = self.read(cr, uid, ids)[0]    
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        if context.get('active_model') == 'sale.order': # created from sales order line
            product_id, bom_id = mrp_obj.action_product_bom_create_from_order_line(cr, uid, context.get(('active_ids'), []), data, context=context)
        elif context.get('active_model') == 'product.product': # created from product_line
            product_id, bom_id = mrp_obj.action_product_bom_create(cr, uid, context.get(('active_ids'), []), data, context=context)
        if not bom_id:
            return False

        res = mod_obj.get_object_reference(cr, uid, 'product', 'product_normal_form_view')
        res_id = res and res[1] or False,

        return {
            'name': _('Product'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res_id,
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': product_id or False,
        } 

product_make_bom()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
