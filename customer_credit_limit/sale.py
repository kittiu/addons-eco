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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = "sale.order"

    def check_limit(self, cr, uid, ids, context=None):
        for order_id in ids:
            processed_order = self.browse(cr, uid, order_id, context=context)
            if processed_order.order_policy == 'prepaid':
                continue
            partner = processed_order.partner_id
            if partner.credit_limit > 0:
                credit = partner.credit
                available_credit = partner.credit_limit - credit
                if processed_order.amount_total > available_credit:
                    title = 'Credit Over Limits!'
                    msg = u'Can not confirm the order since the credit balance is %s\n \
    You can still process the Sales Order by change the Invoice Policy to "Before Delivery."'
                    raise osv.except_osv(_(title), _(msg) % (available_credit,))
                    return False
        return True

sale_order()
