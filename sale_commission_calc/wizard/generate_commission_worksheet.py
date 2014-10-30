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

from openerp.osv import osv, fields
from openerp.tools.translate import _


class generate_commission_worksheet(osv.osv_memory):

    _name = "generate.commission.worksheet"
    _description = "Generate Commission Worksheet"

    _columns = {
        'result': fields.text('Result', readonly=True),
        'state': fields.selection([('init', 'init'), ('done', 'done')], 'Status', readonly=True),
    }
    _defaults = {
        'state': 'init',
    }

    def _create_worksheets(self, cr, uid, sales_worksheets, team_worksheets, context=None):
        worksheet_obj = self.pool.get('commission.worksheet')
        for worksheet in sales_worksheets:  # Sales
            worksheet_obj.create(cr, uid, worksheet)
        for worksheet in team_worksheets:  # Team
            worksheet_obj.create(cr, uid, worksheet)
        # Return Message
        result_message = sales_worksheets and _('Number of Salesperson Commission Worksheet') + ' = ' + str(len(sales_worksheets)) or ''
        result_message += sales_worksheets and "\n" or ''
        result_message += team_worksheets and _('Number of Team Commission Worksheet') + ' = ' + str(len(team_worksheets)) or ''
        return result_message

    def generate_worksheet(self, cr, uid, ids, context=None):

        # For each sales person with commission rule, find all period that worksheet has not been created for.
        sales_worksheets = []
        team_worksheets = []
        # Sales Person Worksheet
        cr.execute("""select salesperson_id, period_id from
                    (select distinct team.salesperson_id, ai.period_id from account_invoice_team team
                    join account_invoice ai on ai.id = team.invoice_id
                    where ai.state in ('open','paid') and ai.period_id is not null
                    ) a except (select distinct salesperson_id, period_id from commission_worksheet)
                    order by salesperson_id, period_id""")
        for res in cr.dictfetchall():
            sales_worksheets.append({'salesperson_id': res['salesperson_id'],
                                           'period_id': res['period_id']})
        # Team Work Sheet
        cr.execute("""select sale_team_id, period_id from
                    (select distinct team.sale_team_id, ai.period_id from account_invoice_team team
                    join account_invoice ai on ai.id = team.invoice_id
                    where ai.state in ('open','paid') and ai.period_id is not null
                    ) a except (select distinct sale_team_id, period_id from commission_worksheet)
                    order by sale_team_id, period_id""")
        for res in cr.dictfetchall():
            team_worksheets.append({'sale_team_id': res['sale_team_id'],
                                        'period_id': res['period_id']})
        # Create worksheet
        result_message = self._create_worksheets(cr, uid, sales_worksheets, team_worksheets, context=context)

        self.write(cr, uid, ids, {'result': result_message, 'state': 'done'}, context=context)
        res = {
            'name': _("Generate Commission Worksheet"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'generate.commission.worksheet',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
