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
    'name' : 'Payment Register',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': "",
    'description': """

Extra step to normal Customer Payment, to register payment to appropriate payment channel.

* Allow cancellation and set to draft.
* Adding bounced check feature.

    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['account_voucher','account_billing','customer_supplier_voucher'],
    'demo' : [],
    'data' : [
            'data/payment_register_data.xml',
            'security/ir.model.access.csv',
            'payment_register_sequence.xml',
            'payment_register_workflow.xml',
            #'payment_register_report.xml',
            'voucher_payment_receipt_view.xml',
            'payment_register_view.xml',
            'payment_register_data.xml',
            ],
    'test' : [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
