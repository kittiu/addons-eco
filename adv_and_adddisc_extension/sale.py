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
import openerp.addons.decimal_precision as dp


class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'add_disc': fields.float('Additional Discount(%)', digits=(16, 16), readonly=True, states={'draft': [('readonly', False)]}),
        'add_disc_amt_ex': fields.float('Additional Discount Amt', digits_compute=dp.get_precision('Additional Discount'), readonly=True, states={'draft': [('readonly', False)]}),
    }

    def init(self, cr):
        # This is a helper to set old add_disc_amt_ex = add_disc_amt
        cr.execute('update sale_order set add_disc_amt_ex = add_disc_amt')

    def onchange_add_disc_amt_ex(self, cr, uid, ids, add_disc_amt_ex, amount_untaxed, context=None):
        v = {}
        if amount_untaxed:
            v['add_disc'] = float(add_disc_amt_ex) / float(amount_untaxed) * 100
        else:
            v['add_disc'] = 0.0
            v['add_disc_amt_ex'] = 0.0
        return {'value': v}

sale_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
