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
    'name' : "Partner's shipper",
    'author' : 'Ecosoft',
    'version' : '1.0',
    'summary': 'Additional Shipper Information for Partners',
    'description': """
This module add new shipper information,
* Adding available shipper for a partner. 
* This shipper information will be available in Other Info tabs in Customer's SO/DO/INV.
* The first shipper of a partner will be used as default shipper in Sales Order
* Shipper from Source Document will be carried to next document.
** SO --> DO --> INV
** SO --> INV
* Add group by Shipper in Delivery Order

""",
    'category': 'Sales',
    'sequence': 8,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['base', 'web_m2x_options', 'account', 'sale', 'stock', 'sale_stock'],
    'demo' : [],
    'data' : [
        'partner_shipper_view.xml',
        'partner_view.xml',
        'account_view.xml',
        'sale_view.xml',
        'stock_view.xml',
        'security/ir.model.access.csv'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
