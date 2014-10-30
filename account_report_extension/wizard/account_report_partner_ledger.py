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

from openerp.osv import  osv


class account_partner_ledger(osv.osv_memory):
    """
    This wizard will provide the partner Ledger report by periods, between any two dates.
    """
    _name = 'account.partner.ledger'
    _inherit = ['account.partner.ledger', 'account.common.partner.report']
    _description = 'Account Partner Ledger'

    def _print_report(self, cr, uid, ids, data, context=None):
        res = super(account_partner_ledger, self)._print_report(cr, uid, ids, data, context)
        data['form'].update(self.read(cr, uid, ids, ['partner_ids'], context=context)[0])
        data['model'] = 'res.partner'
        if data['form']['page_split']:
            res.update({'report_name': 'account.third_party_ledger_ext'})
        else:
            res.update({'report_name': 'account.third_party_ledger_other_ext'}),
        return res

account_partner_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
