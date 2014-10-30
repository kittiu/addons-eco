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

    def fill_move(self, cr, uid, ids, context=None):
        """ To Import Stock Move required by the selected location."""
        if context is None:
            context = {}
            
        move_obj = self.pool.get('stock.move')
        picking_id = context.get('active_id', False)
        uom_obj = self.pool.get('product.uom')
        
        if not picking_id:
            return {'type': 'ir.actions.act_window_close'}
         
        if ids and len(ids):
            ids = ids[0]
        else:
            return {'type': 'ir.actions.act_window_close'}
        fill_move = self.browse(cr, uid, ids, context=context)
         
        # Check for existing lines in this picking, remove them if exists.
        move_ids = move_obj.search(cr, uid,[('picking_id', '=', picking_id)])
        move_obj.unlink(cr, uid, move_ids)
 
        location = fill_move.location_id.id
        flag = False
 
        datas = {}
        move_ids = move_obj.search(cr, uid, ['|',('location_dest_id','=',location),('location_id','=',location),('state','=','done')], context=context)

        for move in move_obj.browse(cr, uid, move_ids, context=context):
            lot_id = move.prodlot_id.id
            prod_id = move.product_id.id
            if move.location_dest_id.id != move.location_id.id:
                if move.location_dest_id.id == location:
                    qty = uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)
                else:
                    qty = -uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)

                if datas.get((prod_id, lot_id)):
                    qty += datas[(prod_id, lot_id)]['product_qty']

                datas[(prod_id, lot_id)] = {'product_id': prod_id, 'location_id': location, 'product_qty': qty, 'product_uom': move.product_id.uom_id.id, 'prod_lot_id': lot_id}
            if datas:
                flag = True

        if not flag:
            raise osv.except_osv(_('Warning!'), _('No product in this location. Please select a location in the product form.'))

        for move in datas.values():

            if fill_move.set_qty_zero:
                move.update({'product_qty': 0})

            res = {
                'picking_id': picking_id,
                'product_id': move['product_id'],
                'name': '/',
                'product_uom': move['product_uom'],
                'product_qty': move['product_qty'],
                'location_id': fill_move.location_id.id,
                'location_dest_id': fill_move.location_dest_id.id,
            }

            if res.get('product_qty') > 0:
                move_obj.create(cr, uid, res)

        return {'type': 'ir.actions.act_window_close'}

stock_fill_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
