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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': "Thai Withholding Tax",
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'Thai Withholding Tax Extension for Accounting Mod',
    'description': """

    * Supplier/Customer Withholding Tax
    * Supplier/Customer Undue Tax
    * Correct Account Posting According to withholding rules.

Note:
* This module also require Ecosoft's addon, customer_supplier_voucher

""",
    'category': 'Accounting & Finance',
    'sequence': 8,
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': [
        'product',
        'sale',
        'purchase',
        'purchase_discount',
        'account',
        'account_voucher',
        'customer_supplier_voucher',
    ],
    'demo': [],
    'data': [
        'account_invoice_view.xml',
        'account_view.xml',
        'partner_view.xml',
        'voucher_payment_receipt_view.xml',
        'customer_supplier_voucher.xml',
        'security/ir.model.access.csv',
        'reports/custom_reports.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
