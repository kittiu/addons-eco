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
        'shipper_id': fields.many2one('partner.shipper', 'Shipper', domain="[('partner_ids','in',partner_id)]"),
    }
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id,
                                                               group, type, context=context)
        
        if type=='out_invoice':
            picking_obj = self.pool.get('stock.picking.out')
            inv_obj = self.pool.get('account.invoice')
            for picking_id in res:
                invoice_id = res.get(picking_id)
                picking = picking_obj.browse(cr, uid, picking_id)
                inv_obj.write(cr, uid, [invoice_id], {'shipper_id': picking.shipper_id.id}, context=context)

        return res
    
    # After partial delivery, also copy the shipper_id from Old DO to new DO
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        if res:
            original_picking = res.keys()[0]
            delivered_picking = res[res.keys()[0]]['delivered_picking']
            if original_picking <> delivered_picking:
                results = self.pool.get('stock.picking.out').read(cr, uid, [original_picking], ['shipper_id'])
                shipper_id = results[0]['shipper_id'] and results[0]['shipper_id'][0] or False
                self.pool.get('stock.picking.out').write(cr, uid, [delivered_picking], {'shipper_id': shipper_id})
        return res

stock_picking()

class stock_picking_out(osv.osv):

    _inherit = 'stock.picking.out'  
    _columns = {
        'shipper_id': fields.many2one('partner.shipper', 'Shipper', domain="[('partner_ids','in',partner_id)]"),
    }

stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
