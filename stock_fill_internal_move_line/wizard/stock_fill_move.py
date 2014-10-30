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

class stock_fill_move(osv.osv_memory):
    _name = "stock.fill.move"
    _description = "Fill Move Lines"

    _columns = {
        'location_id': fields.many2one('stock.location', 'Source Location', required=True),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True),
        'set_qty_zero': fields.boolean("Set move quantity to zero",help="If checked, all product quantities will be set to zero to help ensure a real move is done"),
    }
    
    _defaults = {
        'location_id': lambda self,cr,uid,c: c.get('location_id', False),
        'location_dest_id': lambda self,cr,uid,c: c.get('location_dest_id', False),
    }
# 
#     def view_init(self, cr, uid, fields_list, context=None):
#         """
#          Creates view dynamically and adding fields at runtime.
#          @param self: The object pointer.
#          @param cr: A database cursor
#          @param uid: ID of the user currently logged in
#          @param context: A standard dictionary
#          @return: New arch of view with new columns.
#         """
#         if context is None:
#             context = {}
#         super(stock_fill_move, self).view_init(cr, uid, fields_list, context=context)
# 
#         if len(context.get('active_ids',[])) > 1:
#             raise osv.except_osv(_('Error!'), _('You cannot perform this operation on more than one Stock Inventories.'))
# 
# #         if context.get('active_id', False):
# #             stock_picking = self.pool.get('stock.picking').browse(cr, uid, context.get('active_id', False))
#         return True

    def fill_move(self, cr, uid, ids, context=None):
        """ To Import Stock Move required by the selected location."""
        if context is None:
            context = {}
        
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        picking_id = context.get('active_id', False)
        
        if not picking_id:
            return {'type': 'ir.actions.act_window_close'}
        
        if ids and len(ids):
            ids = ids[0]
        else:
            return {'type': 'ir.actions.act_window_close'}
        fill_move = self.browse(cr, uid, ids, context=context)
 
        location_dest_id = fill_move.location_dest_id.id
        
        # Check for existing lines in this picking, remove it if exists.
        move_ids = move_obj.search(cr, uid,[('picking_id', '=', picking_id)])
        move_obj.unlink(cr, uid, move_ids)

        # Create new move lines
        cr.execute("select product_id, name, product_uom, factor, sum(product_qty) product_qty \
                        from \
                        (select sm.product_id, '[' || pp.default_code || '] ' || pt.name as name, \
                        sm.product_uom, uom.factor, sm.product_qty  from stock_move sm \
                        inner join stock_location sl on sl.id = sm.location_dest_id \
                        inner join product_product pp on pp.id = sm.product_id \
                        inner join product_template pt on pt.id = sm.product_id \
                        inner join product_uom uom on uom.id = sm.product_uom \
                        left outer join stock_picking sp on sp.id = sm.picking_id \
                        where (picking_id is null or sl.usage in ('customer','supplier')) \
                        and (sm.picking_id is not null and sp.type = 'out') \
                        and sm.state in ('assigned','confirmed','waiting') \
                        and sm.location_id = %s \
                        ) move \
                        group by product_id, name, product_uom, factor \
                        order by product_id, factor ", (location_dest_id,))
        
        moves = cr.dictfetchall()

        prev_product_id = 0
        
        for move in moves:
            if fill_move.set_qty_zero:
                move.update({'product_qty': 0})
            else:
                # check required qty = product_qty - available qty at destination
                c = context.copy()
                c.update({'uom': move['product_uom'], 'location': fill_move.location_dest_id.id})
                product = product_obj.browse(cr, uid, move['product_id'], context=c)
                move_qty = round(- product.virtual_available,0) # movement equal to what is lacking
                move.update({'product_qty': move_qty > 0.0 and move_qty or 0.0})
            
            res = {
                'picking_id': picking_id,
                'product_id': move['product_id'],
                'name': move['name'],
                'product_uom': move['product_uom'],
                'product_qty': move['product_qty'],
                'location_id': fill_move.location_id.id,
                'location_dest_id': fill_move.location_dest_id.id,
            }
            
            if res.get('product_qty') > 0 and res.get('product_id') != prev_product_id:
                move_obj.create(cr, uid, res)
                
            prev_product_id = res.get('product_id')

        return {'type': 'ir.actions.act_window_close'}

stock_fill_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
