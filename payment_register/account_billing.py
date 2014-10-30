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
# TODO
# - Only create Payment Register, if Type = Receipt


import time
from lxml import etree

from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class account_billing(osv.osv):
    
    def _get_journal(self, cr, uid, context=None):
        # Ignore the more complex account_voucher._get_journal() and simply return Bank in tansit journal.
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'payment_register', 'bank_intransit_journal')
        return res and res[1] or False
    _inherit = 'account.billing'
    _columns = {
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True),                
    }
    _defaults = {
        'journal_id': _get_journal,
    }
    
account_billing()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
