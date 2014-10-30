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

class account_common_account_report(osv.osv_memory):
    _inherit = "account.common.account.report"
    _columns = {
        'account_ids': fields.many2many('account.account', string='Accounting'),
        'from_account': fields.integer('From Account'),
        'to_account': fields.integer('To Account'),
    }
    
    def onchange_account(self, cr, uid, ids, from_account, to_account):
        result = {}
        res = {}
        account_codes = range(from_account, to_account + 1)
        account_codes = map(str, account_codes)
        account_ids = self.pool.get('account.account').search(cr, uid, [('code', 'in', account_codes)])
        res['account_ids'] = account_ids
        result['value'] = res
        return result

    def pre_print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = super(account_common_account_report, self).pre_print_report(cr, uid, ids, data, context)
        data['form'].update(self.read(cr, uid, ids, ['account_ids'], context=context)[0])
        data['form'].update(self.read(cr, uid, ids, ['from_account', 'to_account'], context=context)[0])
        return data

account_common_account_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
