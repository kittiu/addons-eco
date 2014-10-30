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
    'name' : 'Billing Process',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Group invoice as billing before payment',
    'description': """
Billing Process
======================================================
In some countries, at least for Thailand, there is a customary practice for companies to collect money 
from their customers only once in a month. For example, the customer has 3 payments due in a given month, 
the vendor or billing company should group all the due AR Invoices in a document call Billing Document 
and issue it with all the invoices consolidated to the customer on the Billing Day. 
The customer will be paying based on the payable amount shown in Billing Document in the following month.
    """,
    'category': 'Accounting & Finance',
    'sequence': 4,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [
                ],
    'depends' : ['account','account_voucher','account_check_writing'],
    'demo' : [],
    'data' : [
        'security/ir.model.access.csv',
        'account_billing_sequence.xml',
        'account_billing_workflow.xml',
        'account_billing_view.xml',
        'voucher_payment_receipt_view.xml',
        'account_billing_data.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
