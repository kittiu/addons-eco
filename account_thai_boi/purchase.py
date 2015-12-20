# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import types
from openerp.osv import fields,osv

class purchase_order(osv.osv):
    
    _inherit = "purchase.order"
    
    def onchange_boi_id(self, cr, uid, ids, boi_id=False, context=None):
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('boi_id','=',boi_id)])
        if boi_id:
            fiscal_position_id = self.pool.get('account.boi').browse(cr, uid, boi_id).fiscal_position.id
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                             'fiscal_position': fiscal_position_id},
                   'domain': {'warehouse_id': [('id', 'in', warehouse_ids)]}}
        else:
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                             'fiscal_position': False},
                   'domain': {'warehouse_id': [('id', 'in', warehouse_ids)]}}
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
        'boi_order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', states={'approved':[('readonly',True)],'done':[('readonly',True)]}),
    }    
    
#     def write(self, cr, uid, ids, vals, context=None):
#         if not isinstance(ids, types.ListType):  # Make it a list
#             ids = [ids]
#         res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
#         purchase_line_obj = self.pool.get('purchase.order.line')
#         position_obj = self.pool.get('account.fiscal.position')
#         for purchase in self.browse(cr, uid, ids):
#             # Change fiscal position based on BOI
#             fiscal_position_id = vals.get('fiscal_position', False)
#             if fiscal_position_id:
#                 fiscal_position = position_obj.browse(cr, uid, fiscal_position_id)
#                 # Change tax in product line based on fiscal position
#                 for line in purchase.order_line:
#                     taxes = position_obj.map_tax(cr, uid, fiscal_position, line.taxes_id)
#                     purchase_line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, taxes)]})
#         return res
    
purchase_order()


class purchase_order_line(osv.osv):
    
    _inherit = "purchase.order.line"
    
    _columns = {
        'boi_item_id': fields.many2one('account.boi.item', 'BOI Item', domain="[('boi_id','=',parent.boi_id), ('is_fg','=',False)]", ondelete='restrict'),   
    }    
  
    def onchange_boi_item_id(self, cr, uid, ids, boi_item_id, context=None):
        if not boi_item_id:
            return {'value': {'account_analytic_id': False,
                              'product_id': False}, 
                    'domain': {'product_id': []}}
        boi_item = self.pool.get('account.boi.item').browse(cr, uid, boi_item_id)
            
        boi_product_ids = self.pool.get('account.boi.product').search(cr, uid, [('boi_item_id','=',boi_item_id)])
        product_ids = [x.product_id.id for x in self.pool.get('account.boi.product').browse(cr, uid, boi_product_ids)]
        return {'value': {'account_analytic_id': boi_item.boi_id.analytic_account_id and boi_item.boi_id.analytic_account_id.id},
                'domain': {'product_id': [('id','in',product_ids)]}}
  
purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
