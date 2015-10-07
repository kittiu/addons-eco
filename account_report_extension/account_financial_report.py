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
from openerp.tools.translate import _

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------

class account_financial_report(osv.osv):
    _inherit = "account.financial.report"
    #Overwrite
    def _get_children_by_order(self, cr, uid, ids, context=None):
        '''returns a dictionary with the key= the ID of a record and value = all its children,
           computed recursively, and sorted by sequence. Ready for the printing'''
        res = []
        for id in ids:
            res.append(id)
            ids2 = self.search(cr, uid, [('parent_id', '=', id)], order='sequence ASC', context=context)
            res += self._get_children_by_order(cr, uid, ids2, context=context)
        return res
account_financial_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
