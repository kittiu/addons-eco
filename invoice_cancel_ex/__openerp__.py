# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Ecosoft Co., Ltd. (http://ecosoft.co.th).
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

{
    'name' : 'Cancel Invoice Extra',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Cancel Invoice by create counter document (instead of just delete journal)',
    'description': """

This module put more accounting control into invoice cancellation.

As-Is:
* Set invoice state to cancel
* Delete all related journal (account posting)

To-Be:
* Set invoice state of the invoice to cancel.
* Create new counter invoice also with state cancel.
* Create journal entry same as original document, but switch debit <-> credit
* Name the new document <old_number>_VOID
* Set to Draft button, to always create new Invoice(s)
** With DO reference, create invoice from DO
** WIthout DO reference, create invoice from copy the existing invoice

    """,
    'category': 'Accounting',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['account',],
    'demo' : [],
    'data' : [
        'account_invoice_view.xml'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
