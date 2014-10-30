# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Sales Order Ref',
    'version': '0.1',
    'author': 'Ecosoft',
    'summary': "Add Sales Order Reference to other documents",
    'description': """

The propose of this module is to add reference to sales order in order to calculate the cost occured for that sales order,
especially from Purchase Orders.

The Ref Sales Order can be filled "Manually" at this moment.

Following documents are added "ref_sale_id",

* Purchase Requisition
* Purchase Order
* Supplier Invoice
* Incoming Shipment

TODO:

* Automatically by procurement process
* Selection of SO Lines in PR/PO, to make it more fine grain.

    """,
    'category': 'Sales Management',
    'website': 'http://ecosoft.co.th',
    'images': [],
    'depends': ['web_m2x_options', 'sale', 'sale_stock', 'purchase_requisition', 'purchase'],
    'demo': [],
    'data': [
        'purchase_requisition_view.xml',
        'purchase_view.xml',
        'stock_view.xml',
    ],
    'test': [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
