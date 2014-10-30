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
from openerp import netsvc
from openerp.osv import osv, fields
import time
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare

class delivery_correction(osv.osv_memory):
    """ Delivery Correction """

    _name = "delivery.correction"
    _description = "Correct Mistake Delivery"

    _columns = {
        'invoice_state': fields.selection([('2binvoiced', 'To be refunded/invoiced'), ('none', 'No invoicing')], 'Invoicing',required=True),
    }

    _defaults = {  
        'invoice_state': 'none', # There will be invoice created for this correction.
    }
    
    def action_correct_delivery(self, cr, uid, ids, context=None):
        
        active_id = context.get('active_id', False)
        # Out or In
        pick_obj = context.get('default_type') == 'out' and self.pool.get('stock.picking.out') or self.pool.get('stock.picking.in')
        move_obj = self.pool.get('stock.move')
        pick = pick_obj.browse(cr, uid, active_id, context=context)
        
        # Not allowed, if invoiced or already mark as mistake.
#        if pick.invoice_state == 'invoiced':
#            raise osv.except_osv(_('Warning!'), _("This document is already been invoiced!"))
        if pick.mistake_delivery:
            raise osv.except_osv(_('Warning!'), _("This document is already been corrected for delivery!"))  
                 
        # Step 1: Create incoming shipment (return) and Confirm it.
        self.create_returns(cr, uid, ids, context=context)
        self.do_partial(cr, uid, [context.get('picking_id', False)], context=context)
        
        # Step 2: Duplicate a new Delivery Order (edit existing if true)
        new_picking = pick_obj.copy(cr, uid, active_id, {
                                            'mistake_delivery': False,
                                            'origin': pick.origin
                                        })
        pick_obj.write(cr, uid, [new_picking], {'origin': pick.origin, 'invoice_state': '2binvoiced'})
        
        # Step 3: Looking for Back Order DO (if exists and not done), cancel it and add its lines to the new DO.
        backorder_ids = pick_obj.search(cr, uid, [('backorder_id', '=', active_id),('state', '!=', 'done')])
        
        if len(backorder_ids) > 0:
            pick_obj.action_cancel(cr, uid, backorder_ids, context=context)
            pick_obj.write(cr, uid, backorder_ids, {'mistake_delivery': True})
            backorders = pick_obj.browse(cr, uid, backorder_ids, context=context)
            for pick in backorders:
                for move in pick.move_lines:
                    new_move = move_obj.copy(cr, uid, move.id, {
                                                'picking_id': new_picking,
                                                'state': 'draft',
                    })
        
        # Setp 4: Display the newly created DO.
        return {
            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            'name': _('Delivery Order (Correction)'),
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model': context.get('default_type') == 'out' and 'stock.picking.out' or 'stock.picking.in',
            'type':'ir.actions.act_window',
            'context':context,
        }
        
    # Resemble to stock_return_picking.create_returns()
    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {} 
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        #act_obj = self.pool.get('ir.actions.act_window')
        #model_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        set_invoice_state_to_none = True
        returned_lines = 0
        
#        Create new picking for returned products
        if pick.type =='out':
            new_type = 'in'
        elif pick.type =='in':
            new_type = 'out'
        else:
            new_type = 'internal'
        seq_obj_name = 'stock.picking.' + new_type
        new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
        new_picking = pick_obj.copy(cr, uid, pick.id, {
                                        'name': _('%s-%s-return') % (new_pick_name, pick.name),
                                        'move_lines': [], 
                                        'state':'draft', 
                                        'type': new_type,
                                        'date':date_cur, 
                                        'invoice_state': data['invoice_state'],
        })
        
        for move in pick.move_lines:
            new_qty = move.product_qty
            new_location = move.location_dest_id.id
            returned_qty = move.product_qty
            for rec in move.move_history_ids2:
                returned_qty -= rec.product_qty

            if returned_qty != new_qty:
                set_invoice_state_to_none = False
            if new_qty:
                returned_lines += 1
                new_move=move_obj.copy(cr, uid, move.id, {
                                            'product_qty': new_qty,
                                            'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                                            'picking_id': new_picking, 
                                            'state': 'draft',
                                            'location_id': new_location, 
                                            'location_dest_id': move.location_id.id,
                                            'date': date_cur,
                })
                move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]}, context=context)
        if not returned_lines:
            raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))

        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        # Update view id in context, lp:702939
        model_list = {
                'out': 'stock.picking.out',
                'in': 'stock.picking.in',
                'internal': 'stock.picking',
        }
        
        # Update for new context values as we pass to Incoming Shipment window.
        context.update({'picking_id':new_picking})
        
        # Mark original and new document as mistake_delivery = True
        self.pool.get('stock.picking.out').write(cr, uid, [record_id], {'mistake_delivery':True})
        self.pool.get('stock.picking.in').write(cr, uid, [new_picking], {'mistake_delivery':True})
        
        return True
    
#        return {
#            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
#            'name': _('Returned Picking'),
#            'view_type':'form',
#            'view_mode':'tree,form',
#            'res_model': model_list.get(new_type, 'stock.picking'),
#            'type':'ir.actions.act_window',
#            'context':context,
#        }
        
    # Resemble to stock_partial_picking.do_partial(), but we do in full.
    def do_partial(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_picking = self.pool.get('stock.picking')
#        stock_move = self.pool.get('stock.move')
#        uom_obj = self.pool.get('product.uom')
        partial = stock_picking.browse(cr, uid, ids[0], context=context) # Instead of wizard, we will do in full.
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.type
        for move_line in partial.move_lines:
#            line_uom = move_line.product_uom
#            move_id = move_line.id
#
#            #Quantiny must be Positive
#            if move_line.product_qty < 0:
#                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))
#
#            #Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
#            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, move_line.product_qty, line_uom.id)
#
#            if line_uom.factor and line_uom.factor <> 0:
#                if float_compare(qty_in_line_uom, move_line.product_qty, precision_rounding=line_uom.rounding) != 0:
#                    raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only roundings of "%s %s" is accepted by the Unit of Measure.') % (move_line.product_qty, line_uom.name, line_uom.rounding, line_uom.name))
#            if move_id:
#                #Check rounding Quantity.ex.
#                #picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
#                #partial delivery: 253g
#                #=> result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
#                initial_uom = move_line.product_uom
#                #Compute the quantity for respective wizard_line in the initial uom
#                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, move_line.product_qty, initial_uom.id)
#                without_rounding_qty = (move_line.product_qty / line_uom.factor) * initial_uom.factor
#                if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
#                    raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only roundings of "%s %s" is accepted by the uom.') % (move_line.product_qty, line_uom.name, move_line.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
#            else:
#                seq_obj_name =  'stock.picking.' + picking_type
#                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
#                                                    'product_id': move_line.product_id.id,
#                                                    'product_qty': move_line.product_qty,
#                                                    'product_uom': move_line.product_uom.id,
#                                                    'prodlot_id': move_line.prodlot_id.id,
#                                                    'location_id' : move_line.location_id.id,
#                                                    'location_dest_id' : move_line.location_dest_id.id,
#                                                    'picking_id': partial.id
#                                                    },context=context)
#                stock_move.action_confirm(cr, uid, [move_id], context)
            partial_data['move%s' % (move_line.id)] = {
                'product_id': move_line.product_id.id,
                'product_qty': move_line.product_qty,
                'product_uom': move_line.product_uom.id,
                'prodlot_id': move_line.prodlot_id.id,
            }
            if (picking_type == 'in') and (move_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (move_line.id)].update(product_price=move_line.cost,
                                                                  product_currency=move_line.currency.id)
        stock_picking.do_partial(cr, uid, [partial.id], partial_data, context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
