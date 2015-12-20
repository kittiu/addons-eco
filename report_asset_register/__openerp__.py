# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Ecosoft (<http://www.Ecosoft.co.th >)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name' : 'Asset Register Report',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'website' : 'http://ecosoft.co.th',
    'category' : 'Accounting & Finance',
    'depends' : [
        'stock_asset',
    ],
    'description': '''
Asset Register Report
======================================
- This module used to print assets register report:
- Menu: Invoicing/Reporting/Generic Reporting/Assets/Assets Register
    ''',
    'demo' : [],
    'data' : [
        'wizard/fixed_asset_register_report_view.xml',
        'asset_view.xml',
        'asset_report_view.xml'
    ],
    'installable' : True,
    'active' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
