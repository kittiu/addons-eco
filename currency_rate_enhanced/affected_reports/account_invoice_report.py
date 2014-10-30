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
from openerp.osv import osv


class account_invoice_report(osv.osv):
    _inherit = "account.invoice.report"

    def _select(self):
        select_str = """
            SELECT sub.id, sub.date, sub.year, sub.month, sub.day, sub.product_id, sub.partner_id,
                sub.payment_term, sub.period_id, sub.uom_name, sub.currency_id, sub.journal_id,
                sub.fiscal_position, sub.user_id, sub.company_id, sub.nbr, sub.type, sub.state,
                sub.categ_id, sub.date_due, sub.account_id, sub.account_line_id, sub.partner_bank_id,
                sub.product_qty,
                cr.rate as currency_rate,
                -- kittiu
                case when curr.type_ref_base = 'smaller' then
                    sub.price_total / (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                    else
                    sub.price_total * (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                end AS price_total,
                case when curr.type_ref_base = 'smaller' then
                    sub.price_average / (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                    else
                    sub.price_average * (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                end AS price_average,
                case when curr.type_ref_base = 'smaller' then
                    sub.residual / (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                    else
                    sub.residual * (case when sub.type in ('in_invoice', 'in_refund') then cr.rate else cr.rate_sell end) 
                end AS residual
                --
        """
        return select_str

    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM (
                %s %s %s
            ) AS sub
            JOIN res_currency_rate cr ON (cr.currency_id = sub.currency_id)
            -- kittiu
            JOIN res_currency curr ON curr.id = cr.currency_id
            --
            WHERE
                cr.id IN (SELECT id
                          FROM res_currency_rate cr2
                          WHERE (cr2.currency_id = sub.currency_id)
                              AND ((sub.date IS NOT NULL AND cr2.name <= sub.date)
                                    OR (sub.date IS NULL AND cr2.name <= NOW()))
                          ORDER BY name DESC LIMIT 1)
        )""" % (
                    self._table, 
                    self._select(), self._sub_select(), self._from(), self._group_by()))

account_invoice_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
