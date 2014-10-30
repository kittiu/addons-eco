# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011 Camptocamp (<http://www.camptocamp.com>).
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
    
    _inherit = "stock.picking"

    _columns = {
        'invoice_ids': fields.many2many('account.invoice', 'picking_invoice_rel', 'picking_id', 'invoice_id', 'Invoices'),
        'client_order_ref' : fields.related ('sale_id', 'client_order_ref', type="char", relation="sale.order", string="Client Ref", readonly = True ),
        'picking_id_ref': fields.many2one('stock.picking','Shipping Ref', readonly=True)
    }

    def init(self, cr):
        # This is a helper to guess "old" Relations between pickings and invoices
        cr.execute('select id, origin from account_invoice where length(origin) > 0')
        origins = cr.dictfetchall()
        for origin in origins:
            numbers = origin and origin['origin'] and origin['origin'].replace(' ','').split(',')
            for number in numbers:
                cr.execute("""
                    insert into picking_invoice_rel(picking_id,invoice_id) select p.id,i.id from stock_picking p, account_invoice i
                    where i.id = %s and p.name = split_part(%s,':',1) and (p.id,i.id) not in (select picking_id,invoice_id from picking_invoice_rel);
                    """, (origin['id'],number,))

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        res = super(stock_picking,self).action_invoice_create(cr, uid, ids, journal_id,
            group, type, context)
        for id in res:
            picking_id = id
            invoice_ids = res[id]
            if not isinstance(invoice_ids,list):
                invoice_ids = [invoice_ids]
            self.write(cr, uid, picking_id, {'invoice_ids' : [(6,0, invoice_ids )]}, context=context) 
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        default.update({'invoice_ids': []})
        if default.get('name') and default.get('name').find('-return'):
            default.update({'picking_id_ref': id})
        new_picking_id = super(stock_picking, self).copy(cr, uid, id, default, context)
        # update new id back to original
        new_picking = self.browse(cr, uid, new_picking_id)
        picking = self.browse(cr, uid, id)
        # If picking also have the invoice ref, make sure the old_picking now point the new picking
        if picking.picking_id_ref:
            old_picking =  self.browse(cr, uid, picking.picking_id_ref.id)
            if old_picking.picking_id_ref:
                self.write(cr, uid, [old_picking.id], {'picking_id_ref': new_picking.id})
                self.write(cr, uid, [new_picking.id], {'picking_id_ref': old_picking.id})
        if new_picking.picking_id_ref:
            self.write(cr, uid, [picking.id], {'picking_id_ref': new_picking.id})
        
        return new_picking_id
                
stock_picking()

class stock_picking_out(osv.osv):
    
    _inherit = "stock.picking.out"

    _columns = {
        'invoice_ids': fields.many2many('account.invoice', 'picking_invoice_rel', 'picking_id', 'invoice_id', 'Invoices'),
        'client_order_ref' : fields.related ('sale_id', 'client_order_ref', type="char", relation="sale.order", string="Client Ref", readonly = True ),
        'picking_id_ref': fields.many2one('stock.picking','Shipping Ref', readonly=True)
    }
    
stock_picking_out()

class stock_picking_in(osv.osv):
    
    _inherit = "stock.picking.in"

    _columns = {
        'invoice_ids': fields.many2many('account.invoice', 'picking_invoice_rel', 'picking_id', 'invoice_id', 'Invoices'),
        'client_order_ref' : fields.related ('sale_id', 'client_order_ref', type="char", relation="sale.order", string="Client Ref", readonly = True ),
        'picking_id_ref': fields.many2one('stock.picking','Shipping Ref', readonly=True)
    }
    
stock_picking_in()   


