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
    'name': 'Customer Credit Limit',
    'version': '1.0',
    'description': """Customer Credit Limit
    When approving a Sale Order it computes the sum of:
        * The credit the Partner has to paid
        * The amount of the Sale Order to be aproved
    and compares it with the credit limit of the partner. If the
    credit limit is less it does not allow to approve the Sale
    Order""",
    'author': 'Sistemas ADHOC, ECOSOFT',
    'website': 'http://www.sistemasadhoc.com.ar/,http://www.ecosoft.co.th',
    'depends': ['account', 'sale'],
    'init_xml': [],
    'update_xml': ['sale_workflow.xml'],
    'demo_xml': [],
    'test': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
