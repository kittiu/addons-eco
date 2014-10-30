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

class sale_order(osv.osv):

    _inherit = 'sale.order'
    
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        super(sale_order,self)._create_pickings_and_procurements(cr, uid, order, order_lines, picking_id=picking_id, context=context)
        # update picking created by this order with shipping_id
        picking_obj = self.pool.get('stock.picking.out')
        picking_ids = picking_obj.search(cr, uid, [('origin','=',order.name)])
        picking_obj.write(cr, uid, picking_ids, {'shipper_id': order.shipper_id.id}, context=context)
        
        return True
       
sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
