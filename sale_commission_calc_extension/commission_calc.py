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

from openerp.osv import osv


class commission_worksheet(osv.osv):

    _inherit = 'commission.worksheet'

    def final_update_invoice(self, cr, uid, inv_rec, context=None):
        # Add additional deduction to commission
        inv_rec.update({'add_disc': context.get('percent_deduction_amt', False)})
        return inv_rec

    #  This part deal with the calculation of commission
#     def _prepare_worksheet_line(self, worksheet, invoice, base_amt, commission_amt, context=None):
#         res = super(commission_worksheet, self)._prepare_worksheet_line(worksheet, invoice, base_amt, commission_amt, context=context)
#         commission_amt = res.get('commission_amt', 0.0) * (100.0 - invoice.add_disc) / 100
#         res.update({'commission_amt': commission_amt})
#         return res

    def _get_base_amount(self, invoice):
        # Case with Additional Discount
        base_amt = invoice.amount_net
        return base_amt
    # --- This sections provide logics for each rules ---

commission_worksheet()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
