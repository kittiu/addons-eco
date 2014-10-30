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

from openerp.osv import osv
from openerp import netsvc


class stock_picking_out(osv.osv):

    _inherit = "stock.picking.out"

    def  action_cancel_draft(self, cr, uid, ids, context=None):
        pickings = self.browse(cr, uid, ids, context)

        for picking in pickings:
            update_val = {'state': 'draft', 'invoice_state': '2binvoiced' if picking.sale_id and picking.sale_id.order_policy == 'picking' else 'none', }
            self.write(cr, uid, picking.id, update_val, context)
        move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', ids)], context=context)
        self.pool.get('stock.move').write(cr, uid, move_line_ids, {'state': 'draft'}, context)

        wf_service = netsvc.LocalService("workflow")
        for picking_id in ids:
            wf_service.trg_create(uid, 'stock.picking', picking_id, cr)

        for line_id in move_line_ids:
            wf_service.trg_create(uid, 'stock.move', line_id, cr)

        return True

stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
