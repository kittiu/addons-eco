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
    'name': 'Product Stock Card',
    'version': '1.0',
    'category': 'Warehouse',
    'description': """

Normally, when user want to see the movement of a product, they will use Inventory Move.
Although it give full information about the movement of the product, it is not easy for user to understand quickly.
Stock Card will give the movement view of a product for a location is a much simpler way.

The main purpose of Stock Card module is to show a report view of item movement for a given product for a given locaton.
It gives following information,
  * In Qty
  * Out Qty
  * Balance

Different ways to access Stock Card
===================================

1) Overall quantity in different locations in product's new tab, "Stock Location"

2) View Stock Card from selected product
  * Given a product is opened, click menu More > Stock Card
  * In product list view, select one or multiple product, then click menu More > Stock Card

  In either way, you have ability to view Stock Card in OpenERP on print it out.

3) View Stock Card from menu Warehouse > Inventory Control > Stock Card

  This way is the same as previous, except you will select product right here.

    """,
    'author': 'Ecosoft',
    'website': 'http://www.ecosoft.co.th',
    'depends': ['stock', 'product', 'jasper_reports', 'report_menu_restriction'],
    'data': [
             'product_stock_card_view.xml',
             'wizard/product_stock_card_location_view.xml',
             'security/ir.model.access.csv',
             'product_view.xml',
             'reports.xml',
    ],
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
