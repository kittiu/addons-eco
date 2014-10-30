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
import time
import datetime


class sale_order(osv.osv):

    _inherit = "sale.order"

    _columns = {
        'date_expected': fields.date('Expected Delivery Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }
    _defaults = {
        'date_expected': lambda *a: datetime.datetime.now().strftime('%Y-%m-%d'),
    }

    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        # Overwrite with this date
        return order.date_expected

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
