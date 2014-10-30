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
    'name': 'Supplier Tax Invoice Info',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'To adjust Tax base and/or Tax amount for reporting purposes',
    'description': """

This module add new tax invoice information into Supplier Invoice.
In case, there are difference in base and tax amount, user can check "Adjust Tax Invoice information for VAT report",
which will open new tab "Tax Invoice Info".

User can then enter the base and tax amount exactly as what received by supplier.

Note: Anything from this module will merely relate to reporting purposes (report to revenue department).

Note 2:
=======

On 8 August 14, N&L conclude that this module is not applicable. By using standard, we can adjust tax and account can be posted already.
For base amount, user need to do manual adjustment in line price him/herself.

In summary, simply use standard.

    """,
    'category': 'Accounting',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['account', 'account_thai_wht', 'web_m2x_options'],
    'demo': [],
    'data': [
        'account_invoice_view.xml',
        'voucher_payment_receipt_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
