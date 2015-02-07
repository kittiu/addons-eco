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

class stock_warehouse(osv.osv):

    _inherit = "stock.warehouse"
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
    }

stock_warehouse()

class stock_picking_in(osv.osv):

    _inherit = 'stock.picking.in'
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
    }

stock_picking_in()

class stock_picking_out(osv.osv):

    _inherit = 'stock.picking.out'
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
    }

stock_picking_out()

class stock_picking(osv.osv):

    _inherit = "stock.picking"
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('purchase_id', False):
            purchase = self.pool.get('purchase.order').browse(cr, uid, vals.get('purchase_id'))
            vals.update({
                'boi_id': purchase.boi_id and purchase.boi_id.id or False,
            })
        if vals.get('sale_id', False):
            sale = self.pool.get('sale.order').browse(cr, uid, vals.get('sale_id'))
            vals.update({
                'boi_id': sale.boi_id and sale.boi_id.id or False,
            })
        res = super(stock_picking, self).create(cr, uid, vals, context=context)
        return res
    
stock_picking()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
