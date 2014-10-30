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
    'name': 'Invoice to Picking Relation',
    'version': '1.0',
    'author': 'Ecosoft, Camptocamp',
    'summary': 'Adds reference between Invoice and Picking',
    'description': """
This module is based on picking_invoice_rel module from camptocamp, but has been improved to cover more cases of relationships.
    """,
    'category': 'Accounting & Finance',
    'sequence': 4,
    'website': 'http://ecosoft.co.th/',
    'images': [],
    'depends': ['stock',
                 'account',
                 'purchase',
                 'sale'],
    'demo': [],
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'invoice_view.xml',
        'picking_view.xml',
        'stock_view.xml',
    ],
    'test': [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
