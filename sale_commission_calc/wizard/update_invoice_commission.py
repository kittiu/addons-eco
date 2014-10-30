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

from openerp.osv import osv, fields
from openerp.tools.translate import _


class update_invoce_commission(osv.osv_memory):

    _name = "update.invoice.commission"
    _description = "Update Invoice Commission"

    _columns = {
        'result': fields.text('Result', readonly=True),
        'state': fields.selection([('init', 'init'), ('done', 'done')], 'Status', readonly=True),
    }
    _defaults = {
        'state': 'init',
    }

    def update_commission(self, cr, uid, ids, context=None):
        updated = 0
        invoice_obj = self.pool.get('account.invoice')
        invoice_team_obj = self.pool.get('account.invoice.team')
        # Get salepersons/team commission for users in invoices
        cr.execute("select distinct user_id from account_invoice where type in ('out_invoice','out_refund')")
        users = cr.dictfetchall()
        for user in users:
            user_id = user['user_id']
            # For this users, find relevant commission
            salespersons = invoice_obj._get_salesperson_comm(cr, uid, user_id)
            sale_teams = invoice_obj._get_sale_team_comm(cr, uid, user_id)
            invoice_comms = salespersons + sale_teams
            if not invoice_comms:
                continue
            # For this users, find relevant invoices
            invoice_ids = invoice_obj.search(cr, uid, [('user_id', '=', user_id), ('type', 'in', ('out_invoice', 'out_refund'))])
            invoices = invoice_obj.browse(cr, uid, invoice_ids)
            # Only for invoice without commission, create it.
            for invoice in invoices:
                if not invoice.sale_team_ids:
                    for invoice_comm in invoice_comms:
                        invoice_comm.update({'invoice_id': invoice.id})
                        invoice_team_obj.create(cr, uid, invoice_comm)
                    updated += 1
        # Message
        result_message = _('Number of invoice updated') + ' = ' + str(updated)

        self.write(cr, uid, ids, {'result': result_message, 'state': 'done'}, context=context)
        res = {
            'name': _("Update Invoice's Commission"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.invoice.commission',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
