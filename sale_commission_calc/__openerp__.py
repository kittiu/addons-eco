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
    'name': "Sales Commission Calculations",
    'author': 'Ecosoft',
    'summary': '',
    'description': """

Commission is something seem easy, yet never easy. What make it difficult is not the calculation method itself,
but more into how and when the readily calculated commission can be released too sales people. For example,
some company may says, OK, we have SO we have Invoice, commission is calculated, but to release it,
the invoice must has been paid first. Some says, not enough, the money must be in the bank too. Some says,
need the be paid on time and the selling price must not too low, etc…and guess what, it could be more complex
than this especially when deal with SMEs.

Our commission module is very much focus on the release condition of commissions, which we think is very
important for our customer requirement. For the commission calculation, though at the beginning we have 5 method
(for most customers, should be enough), but we have make sure that our code is good enough for easy extension.

Concept
=======

Each Salesperson (or Team) will have 1 Worksheet per Period.
Each worksheet will list commission lines, each with a calculated commission to be released as Commission Invoice.
Commission amount will be created based on the Commission Rule assiged to each Salesperson (or Team).
Whether each commission line is "Ready" will be based Release Conditions specified for each salesperson / team.
If those conditions are met (e.g., is paid, due date, etc) the commission line status will be changed to "Ready",
and the commission invoice then can be created for that particular salesperson.
And whether or not the commission is ready, user can always force release or skip.

Workflows
=========

1) Assign commission rule and release conditions for all salesperson / sales team. Use Configuration > Salesperson (or Sales Team).
2) In each Sales Order, as salesperson assigned, resulting Customer Invoice will have that salesperson / team in "Salesperson/Team and Commission" section of Other Info tab. This mark this invoices as eligible for commision for this salesperson.
3) Create Commission Worksheet for Salesperson / Team vs Period of interest.
4) Click "Calculate Commission" in the worksheet to list all eligible invoices of the period. System check for the commission readiness of each line.
5) Confirm this worksheet to freeze the commission lines, and make it ready to Create Commission Invoice.
6) For lines stated as "Ready", click "Create Commission Invoice" button will create Commission Invoices.
7) Worksheet state will be "Done" as all lines stated as "Ready" has been created as Commission Invoices.

Menus / Windows
===============

Module **Commission Calc** located under **Sales** Module

Working Windows
---------------

* **Salesperson Worksheet:** The worksheet is the main window to work on. One worksheet can be created for a person in a period.

  Following are the states of this worksheet.

  * Draft -> As the worksheet is created. User can click "Calculate Commission" to create commission lines
  * Confirmed -> As user reviewed the worksheet and approve as is. Once confirmed, no more lines can be added. But the status of each line can get updated as times goes. During this state, user can click "Create Commission Invoices" for which line with status "Ready" will be used, after that, status will change to "Done"
  * Done -> As all commission with status "Ready" has been created as commission invoices, the status will be changed to "Done" automatically.
  * Cancelled -> As user decide not to give any commission to this salesperson.

  "Commission Invoices" Tab will show commission invoice created from this worksheet.

* **Team Worksheet:** Work exactly the same as Salesperson. Each salesperson in team will get the same commission, meaning, when generate Commission Invoices, each person will get his/her copy of Commission Invoices. E.g., 3 person in a team. When click "Create Commission Invoices", 3 commission invoices will be created, each for each person.

Setup Windows
-------------

Commission Rules
~~~~~~~~~~~~~~~~

* **Commission Rules:** Multiple Rules can be created. The amount of calculation will be based on Invoice Amount.
  Currently, there are 5 commission calculation methods available.

  * Fixed Commission Rate -> Commission = [Commission Rate] * [Base Amount]
  * Product Category Commission Rate -> Commission = SUM([Category Rate] * [Product Line Base Amount])
  * Product Commission Rate -> Commission = SUM([Product Rate] * [Product Line Base Amount])
  * Product Commission Rate Step -> Commission = SUM([Product Rate] * [Product Line Base Amount]), where [Product Rate] is based on the Sales Unit Price.
  * Commission Rate by Order Amount -> Commission = [Commission Rate] * [Base Amount], where [Commission Rate] depends on the amount of invoice.

Commission Rates
~~~~~~~~~~~~~~~~

* **Product Rates:** product rate configuration window
* **Product Rate Price Step:** product rate by sales unit price configuration window
* **Product Category Rates:** product category rate configuration window

Configuration
~~~~~~~~~~~~~

* **Salespersons:** define "Applied Commission Rule" and release conditions for each sales person.
* **Sale Teams:** define "Applied Commission Rule" and release conditions for each team.

**Note:** Condition consist of -> "Last Pay Due Date", "Require Paid Invoice", "Require Payment Detail Posted", "Allow Overdue" and "Buffer Days"

* **Update Invoices:** this wizard help assign salesperson / sales team to the unassigned invoices, mainly for backward compatibility.
* **Create Worksheet(s):** this wizard help create all uncreated draft worksheet for all salesperson / sales team in one go.

Group / Securities
==================

1) See Own Worksheet: see only their own worksheet in readonly mode.
2) User: full access in all windows and operation, except can not confirm worksheet.
3) Manager: full access in all windows, and can confirm worksheet.

""",
    'category': 'Sales',
    'sequence': 8,
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['product', 'sale', 'account', 'payment_register'],
    'demo': [],
    'init_xml': [
          'commission_data.xml',
          'product_data.xml',
    ],
    'data': [
        'security/module_data.xml',
        'security/sale_commission_calc_security.xml',
        'security/ir.model.access.csv',
        'wizard/create_commission_invoice_view.xml',
        'wizard/invoice_info_view.xml',
        'commission_calc_view.xml',
        'commission_rule_view.xml',
        'account_invoice_view.xml',
        'commission_calc_sequence.xml',
        'wizard/update_invoice_commission_view.xml',
        'wizard/generate_commission_worksheet_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
