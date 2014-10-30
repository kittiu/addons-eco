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


class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'
    _columns = {
        'mistake_delivery': fields.boolean('Mistake Delivery', help="This is a mistake delivery that need correction."),
    }
    _defaults = {  
        'mistake_delivery': False
    }
        
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'mistake_delivery': fields.boolean('Mistake Delivery', help="This is a mistake delivery that need correction."),
    }
    _defaults = {  
        'mistake_delivery': False
    }  
    def action_process_correct_delivery(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Open the Correct Mistake Delivery Wizard"""
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.correction',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
        
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        
        default['mistake_delivery'] = False
        res=super(stock_picking_out, self).copy(cr, uid, id, default, context)
        return res        
        
stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
        'mistake_delivery': fields.boolean('Mistake Delivery', help="This is a mistake delivery that need correction."),
    }
    _defaults = {  
        'mistake_delivery': False
    }  
    
    def action_process_correct_delivery(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Open the Correct Mistake Delivery Wizard"""
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.correction',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }    
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        
        default['mistake_delivery'] = False
        res=super(stock_picking_in, self).copy(cr, uid, id, default, context)
        return res       
    
stock_picking_in()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
