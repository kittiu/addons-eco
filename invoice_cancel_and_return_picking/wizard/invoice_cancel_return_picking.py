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
import time

from openerp.osv import osv,fields
from openerp.tools.translate import _


class invoice_cancel_return_picking_list(osv.osv_memory):
    _name = "invoice.cancel.return.picking.list"
    _rec_name = 'picking_id'
    _columns = {
        'picking_id' : fields.many2one('stock.picking', string="Delivery Order", Readonly=True),
        'wizard_id' : fields.many2one('invoice.cancel.return.picking', string="Wizard"),
    }

invoice_cancel_return_picking_list()

class invoice_cancel_return_picking(osv.osv_memory):
    
    _name = 'invoice.cancel.return.picking'
    _description = 'Cancel Invoice and Return Pickings'
    
    _columns = {
        'picking_ids': fields.one2many('invoice.cancel.return.picking.list', 'wizard_id', 'Shipments', readonly=True),
        #'invoice_state': fields.selection([('2binvoiced', 'To be refunded/invoiced'), ('none', 'No invoicing')], 'Invoicing',required=True),
        'invoice_state': fields.selection([('none', 'No invoicing')], 'Invoicing',required=True),

    }
    
    _defaults = {
        'invoice_state':'none'
    }
 
    def default_get(self, cr, uid, fields, context=None):

        result1 = []
        if context is None:
            context = {}
        res = super(invoice_cancel_return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(cr, uid, record_id, context=context)
        if invoice:
            for picking_id in invoice.picking_ids:
                result1.append({'picking_id': picking_id.id})
            if 'picking_ids' in fields:
                res.update({'picking_ids': result1})
        return res

    def get_picking_list(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        invoice_obj = self.pool.get('account.invoice')
        for invoice in invoice_obj.browse(cr, uid, ids, context=context):
            result[invoice.id] = invoice.picking_ids
        return result

    def create_cancel_and_returns(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        # Check return history of all the pickings,
        wizard = self.browse(cr, uid, ids[0], context=context)
        picking_obj = self.pool.get('stock.picking')
        if len(wizard.picking_ids) > 1:
            (_('Error!'), _('This is a merged invoice (> 1 referenced shipments). This method is not allowed!\nPlease use standard cancellation method.'))

        for w_picking in wizard.picking_ids:
            picking = picking_obj.browse(cr, uid, w_picking.picking_id.id, context=context)
            for m in picking.move_lines:
                if m.move_history_ids2:
                    raise osv.except_osv(_('Error!'), _('Some shipments has been partially returned. This method is not allowed!\nPlease use standard cancellation method.'))
            
        record_id = context and context.get('active_id', False) or False
        
        # Do the cancel,
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'account.invoice', record_id, 'invoice_cancel', cr)
        
        # Do the return
        for w_picking in wizard.picking_ids:
            data = {'invoice_state': wizard.invoice_state}
            result1 = []      
            pick = picking_obj.browse(cr, uid, w_picking.picking_id.id, context=context)
            if pick:
                for line in pick.move_lines:
                    qty = line.product_qty
                    if qty > 0:
                        result1.append({'product_id': line.product_id.id, 'quantity': qty,'move_id':line.id, 'prodlot_id': line.prodlot_id and line.prodlot_id.id or False})
                    data.update({'product_return_moves': result1})
                    
                
                # Create new returns
                new_type, new_picking = self.create_returns(cr, uid, pick.id, data, context=context)
                
            # Opening Partial Picking window to return the product.
            context.update({
                'default_type': new_type,
                'active_model': 'stock.picking.' + new_type,
                'active_ids': [new_picking],
                'active_id': new_picking
            })
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.partial.picking',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context,
                'nodestroy': True,
            }              
        
        return True
    
    def create_returns(self, cr, uid, record_id, data, context=None):

        if context is None:
            context = {} 
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
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
                                        'name': _('%s-%s-return*') % (new_pick_name, pick.name),
                                        'move_lines': [], 
                                        'state':'draft', 
                                        'type': new_type,
                                        'date':date_cur, 
                                        'invoice_state': data['invoice_state'],
        })
        
        for move_line in data['product_return_moves']:
            mov_id = move_line['move_id']
            new_qty = move_line['quantity']
            move = move_obj.browse(cr, uid, mov_id, context=context)
            new_location = move.location_dest_id.id

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

        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        
        return new_type, new_picking

invoice_cancel_return_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
