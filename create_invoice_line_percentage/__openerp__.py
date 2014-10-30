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
    'name': 'Create Invoice Line by Percentage',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'New method to creating invoice based on Sales Order line by percentage',
    'description': """

This module add an additional method in creating Invoice from Sales Order.
It is similar to existing "Percentage" method, but instead of using the whole net amount, 
it goes into each line of Sales Order to create new Invoice.

    """,
    'category': 'Sales Management',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['sale', 'purchase_product_uos', 'advance_and_additional_discount'],
    'demo': [],
    'data': ['wizard/sale_make_invoice_advance.xml',
              'wizard/purchase_make_invoice_advance.xml',
              'purchase_view.xml',
              'sale_view.xml'],
    'test': [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
