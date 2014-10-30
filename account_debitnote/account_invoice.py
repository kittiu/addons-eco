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

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice(osv.osv):
    
    _inherit = 'account.invoice'
    
    def _debitnote_cleanup_lines(self, cr, uid, lines, context=None):
        """Convert records to dict of values suitable for one2many line creation

            :param list(browse_record) lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        clean_lines = []
        for line in lines:
            clean_line = {}
            for field in line._all_columns.keys():
                if line._all_columns[field].column._type == 'many2one':
                    clean_line[field] = line[field].id
                elif line._all_columns[field].column._type not in ['many2many','one2many']:
                    clean_line[field] = line[field]
                elif field == 'invoice_line_tax_id':
                    tax_list = []
                    for tax in line[field]:
                        tax_list.append(tax.id)
                    clean_line[field] = [(6,0, tax_list)]
            clean_lines.append(clean_line)
        return map(lambda x: (0,0,x), clean_lines)
    
    def _prepare_debitnote(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        """Prepare the dict of values to create the new debit note from the invoice.
            This method may be overridden to implement custom
            debit note generation (making sure to call super() to establish
            a clean extension chain).

            :param integer invoice_id: id of the invoice to create debit note
            :param dict invoice: read of the invoice to create debit note
            :param string date: debit note creation date from the wizard
            :param integer period_id: force account.period from the wizard
            :param string description: description of the debit note from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the debit note
        """
        obj_journal = self.pool.get('account.journal')
        
        type_list = ['out_invoice','in_invoice']
        if invoice.type not in type_list:
            raise osv.except_osv(_('Error!'), _('Can not create Debit Note from this document!'))

        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = self._debitnote_cleanup_lines(cr, uid, invoice.invoice_line, context=context)

        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._debitnote_cleanup_lines(cr, uid, tax_lines, context=context)
        if journal_id:
            debitnote_journal_ids = [journal_id]
        elif invoice['type'] == 'in_invoice':
            debitnote_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_debitnote')], context=context)
        else:
            debitnote_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_debitnote')], context=context)

        if not date:
            date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': invoice['type'],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            'invoice_line': invoice_lines,
            'tax_line': tax_lines,
            'journal_id': debitnote_journal_ids and debitnote_journal_ids[0] or False,
            'invoice_id_ref': invoice.id
        })
        if period_id:
            invoice_data['period_id'] = period_id
        if description:
            invoice_data['name'] = description
        return invoice_data

    def debitnote(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = []
        for invoice in self.browse(cr, uid, ids, context=context):
            invoice = self._prepare_debitnote(cr, uid, invoice,
                                                date=date,
                                                period_id=period_id,
                                                description=description,
                                                journal_id=journal_id,
                                                context=context)
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice, context=context))

        for new_invoice in self.browse(cr, uid, new_ids, context=context):
            if new_invoice.invoice_id_ref:
                self.write(cr, uid, [new_invoice.invoice_id_ref.id], {'invoice_id_ref': new_invoice.id})

        return new_ids
    
    def is_debitnote(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cursor, user, ids, context=context):
            if invoice.journal_id and invoice.journal_id.type in ('sale_debitnote', 'purchase_debitnote'):
                res[invoice.id] = True
            else:
                res[invoice.id] = False
        return res
    
    _columns = {
        'is_debitnote': fields.function(is_debitnote, string='Is Debit Note?', type='boolean', store=True),
    }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(account_invoice, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)        
        journal_obj = self.pool.get('account.journal')
        type = context.get('journal_type', False)
        for field in res['fields']:
            if field == 'journal_id' and type in ('sale','purchase'):
                # Add debit note type with sale type.
                if type == 'sale':
                    type = ('sale','sale_debitnote')
                if type == 'purchase':
                    type = ('purchase','purchase_debitnote')
                journal_select = journal_obj._name_search(cr, uid, '', [('type', 'in', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
