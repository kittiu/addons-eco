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


class sale_shop(osv.osv):

    _inherit = "sale.shop"

    def _get_boi_id(self, cr, uid, ids, field_names, arg=None, context=None):
        """ BOI Cert. from Stock Location of this warehouse """
        res =  dict.fromkeys(ids, False)
        for shop in self.browse(cr, uid, ids):
            res[shop.id] = shop.warehouse_id.boi_id and shop.warehouse_id.boi_id.id or False
        return res  
     
    def _search_boi_id(self, cr, uid, obj, name, args, domain=None, context=None):
        if not len(args):
            return []
        today = fields.date.context_today(self,cr,uid,context=context)
        ids = []
        for arg in args:
            if arg[1] == '=':
                if arg[2]:
                    cr.execute("""
                        select shop.id, active from sale_shop shop
                        join stock_warehouse wh on wh.id = shop.warehouse_id
                        join stock_location loc on wh.lot_stock_id = loc.id
                        where loc.boi_id = %s and active = True
                    """, (arg[2],))
                else:
                    cr.execute("""
                        select shop.id, active from sale_shop shop
                        join stock_warehouse wh on wh.id = shop.warehouse_id
                        join stock_location loc on wh.lot_stock_id = loc.id
                        where loc.boi_id is null and active = True
                    """)
                 
                ids = map(lambda x: x[0], cr.fetchall())
        return [('id', 'in', [id for id in ids])] 
       
    _columns = {
        'boi_id': fields.function(_get_boi_id, fnct_search=_search_boi_id, string='BOI Cert.', type='many2one', relation='account.boi',
                                  help="This BOI Cert. is retrieved from Stock Location of this shop"),
    }

sale_shop()

class sale_order(osv.osv):
    
    _inherit = "sale.order"
    
    def onchange_boi_id(self, cr, uid, ids, boi_id=False, context=None):
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('boi_id','=',boi_id)])
        if boi_id:
            boi = self.pool.get('account.boi').browse(cr, uid, boi_id)
            analytic_account_id = boi.analytic_account_id and boi.analytic_account_id.id
            fiscal_position_id = boi.fiscal_position and boi.fiscal_position.id
            res = {'value': {'shop_id': shop_ids and shop_ids[0] or False,
                             'fiscal_position': fiscal_position_id,
                             'project_id': analytic_account_id},
                   'domain': {'shop_id': [('id', 'in', shop_ids)]}}
        else:
            res = {'value': {'shop_id': shop_ids and shop_ids[0] or False,
                             'fiscal_position': False},
                             'project_id': False,
                   'domain': {'shop_id': [('id', 'in', shop_ids)]}}
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
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
    
sale_order()


class sale_order_line(osv.osv):
    
    _inherit = "sale.order.line"
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.'),
        'boi_item_id': fields.many2one('account.boi.item', 'BOI Item', domain="[('boi_id','=',parent.boi_id), ('is_fg','=',True)]", ondelete='restrict'),   
    }    
    _defaults = {
        'boi_id': lambda self,cr,uid,c: c.get('boi_id', False),
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
  
sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
