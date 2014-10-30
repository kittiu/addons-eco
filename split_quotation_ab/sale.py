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

from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'split_ab_ref': fields.many2one('sale.order', 'Split A/B Ref', readonly=True, required=False, help='Reference Order from Split A/B'),
    }

    def split_quotation_ab(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        order = self.browse(cr, uid, ids[0])        
        
        # Create new quoation with name = <name>/B
        default = {}
        default['name'] = order.name + '/B'
        default['split_ab_ref'] = order.id
        default['order_line'] = False
        default['header_msg'] = '<div><b>LABOUR COST</b></div><br>' + order.header_msg 
        vals = {}
        vals = self.copy_data(cr, uid, ids[0], default, context)
        new_order_id = super(sale_order, self).create(cr, uid, vals, context=context)        
        
        # Change existing quotation name to <name>/A
        self.write(cr, uid, [order.id], {'name': order.name + '/A', 
                                         'split_ab_ref': new_order_id})   
        
        # redisplay the record as a sales order
        data_pool = self.pool.get('ir.model.data')
        action_model = False
        action = {}
        action_model,action_id = data_pool.get_object_reference(cr, uid, 'sale', 'action_quotations')
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in',[%s, %s])]" % (order.id, new_order_id)
        return action    

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default['split_ab_ref'] = False
        return super(sale_order, self).copy(cr, uid, id, default, context=context)

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
