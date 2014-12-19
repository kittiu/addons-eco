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
    'name': 'Job Cost Sheet',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'Job Cost Sheet Report SO price vs Expense cost',
    'description': """

All Expense Documents (i.e., Invoice, Expense, etc) will have reference with Sales Order, 
and will be passed to following document, PR -> PO -> Supplier Invoice

Account Code to be used as Cost in the Job Cost Sheet, can be defined in Account window.

Report located in manu Reporting > Sales > Job Cost Sheet


    """,
    'category': 'Accounting',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['web_m2x_options',
                'purchase',
                'purchase_requisition',
                'account',
                'picking_invoice_relation',
                'currency_rate_enhanced'],
    'demo': [],
    'data': ['purchase_requisition_view.xml',
             'purchase_view.xml',
             'account_invoice_view.xml',
             'account_view.xml',
             'report/job_cost_sheet_report_view.xml'
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
