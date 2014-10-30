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

from openerp.osv import fields, osv


class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'ref_sale_order_id': fields.many2one('sale.order', 'Ref Sales Order', states={'done': [('readonly', True)]}),
    }

    def create(self, cr, uid, data, context=None):
        # if has ref_sale_order_id, copy it here.
        if data.get('requisition_id', False):
            requisition = self.pool.get('purchase.requisition').browse(cr, uid, data.get('requisition_id'), context=context)
            if requisition.ref_sale_order_id:
                data.update({'ref_sale_order_id': requisition.ref_sale_order_id.id})
        result = super(purchase_order, self).create(cr, uid, data, context=context)
        return result

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
