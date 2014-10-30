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
from openerp.tools.translate import _


class create_commission_invoice(osv.osv_memory):

    _inherit = "create.commission.invoice"
    _columns = {
        'deduction_amt': fields.float('Deduction Amount', digits_compute=dp.get_precision('Account')),
    }

    def create_commission_invoice(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        form_data = self.read(cr, uid, ids, ['deduction_amt', 'commission_amt'], context=context)[0]
        deduction_amt = form_data['deduction_amt'] or 0.0
        commission_amt = form_data['commission_amt'] or 0.0
        if not deduction_amt < commission_amt:
            raise osv.except_osv(_('Warning!'), _('Deduction Amount must be less than Commission Amount'))
        context.update({'percent_deduction_amt': commission_amt > 0.0 and (deduction_amt / commission_amt) * 100 or 0.0})
        return super(create_commission_invoice, self).create_commission_invoice(cr, uid, ids, context=context)

create_commission_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
