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
from openerp.tools.translate import _

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    # Check whether product belong to category that need serial on deliver
    def action_done(self, cr, uid, ids, context=None):
            
        moves = self.browse(cr, uid, ids)
        for move in moves:
            if move.product_id.categ_id.require_serial_on_deivery and not move.prodlot_id:
                raise osv.except_osv(_('Warning'), _('Product: %s, requires a serial number to process!')% (move.product_id.name,))
                
        return super(stock_move, self).action_done(cr, uid, ids, context=context)
        
stock_move()
