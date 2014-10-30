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


class job_cost_sheet_report(osv.osv):
    _name = "job.cost.sheet.report"
    _description = "Job Cost Sheet"
    _auto = False
    #_rec_name = 'date'
    _columns = {
        'sale_order_id': fields.many2one('sale.order', 'Sales Order', readonly=True),
        'move_id': fields.many2one('account.move', 'Journal', readonly=True),
        'account_id': fields.many2one('account.account', 'Account', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'date': fields.date('Date Order', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'amount_net': fields.float('Amount', readonly=True),
        'amount_cost': fields.float('Cost', readonly=True),
        'amount_margin': fields.float('Margin', readonly=True),
        'percent_margin': fields.float('Percent Margin', readonly=True, group_operator="avg"),
    }
    _order = 'sale_order_id'

    def init(self, cr):
        # Main
        tools.drop_view_if_exists(cr, 'job_cost_sheet_1')
        cr.execute("""
            create or replace view job_cost_sheet_1 as (
                select min(aml.id) id,
                        aml.ref_sale_order_id as sale_order_id,
                        aml.move_id,
                        aml.account_id,
                        aml.product_id,
                        so.date_order as date,
                        so.user_id,
                        to_char(so.date_order, 'YYYY') as year,
                        to_char(so.date_order, 'MM') as month,
                        to_char(so.date_order, 'YYYY-MM-DD') as day,
                        avg(so.amount_net) as amount_net,
                        sum(aml.debit-aml.credit) as amount_cost
                from account_move_line aml
                join account_account aa on aa.id = aml.account_id and aa.job_cost_sheet = true
                join sale_order so on so.id = aml.ref_sale_order_id
                group by aml.id,
                        aml.ref_sale_order_id,
                        aml.move_id,
                        aml.account_id,
                        aml.product_id,
                        so.date_order,
                        so.user_id
            )
        """)
        # Count SO
        tools.drop_view_if_exists(cr, 'job_cost_sheet_2')
        cr.execute("""
            create or replace view job_cost_sheet_2 as (
                select sale_order_id, count(*) so_count
                    from job_cost_sheet_1
                    group by sale_order_id
            )
        """)
        # Final Report (avg amount and margin)
        tools.drop_view_if_exists(cr, 'job_cost_sheet_report')
        cr.execute("""
            create or replace view job_cost_sheet_report as (
                select *, ((case when coalesce(a.amount_net, 0.0) = 0 then 0 else amount_margin / a.amount_net end) * 100)::decimal(16,2) as percent_margin
                from (
                        select id,
                            a.sale_order_id,
                            a.move_id,
                            a.account_id,
                            a.product_id,
                            a.date,
                            a.user_id,
                            a.year,
                            a.month,
                            a.day,
                            (a.amount_net / b.so_count)::decimal(16,2) as amount_net,
                            a.amount_cost,
                            (a.amount_net / b.so_count)::decimal(16,2) - a.amount_cost as amount_margin
                        from job_cost_sheet_1 a
                        left outer join job_cost_sheet_2 b on a.sale_order_id = b.sale_order_id) a            )
        """)
job_cost_sheet_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
