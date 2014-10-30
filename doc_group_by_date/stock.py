#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from openerp.osv import fields, osv


class stock_picking(osv.osv):

    _inherit = "stock.picking"

    def _get_date_string(self, cr, uid, ids, name, args, context=None):
        res = {}
        for picking in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
            res[picking.id] = picking.min_date and datetime.strptime(picking.min_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        return res

    _columns = {
        'date_str': fields.function(_get_date_string, type='char', size=10, string="Date String", store=True),
    }

    def _update_date_string(self, cr, uid, ids=None, context=None):
        cr.execute("update stock_picking set date_str = to_char(min_date, 'YYYY-MM-DD');")

stock_picking()


class stock_picking_out(osv.osv):

    _inherit = "stock.picking.out"

    def _get_date_string(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking')._get_date_string(cr, uid, ids, name, args, context=context)   

    _columns = {
        'date_str': fields.function(_get_date_string, type='char', size=10, string="Date String", store=True),
    }

stock_picking_out()


class stock_picking_in(osv.osv):

    _inherit = "stock.picking.in"

    def _get_date_string(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking')._get_date_string(cr, uid, ids, name, args, context=context)

    _columns = {
        'date_str': fields.function(_get_date_string, type='char', size=10, string="Date String", store=True),
    }

stock_picking_out()


class stock_move(osv.osv):

    _inherit = "stock.move"

    def _get_date_string(self, cr, uid, ids, name, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = move.date_expected and datetime.strptime(move.date_expected, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        return res

    _columns = {
        'date_str': fields.function(_get_date_string, type='char', size=10, string="Date String", store=True),
    }

    def _update_date_string(self, cr, uid, ids=None, context=None):
        cr.execute("update stock_move set date_str = to_char(date_expected, 'YYYY-MM-DD');")

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
