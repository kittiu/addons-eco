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
    'name': 'Supplier Payment VAT Info',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'Additional VAT info for Tax Report purpose',
    'description': """

This module extend the Deferred / WHT Tax concept from account_thai_wht.

In that module, tax table in account_voucher displayed as Grouped Tax, which make it not possible for Thai Tax Report.

In this module, a new Vat Info tab is introduced. It will display deferred tax in detailed per supplier invoice.

    """,
    'category': 'Accounting',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': [
        'account_voucher',
        'account_thai_wht',
        'advance_and_additional_discount',
        'web_m2x_options'
    ],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'account_voucher_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
