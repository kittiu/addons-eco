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
import openerp.addons.decimal_precision as dp


class create_commission_invoice(osv.osv_memory):

    """Create Commission Invoice"""

    def _get_commission_amt(self, cr, uid, context=None):
        worksheet = self.pool.get('commission.worksheet').browse(cr, uid, context['active_id'], context=context)
        if worksheet:
            return worksheet.amount_valid
        return False

    _name = "create.commission.invoice"
    _description = "Create Commission Invoice"
    _columns = {
        'commission_amt': fields.float('Commission Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'comment': fields.text('Comment'),
    }
    _defaults = {
        'commission_amt': _get_commission_amt,
    }

    def create_commission_invoice(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        form_data = self.read(cr, uid, ids, ['comment'], context=context)[0]
        context.update({'comment': form_data['comment']})
        return self.pool.get('commission.worksheet').action_create_invoice(cr, uid, [context['active_id']], context=context)


create_commission_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
