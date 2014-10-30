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
    'name' : 'Product UOS for Purchase',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': "Replicate Unit of Sales concept from Sales but for Purchase",
    'description': """

This addon is not full feature, will apply concept of UOS only in the following function.

* No change in the interface of product but reuse the conversion rate from Sales' UOS
* Enforce Product's Purchase UOM always equal to Default UOM (use UOS instead)
* New UOS and UOS Qty in PUrchase Order Line.
* In Purchase Order Line, Purchase UOM will not apply to the default UOM as per existing functionality, but instead to the new UOS field.
* Incoming Shipment now have new UOS Qty column. It only use for documentation.
* Support when working with Purchase Requisition

    """,
    'category': 'Purchase',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['product',
                 'sale',
                 'purchase',
                 'purchase_requisition',
                 'web_m2x_options'],
    'demo' : [],
    'data' : [
              'product_data.xml',
              'purchase_view.xml',
              'product_view.xml',
              'stock_view.xml',
              #'wizard/stock_partial_picking_view.xml'
              ],
    'test' : [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
