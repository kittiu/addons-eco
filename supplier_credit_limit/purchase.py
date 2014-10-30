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


class purchase_order(osv.osv):

    _inherit = "purchase.order"

    def check_limit(self, cr, uid, ids, context=None):
        for order_id in ids:
            processed_order = self.browse(cr, uid, order_id, context=context)
            partner = processed_order.partner_id
            if partner.debit_limit > 0:
                debit = partner.debit
                available_credit = partner.debit_limit - debit
                if processed_order.amount_total > available_credit:
                    title = 'Credit Over Limits!'
                    msg = 'Can not confirm Purchase Order, the credit balance is %s'
                    raise osv.except_osv(_(title), _(msg) % (available_credit,))
                    return False
        return True

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
