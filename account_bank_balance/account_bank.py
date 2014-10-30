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

from openerp.tools.translate import _
from openerp.osv import fields, osv


class bank(osv.osv):

    _inherit = "res.partner.bank"

    def _get_journal_currency(self, cr, uid, ids, name, args, context=None):
        res = {}
        for bank in self.browse(cr, uid, ids, context=context):
            res[bank.id] = bank.journal_id and bank.journal_id.default_debit_account_id.balance or 0.0
        return res

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.id

    _columns = {
        'balance': fields.function(_get_journal_currency, type="float", readonly=True, string="Balance in Company's Currency"),
    }
    _defaults = {
        'company_id': _default_company
    }

bank()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
