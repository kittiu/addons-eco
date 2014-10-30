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
    'name' : 'Cancel Invoice and Return Shipments',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Canceling of Invoice to automatic make relevante to return to delivered shipments, all in one click.',
    'description': """

This module put more accounting control into invoice cancellation.

As-Is:
* User cancel invoice, and know the DO number,
* User search for the DO, and click Return Products. A new Return Document will be created.
* User go to that document and click Receive (with/without new invoice)


To-Be:
* User cancel invoice, a wizard asking return will be with/without new invoice. - Done.

    """,
    'category': 'Accounting',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['account', 'picking_invoice_relation'],
    'demo' : [],
    'data' : [
        'wizard/invoice_cancel_return_picking_view.xml',
        'account_invoice_view.xml'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
