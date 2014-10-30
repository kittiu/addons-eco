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
    'name' : 'Optional Move Locations',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Additional options in defining source move locations',
    'description': """

In standard, product will be delivered from Warehouse's stock location.
This addons add more options (but will fall-back if higher priority specified),

* First Priority: Partner's Customer Delivery Source
* Second Priority: Warehouse's Warehouse Delivery Source
* Last Priority (existing): Warehouse's Location Stock
    """,
    'category': 'Warehouse Management',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['sale_stock'],
    'demo' : [],
    'data' : [
        'stock_view.xml',
        'partner_view.xml'
    ],  
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
