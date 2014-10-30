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
    
    _columns = {
        'shipper_id': fields.many2one('partner.shipper', 'Shipper', domain="[('partner_ids','in',partner_id)]"),
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        val = res.get('value')
        # get the first shipper and assign it.
        shipper_ids = self.pool.get('partner.shipper').search(cr, uid, [('partner_ids','in',part)])
        val['shipper_id'] = shipper_ids and shipper_ids[0] or False
        return {'value': val}
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        res = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped=grouped, states=states, date_invoice = date_invoice, context=context)
        inv_obj = self.pool.get('account.invoice')
        for order_id in ids:
            order = self.browse(cr, uid, order_id)
            inv_obj.write(cr, uid, [res], {'shipper_id': order.shipper_id.id}, context=context)
        return res
    
sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
