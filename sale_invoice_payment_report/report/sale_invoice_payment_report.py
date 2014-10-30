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

from openerp import tools
from openerp.osv import fields, osv


class sale_invoice_payment_report(osv.osv):

    _name = "sale.invoice.payment.report"
    _description = "Sales-Invoice-Payment Analysis"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True),
        'order_id': fields.many2one('sale.order', 'Sales Order', readonly=True),
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'order_amount': fields.float('Amount', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'invoiced_amount': fields.float('Invoiced', readonly=True),
        'unpaid_amount': fields.float('Unpaid', readonly=True),
        'paid_amount': fields.float('Paid', readonly=True),
        'percent_paid': fields.float('Percent Paid', readonly=True, group_operator="avg"),
    }
    _order = 'date desc'

    def init(self, cr):
        # self._table = sale_invoice_payment_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW sale_invoice_payment_report as (
            select *, ((case when coalesce(order_amount, 0) = 0 then 1 when paid_amount > order_amount then 1 else paid_amount / order_amount end) * 100)::decimal(16,2) as percent_paid
            from (
                select *, (case when coalesce(amount_total, 0) = 0 then 0 else ((invoiced_amount / amount_total) * residual) end)::decimal(16,2) as unpaid_amount,
                    (case when coalesce(amount_total, 0) = 0 then 0 else invoiced_amount - ((invoiced_amount / amount_total) * residual) end)::decimal(16,2) as paid_amount
                    from (
                                select so.id as id,
                                    so.user_id,
                                    so.partner_id,
                                    so.id as order_id,
                                    so.date_order as date,
                                    to_char(so.date_order::timestamp with time zone, 'YYYY'::text) AS year,
                                    to_char(so.date_order::timestamp with time zone, 'MM'::text) AS month,
                                    to_char(so.date_order::timestamp with time zone, 'YYYY-MM-DD'::text) AS day,
                                    (case when coalesce(so.amount_untaxed, 0) = 0 then so.amount_untaxed else so.amount_untaxed end) as order_amount,
                                    ai.id as invoice_id,
                                    ai.amount_beforetax as invoiced_amount,
                                    -- to be calculated
                                    ai.amount_total,
                                    ai.residual
                                from sale_order so
                                left outer join sale_order_invoice_rel sir on so.id = sir.order_id
                                left outer join account_invoice ai on ai.id = sir.invoice_id and ai.state not in ('draft','cancel')
                                where so.state not in ('draft', 'cancel')
                    ) a
                ) b
        )""")

sale_invoice_payment_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
