# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Mentis d.o.o. (<http://www.mentis.si/openerp>).
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
from openerp.tools.sql import drop_view_if_exists
import openerp.addons.decimal_precision as dp


class product_stock_card(osv.osv):
    _name = "product.stock.card"
    _description = "Product Stock Card"
    _auto = False
    _order = "product_id, date"
    _table = "product_stock_card"

    def _get_stock_tacking(self, cr, uid, ids, name, arg, context={}):
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')
        location = context.get('location', False)
        res = {}.fromkeys(ids, {}.fromkeys(name, 0.00))

        for st_move in self.browse(cr, uid, ids, context):
            in_qty = 0.00
            out_qty = 0.00
            qty = uom_obj._compute_qty_obj(cr, uid, st_move.move_uom, st_move.picking_qty, st_move.default_uom, context=context)
            if location:
                if st_move.location_id.id == location:
                    out_qty = qty
                else:
                    in_qty = qty
            else:
                if st_move.type == 'in':
                    in_qty = qty
                else:
                    if st_move.type == 'adjust':
                        if st_move.location_id.usage == 'inventory':
                            in_qty = qty
                        else:
                            out_qty = qty
                    else:
                        if st_move.type in ('out', 'internal'):
                            out_qty = qty

            d2 = st_move.date
            c = context.copy()
            c.update({'to_date': d2})
            prd = prod_obj.browse(cr, uid, st_move.product_id.id, context=c)
            res.update({st_move.id: {'in_qty': in_qty, 'out_qty': out_qty, 'balance': prd.qty_available}})

        return res

    _columns = {
        'name': fields.char('Document Name', size=20, readonly=True, select=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Picking', readonly=True),
        'date': fields.datetime('Date', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price'), readonly=True),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'location_id': fields.many2one('stock.location', 'Source Location', readonly=True, select=True),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', readonly=True, select=True),
        'picking_qty': fields.float('Picking quantity', readonly=True),
        'default_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True, select=True),
        'move_uom': fields.many2one('product.uom', 'Unit of Move', readonly=True, select=True),
        'in_qty': fields.function(_get_stock_tacking, method=True,
                                       type='float', multi='qty_balance',
                                       string='In',
                                       digits_compute=dp.get_precision('Account')),
        'out_qty': fields.function(_get_stock_tacking, method=True,
                                       type='float', multi='qty_balance',
                                       string='Out',
                                       digits_compute=dp.get_precision('Account')),
        'balance': fields.function(_get_stock_tacking, method=True,
                                       type='float', multi='qty_balance',
                                       string='Balance',
                                       digits_compute=dp.get_precision('Account')),
        'type': fields.char('Type', readonly=True),
    }

    def init(self, cr):
        drop_view_if_exists(cr, 'product_stock_card')
        cr.execute("""CREATE OR REPLACE VIEW product_stock_card AS
                      (SELECT sm.id AS id,
                              sm.product_id AS product_id,
                              sp.id AS picking_id,
                              sm.date AS date,
                              pa.id AS partner_id,
                              CASE
                                WHEN sp.type = 'in'
                                  THEN pai.id
                                WHEN sp.type = 'out'
                                  THEN sai.id
                                ELSE NULL
                              END AS invoice_id,
                              sm.price_unit AS price_unit,
                              sm.product_qty * sm.price_unit AS amount,
                              case WHEN sp.name is null THEN sm.name ELSE sp.name END as name,
                              sm.location_id as location_id,
                              sm.location_dest_id as location_dest_id,
                              CASE WHEN sp.type = 'internal' and
                                  (select usage from stock_location sl WHERE sl.id = sm.location_id) = (select usage from stock_location sl WHERE sl.id = sm.location_dest_id)
                                  THEN 'move'
                                  WHEN sp.type is null THEN 'adjust'
                                  ELSE sp.type
                              END as type,
                              sm.product_qty as picking_qty,
                              pt.uom_id as default_uom,
                              sm.product_uom as move_uom
                         FROM stock_move AS sm
                              LEFT OUTER JOIN res_partner AS pa ON pa.id = sm.partner_id
                              LEFT OUTER JOIN stock_picking AS sp ON sp.id = sm.picking_id
                              LEFT OUTER JOIN sale_order_line_invoice_rel AS solir ON solir.order_line_id = sm.sale_line_id
                              LEFT OUTER JOIN purchase_order_line_invoice_rel AS polir ON polir.order_line_id = sm.purchase_line_id
                              LEFT OUTER JOIN account_invoice_line AS sail ON sail.id = solir.invoice_id
                              LEFT OUTER JOIN account_invoice AS sai ON sai.id = sail.invoice_id
                              LEFT OUTER JOIN account_invoice_line AS pail ON pail.id = polir.invoice_id
                              LEFT OUTER JOIN account_invoice AS pai ON pai.id = pail.invoice_id
                              LEFT OUTER JOIN product_product d on (d.id=sm.product_id)
                              LEFT OUTER JOIN product_template pt on (pt.id=d.product_tmpl_id)
                        WHERE sm.state = 'done' and  sm.location_id <> sm.location_dest_id);""")


class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'stock_card_ids': fields.one2many('product.stock.card', 'product_id', 'Stock Card'),
    }

    # copy must not copy stock_product_by_location_ids
    def copy(self, cr, uid, id, default={}, context=None):
        default = default.copy()
        default['stock_card_ids'] = []
        return super(product_product, self).copy(cr, uid, id, default, context)

product_product()
