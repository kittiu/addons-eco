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


class payment_register(osv.osv):

    _inherit = 'payment.register'

    # If payment register state changed, update commission line
    def write(self, cr, uid, ids, vals, context=None):
        res = super(payment_register, self).write(cr, uid, ids, vals, context=context)
        if 'state' in vals:
            # Get invoice ids from this payment detail
            cr.execute("""
                select av.id from payment_register pr
                join account_voucher_line avl on avl.voucher_id = pr.voucher_id
                join account_move_line aml on aml.id = avl.move_line_id
                join account_invoice av on av.move_id = aml.move_id
                where pr.id in %s
            """, (tuple(ids),))
            invoice_ids = map(lambda x: x[0], cr.fetchall())
            if invoice_ids:
                # Get commission line ids from these invoice ids
                line_ids = self.pool.get('commission.worksheet.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)])
                if line_ids:
                    self.pool.get('commission.worksheet.line').update_commission_line_status(cr, uid, line_ids, context=context)
        return res

payment_register()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
