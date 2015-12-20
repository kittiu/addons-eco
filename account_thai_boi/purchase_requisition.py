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

class purchase_requisition(osv.osv):
    
    _inherit = "purchase.requisition"
    
    def onchange_boi_id(self, cr, uid, ids, boi_id=False, context=None):
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('boi_id','=',boi_id)])
        if boi_id:
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False},
                   'domain': {'warehouse_id': [('id', '=', warehouse_ids)]}}
        else:
            res = {'value': {'warehouse_id': warehouse_ids and warehouse_ids[0] or False},
                   'domain': {'warehouse_id': [('id', '=', warehouse_ids)]}}
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', ondelete='restrict'),      
    }
    
    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        res = super(purchase_requisition, self).make_purchase_order(cr, uid, ids, partner_id, context=context)
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        boi_obj = self.pool.get('account.boi')
        position_obj = self.pool.get('account.fiscal.position')
        for requisition in self.browse(cr, uid, ids):
            purchase = purchase_obj.browse(cr, uid, res[requisition.id], context=context)
            # Change fiscal position based on BOI
            if requisition.boi_id:
                boi_id = requisition.boi_id.id
                fiscal_position = boi_obj.browse(cr, uid, boi_id).fiscal_position
                purchase_obj.write(cr, uid, [purchase.id], {'boi_id': boi_id,
                                                            'fiscal_position': fiscal_position.id})
                # Change tax in product line based on fiscal position
                for line in purchase.order_line:
                    taxes = position_obj.map_tax(cr, uid, fiscal_position, line.taxes_id)
                    purchase_line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, taxes)]})
        return res
    
purchase_requisition()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
