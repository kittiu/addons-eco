{
    "name": "Advance and Additional discount",
    "version": "1.0",
    "depends": ["base", "sale", "purchase", "account",
                "stock", "picking_invoice_relation",
                "account_thai_wht",
                ],
    "author": "Ecosoft",
    "category": "Sales",
    "description": """
This module add 3 new features, Additional Discount and Advance Amount (Advance and Deposit)
and lastly, the Retention.

For Additional Discount, it is the same as additional_discount module, and quite easy to use by self.

For Advance Amount, following are how it works,

* First, Accounting or Advancement need to be assigned in Settings > Configurations > Accounting
* Once this module, Create Invoice options on Sales Order will list Advance Method (Fixed and Percentage) only for the first invoice creation (was freely available without this module).
* If user select the first invoice as Advance invoice with percentage or fixed amount, the percentage will be kept in Advance Percentage field in that Sales Order.
* For Advance, all the followings invoices from that Sales Order will be deducted with the percentage specified on Sales order
* For Deposit, the full amount will be deducted in the 2nd invoice.
* Applicable for both Sales and Purchases Order.
* Accounting for invoice will be posted in regards to the deducted amount.

For Retention, following are how it works,

* Create invoice wizard (from SO), will ask if you have retention (%).
* If you specify the retention, it will be kept that % in SO, and any retention amount will be deducted from After Tax amount.
* All the following invoices will then have the retention amount.

    """,
    "init_xml": [],
    'update_xml': ['wizard/sale_make_invoice_advance.xml',
                   'wizard/purchase_make_invoice_advance.xml',
                   'wizard/sale_line_invoice.xml',
                   'decimal_data.xml',
                   'all_view.xml','partner_view.xml','res_config_view.xml',
                   'sale_workflow.xml'
                   ],
    'demo_xml': [],
    'test': [
        'test/scenario1.yml',
        'test/scenario2.yml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
#    'certificate': 'certificate',
}
