# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

class stock_partial_move(osv.osv_memory):

    _inherit = 'stock.partial.picking'
    
    def _check_qty_remaining(self, cr, uid, ids, product_id, product_qty, context=None, lock=False):
        """
        Attempt to find a quantity ``product_qty`` (in the product's default uom or the uom passed in ``context``) of product ``product_id``
        in locations with id ``ids`` and their child locations. If ``lock`` is True, the stock.move lines
        of product with id ``product_id`` in the searched location will be write-locked using Postgres's
        "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back, to prevent reservin
        twice the same products.
        If ``lock`` is True and the lock cannot be obtained (because another transaction has locked some of
        the same stock.move lines), a log line will be output and False will be returned, as if there was
        not enough stock.

        :param product_id: Id of product to reserve
        :param product_qty: Quantity of product to reserve (in the product's default uom or the uom passed in ``context``)
        :param lock: if True, the stock.move lines of product with id ``product_id`` in all locations (and children locations) with ``ids`` will
                     be write-locked using postgres's "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back. This is
                     to prevent reserving twice the same products.
        :param context: optional context dictionary: if a 'uom' key is present it will be used instead of the default product uom to
                        compute the ``product_qty`` and in the return value.
        :return: List of tuples in the form (qty, location_id) with the (partial) quantities that can be taken in each location to
                 reach the requested product_qty (``qty`` is expressed in the default uom of the product), of False if enough
                 products could not be found, or the lock could not be obtained (and ``lock`` was True).
        """
        result = []
        amount = 0.0
        if context is None:
            context = {}
        location_obj = self.pool.get('stock.location')
        uom_obj = self.pool.get('product.uom')
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        if product.categ_id and product.categ_id.is_check_qty_deliver:
            uom_rounding = product.uom_id.rounding
            if context.get('uom'):
                uom_rounding = uom_obj.browse(cr, uid, context.get('uom'), context=context).rounding
            for id in location_obj.search(cr, uid, [('location_id', 'child_of', ids), ('usage','=','internal')]):
                if lock:
                    try:
                        # Must lock with a separate select query because FOR UPDATE can't be used with
                        # aggregation/group by's (when individual rows aren't identifiable).
                        # We use a SAVEPOINT to be able to rollback this part of the transaction without
                        # failing the whole transaction in case the LOCK cannot be acquired.
                        cr.execute("SAVEPOINT stock_location_product_reserve")
                        cr.execute("""SELECT id FROM stock_move
                                      WHERE product_id=%s AND
                                              (
                                                (location_dest_id=%s AND
                                                 location_id<>%s AND
                                                 state='done')
                                                OR
                                                (location_id=%s AND
                                                 location_dest_id<>%s AND
                                                 state in ('done', 'assigned'))
                                              )
                                      FOR UPDATE of stock_move NOWAIT""", (product_id, id, id, id, id), log_exceptions=False)
                    except Exception:
                        # Here it's likely that the FOR UPDATE NOWAIT failed to get the LOCK,
                        # so we ROLLBACK to the SAVEPOINT to restore the transaction to its earlier
                        # state, we return False as if the products were not available, and log it:
                        cr.execute("ROLLBACK TO stock_location_product_reserve")
                        _logger.warning("Failed attempt to reserve %s x product %s, likely due to another transaction already in progress. Next attempt is likely to work. Detailed error available at DEBUG level.", product_qty, product_id)
                        _logger.debug("Trace of the failed product reservation attempt: ", exc_info=True)
                        return False
    
                # XXX TODO: rewrite this with one single query, possibly even the quantity conversion
                cr.execute("""SELECT product_uom, sum(product_qty) AS product_qty
                              FROM stock_move
                              WHERE location_dest_id=%s AND
                                    location_id<>%s AND
                                    product_id=%s AND
                                    state='done'
                              GROUP BY product_uom
                           """,
                           (id, id, product_id))
                results = cr.dictfetchall()
                cr.execute("""SELECT product_uom,-sum(product_qty) AS product_qty
                              FROM stock_move
                              WHERE location_id=%s AND
                                    location_dest_id<>%s AND
                                    product_id=%s AND
                                    state in ('done')
                              GROUP BY product_uom
                           """,
                           (id, id, product_id))
                results += cr.dictfetchall()
                total = 0.0
                results2 = 0.0
                for r in results:
                    amount = uom_obj._compute_qty(cr, uid, r['product_uom'], r['product_qty'], context.get('uom', False))
                    results2 += amount
                    total += amount
                total_after_move = total - product_qty
                if total_after_move < 0.0:
                    raise osv.except_osv(_('Error!'), _('The inventory of %s is not enough!, only %s left in stock.') % (product.name, total,))

# 
#             amount = results2
#             compare_qty = float_compare(amount, 0, precision_rounding=uom_rounding)
#             if compare_qty == 1:
#                 if amount > min(total, product_qty):
#                     amount = min(product_qty, total)
#                 result.append((amount, id))
#                 product_qty -= amount
#                 total -= amount
#                 if product_qty <= 0.0:
#                     return result
#                 if total <= 0.0:
#                     continue
        return False    

    def do_partial(self, cr, uid, ids, context=None):
        
        # no call to super!
        assert len(ids) == 1, 'Partial move processing may only be done one form at a time.'
        partial = self.browse(cr, uid, ids[0], context=context)
        move_product_qty = {}
        for move in partial.move_ids:
            if move.move_id:
                if move_product_qty.get(move.product_id.id, False): # If duplicate line
                    move_product_qty[move.product_id.id] += move.quantity
                else:
                    move_product_qty[move.product_id.id] = move.quantity
                stock_move = self.pool.get('stock.move').browse(cr, uid, move.move_id.id)
                self._check_qty_remaining(cr, uid, [stock_move.location_id.id], move.product_id.id, move_product_qty[move.product_id.id], {'uom': move.product_uom.id}, lock=True)
        return super(stock_partial_move, self).do_partial(cr, uid, ids, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
