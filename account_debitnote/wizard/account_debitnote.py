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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class account_debitnote(osv.osv_memory):

    """Debit Note invoice"""

    _name = "account.debitnote"
    _description = "Invoice Debit Note"
    _columns = {
       'date': fields.date('Date', help='This date will be used as the invoice date for debit note and period will be chosen accordingly!'),
       'period': fields.many2one('account.period', 'Force period'),
       'journal_id': fields.many2one('account.journal', 'Debit Journal', help='You can select here the journal to use for the debit note that will be created. If you leave that field empty, it will use the same journal as the current invoice.'),
       'description': fields.char('Reason', size=128, required=True),
    }

    def _get_journal(self, cr, uid, context=None):
        obj_journal = self.pool.get('account.journal')
        user_obj = self.pool.get('res.users')
        if context is None:
            context = {}
        inv_type = context.get('type', 'out_invoice')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        type = (inv_type == 'out_invoice') and 'sale_debitnote' or \
               (inv_type == 'in_invoice') and 'purchase_debitnote'
               
        journal = obj_journal.search(cr, uid, [('type', '=', type), ('company_id','=',company_id)], limit=1, context=context)
        return journal and journal[0] or False

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'journal_id': _get_journal,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        journal_obj = self.pool.get('account.journal')
        user_obj = self.pool.get('res.users')
        # remove the entry with key 'form_view_ref', otherwise fields_view_get crashes
        context.pop('form_view_ref', None)
        res = super(account_debitnote,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('type', 'out_invoice')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        journal_type = (type == 'out_invoice') and 'sale_debitnote' or \
                       (type == 'in_invoice') and 'purchase_debitnote'
        for field in res['fields']:
            if field == 'journal_id':
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', journal_type), ('company_id','child_of',[company_id])], context=context)
                res['fields'][field]['selection'] = journal_select
        return res

    def compute_debitnote(self, cr, uid, ids, context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice debitnote’s ID or list of IDs

        """
        inv_obj = self.pool.get('account.invoice')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        res_users_obj = self.pool.get('res.users')
        if context is None:
            context = {}

        for form in self.browse(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.journal_id.id
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error!'), _('Cannot create debit note for draft/proforma/cancel invoice.'))
                if form.period.id:
                    period = form.period.id
                else:
                    period = inv.period_id and inv.period_id.id or False

                if not journal_id:
                    journal_id = inv.journal_id.id

                if form.date:
                    date = form.date
                    if not form.period.id:
                            cr.execute("select name from ir_model_fields \
                                            where model = 'account.period' \
                                            and name = 'company_id'")
                            result_query = cr.fetchone()
                            if result_query:
                                cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                                    and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                            else:
                                cr.execute("""SELECT id
                                        from account_period where date(%s)
                                        between date_start AND  date_stop  \
                                        limit 1 """, (date,))
                            res = cr.fetchone()
                            if res:
                                period = res[0]
                else:
                    date = inv.date_invoice
                if form.description:
                    description = form.description
                else:
                    description = inv.name

                if not period:
                    raise osv.except_osv(_('Insufficient Data!'), \
                                            _('No period found on the invoice.'))

                debitnote_id = inv_obj.debitnote(cr, uid, [inv.id], date, period, description, journal_id, context=context)
                debitnote = inv_obj.browse(cr, uid, debitnote_id[0], context=context)
                inv_obj.write(cr, uid, [debitnote.id], {'date_due': date,
                                                'check_total': inv.check_total})
                inv_obj.button_compute(cr, uid, debitnote_id)

                created_inv.append(debitnote_id[0])
                
            xml_id = (inv.type == 'out_invoice') and 'action_invoice_tree1' or \
                     (inv.type == 'in_invoice') and 'action_invoice_tree2'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result

    def invoice_debitnote(self, cr, uid, ids, context=None):
        return self.compute_debitnote(cr, uid, ids, context=context)


account_debitnote()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
