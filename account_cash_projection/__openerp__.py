# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Ecosoft (<http://www.ecosoft.co.th>)
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
    "name" : "Cash Projection Report",
    "version" : "1.0",
    "depends" : ["account_voucher"],
    "author" : "Kitti U",
    "website" : "http://www.ecosoft.co.th",
    "description": """
Cash Projection Report
============================

Features
--------
This module allow user to print cash projection flow report.
Menu: Accounting/Reporting/Generic Reporting/Partners/Print Cash Projection
    """,
    "category" : "Accounting & Finance",
    "sequence": 70,
    "update_xml" : [
        "wizard/account_report_cash_projection_view.xml",
        "wizard/xls_output_wiz.xml"
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: