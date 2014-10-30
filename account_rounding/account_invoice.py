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
from openerp.tools.translate import _


class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'

    def _add_account_rounding(self, cr, uid, inv, res, context=None):
        sign = -1
        diff = sum([i['price'] for i in res]) - inv.amount_untaxed
        if diff:
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_journal_rounding', 'account.journal', context=context)
            prop_id = prop and prop.id or False
            if not prop_id:
                raise osv.except_osv(_('Error Accounting!'),
                    _('Account for Amount Rounding is not set!'))
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)
            res.append({
                'type': 'src',
                'name': _('Accounting Rounding'),
                'price_unit': sign * diff,
                'quantity': 1,
                'price': sign * diff,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })
        return res

    def move_line_get(self, cr, uid, invoice_id, context=None):
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        res = super(account_invoice_line, self).move_line_get(cr, uid, invoice_id, context=context)
        res = self._add_account_rounding(cr, uid, inv, res, context=context)
        return res

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
