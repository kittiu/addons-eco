# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import fields,osv

class purchase_order(osv.osv):
    
    _inherit = "purchase.order"
    
    def onchange_boi_id(self, cr, uid, ids, boi_id=False, context=None):
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('boi_id','=',boi_id)])
        if boi_id:
            fiscal_position_id = self.pool.get('account.boi').browse(cr, uid, boi_id).fiscal_position.id
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                             'fiscal_position': fiscal_position_id},
                   'domain': {'warehouse_id': [('boi_id', '=', boi_id)]}}
        else:
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                             'fiscal_position': False},
                   'domain': {'warehouse_id': [('boi_id', '=', False)]}}
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),      
    }    
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        purchase_line_obj = self.pool.get('purchase.order.line')
        position_obj = self.pool.get('account.fiscal.position')
        for purchase in self.browse(cr, uid, ids):
            # Change fiscal position based on BOI
            fiscal_position_id = vals.get('fiscal_position', False)
            if fiscal_position_id:
                fiscal_position = position_obj.browse(cr, uid, fiscal_position_id)
                # Change tax in product line based on fiscal position
                for line in purchase.order_line:
                    taxes = position_obj.map_tax(cr, uid, fiscal_position, line.taxes_id)
                    purchase_line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, taxes)]})
        return res
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
