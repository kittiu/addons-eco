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
    'name' : 'BOI for Thai Business',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'BOI for Thai Business',
    'description': """

    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['stock',
                 'account',
                 'analytic',
                 'purchase_requisition',
                 'purchase',
                 'sale',
                 'ext_purchase', # This one can be removed if not SQP
                 'picking_invoice_relation'
    ],
    'demo' : [],
    'data' : ['account_boi_view.xml',
              'stock_view.xml',
              'purchase_requisition_view.xml',
              'purchase_view.xml',
              'sale_view.xml',
              'account_invoice_view.xml'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
