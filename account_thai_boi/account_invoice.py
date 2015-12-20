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

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def _get_boi(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.purchase_order_ids:  # PO
                res[invoice.id] = invoice.purchase_order_ids[0] and invoice.purchase_order_ids[0].boi_id.id or False
            elif invoice.sale_order_ids:  # SO
                res[invoice.id] = invoice.sale_order_ids[0] and invoice.sale_order_ids[0].boi_id.id or False
        return res    
        
    _columns = {
        'boi_id': fields.function(_get_boi, type='many2one', relation='account.boi', string='BOI Cert', readonly=True, store=True),
    }

account_invoice
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
