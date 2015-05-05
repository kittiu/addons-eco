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

    def _get_boi_id(self, cr, uid, ids, field_names, arg=None, context=None):
        """ BOI Cert. from Stock Location of this warehouse """
        res =  dict.fromkeys(ids, False)
        for wh in self.browse(cr, uid, ids):
            res[wh.id] = wh.lot_stock_id.boi_id and wh.lot_stock_id.boi_id.id or False
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
                        select wh.id, active from stock_warehouse wh 
                        join stock_location loc on wh.lot_stock_id = loc.id
                        where loc.boi_id = %s and active = True
                    """, (arg[2],))
                else:
                    cr.execute("""
                        select wh.id, active from stock_warehouse wh 
                        join stock_location loc on wh.lot_stock_id = loc.id
                        where loc.boi_id is null and active = True
                    """)
                
                ids = map(lambda x: x[0], cr.fetchall())
        return [('id', 'in', [id for id in ids])] 
       
    _columns = {
        'boi_id': fields.function(_get_boi_id, fnct_search=_search_boi_id, string='BOI Cert.', type='many2one', relation='account.boi',
                                  help="This BOI Cert. is retrieved from Stock Location of this warehouse"),
    }

stock_warehouse()

class stock_location(osv.osv):

    _inherit = "stock.location"
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
    }

stock_location()

class stock_picking_in(osv.osv):
    
    def _get_boi_product_borrow_detail(self, cr, uid, ids, field_names, arg=None, context=None):
        return super(stock_picking_in, self)._get_boi_product_borrow_detail(cr, uid, ids, field_names, arg=arg, context=context)
 
    def _is_borrow(self, cr, uid, ids, field_names, arg=None, context=None):
        return super(stock_picking_in, self)._is_borow(cr, uid, ids, field_names, arg=arg, context=context)

    _inherit = 'stock.picking.in'
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),
        'boi_product_borrow_detail': fields.function(_get_boi_product_borrow_detail, method=True, type='one2many', relation='account.boi.product.borrow.detail', string='Borrow Details'),
        'is_borrow': fields.function(_is_borrow, type='boolean', string='Borrow')
    }

stock_picking_in()

class stock_picking_out(osv.osv):

    def _get_boi_product_borrow_detail(self, cr, uid, ids, field_names, arg=None, context=None):
        return super(stock_picking_out, self)._get_boi_product_borrow_detail(cr, uid, ids, field_names, arg=arg, context=context)

    def _is_borrow(self, cr, uid, ids, field_names, arg=None, context=None):
        return super(stock_picking_out, self)._is_borow(cr, uid, ids, field_names, arg=arg, context=context)

    _inherit = 'stock.picking.out'
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'), 
        'boi_product_borrow_detail': fields.function(_get_boi_product_borrow_detail, method=True, type='one2many', relation='account.boi.product.borrow.detail', string='Borrow Details'),
        'is_borrow': fields.function(_is_borrow, type='boolean', string='Borrow')
    }
    
stock_picking_out()

class stock_picking(osv.osv):

    _inherit = "stock.picking"
    
    def _get_boi_product_borrow_detail(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result
        for id in ids:
            result.setdefault(id, [])
        cr.execute("""select  move.picking_id, detail.id detail_id from account_boi_product_borrow_detail detail join
                    stock_move move on move.product_id = detail.product_id and move.location_dest_id = detail.borrow_location_id
                    and move.picking_id in %s""",(tuple(ids),))
        res = cr.fetchall()
        for r in res:
            result[r[0]].append(r[1])
        return result    
    
    def _is_borrow(self, cr, uid, ids, field_names, arg=None, context=None):
        res =  dict.fromkeys(ids, False)
        for pick in self.browse(cr, uid, ids):
            if len(pick.boi_product_borrow_detail) > 0:
                res[pick.id] = True
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'), 
        'boi_product_borrow_detail': fields.function(_get_boi_product_borrow_detail, method=True, type='one2many', relation='account.boi.product.borrow.detail', string='Borrow Details'),
        'is_borrow': fields.function(_is_borrow, type='boolean', string='Borrow')
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
