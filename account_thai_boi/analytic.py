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

class account_analytic_account(osv.osv):

    _inherit = 'account.analytic.account'
    
    def __init__(self, pool, cr):
        super(account_analytic_account, self).__init__(pool, cr)
        option = ('boi', 'BOI')
        type_selection = self._columns['type'].selection
        if option not in type_selection:
            type_selection.append(option)

account_analytic_account()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
