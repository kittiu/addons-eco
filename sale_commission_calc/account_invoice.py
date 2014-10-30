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

from openerp.osv import fields, osv


class account_invoice_team(osv.osv):

    _name = "account.invoice.team"
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=False, ondelete='cascade'),
        'salesperson_id': fields.many2one('res.users', 'Salesperson', required=False),
        'sale_team_id': fields.many2one('sale.team', 'Team', required=False),
        'commission_rule_id': fields.many2one('commission.rule', 'Applied Commission', required=True, readonly=True),
    }

    def onchange_sale_team_id(self, cr, uid, ids, sale_team_id):
        result = {}
        res = {}
        if sale_team_id:
            team = self.pool.get('sale.team').browse(cr, uid, sale_team_id)
            res['commission_rule_id'] = team.commission_rule_id.id
            res['salesperson_id'] = False

        result['value'] = res
        return result

    def onchange_salesperson_id(self, cr, uid, ids, salesperson_id):
        result = {}
        res = {}
        if salesperson_id:
            salesperson = self.pool.get('res.users').browse(cr, uid, salesperson_id)
            res['commission_rule_id'] = salesperson.commission_rule_id.id
            res['sale_team_id'] = False

        result['value'] = res
        return result

account_invoice_team()


class account_invoice(osv.osv):

    _inherit = "account.invoice"
    _columns = {
        'sale_team_ids': fields.one2many('account.invoice.team', 'invoice_id', 'Teams', states={'draft': [('readonly', False)]}),
        'worksheet_id': fields.many2one('commission.worksheet', 'Commission Worksheet', readonly=True)
    }

    def _get_salesperson_comm(self, cr, uid, user_id):
        salesperson_recs = []
        if user_id:
            salesperson = self.pool.get('res.users').browse(cr, uid, user_id)
            if salesperson.commission_rule_id:
                salesperson_recs.append({'salesperson_id': salesperson.id, 'commission_rule_id':
                                         salesperson.commission_rule_id.id})
        return salesperson_recs

    def _get_sale_team_comm(self, cr, uid, user_id):
        team_recs = []
        if user_id:
            cr.execute("""select a.tid team_id, b.tid as inherit_id  from sale_team_users_rel a
                            left outer join sale_team_implied_rel b on b.hid = a.tid
                            where uid = %s
                            """,
                            (user_id,))
            team_ids = []
            for team_id, inherit_id in cr.fetchall():
                if team_id not in team_ids:
                    team_ids.append(team_id)
                if inherit_id:
                    if inherit_id not in team_ids:
                        team_ids.append(inherit_id)

                    def _get_all_inherited_team(cr, uid, team_ids, inherit_id):
                        cr.execute("""select tid as interit_id from sale_team_implied_rel
                                    where hid = %s and tid != hid
                                    """,
                                    (inherit_id,))
                        for team_id in cr.fetchall():
                            if team_id[0] not in team_ids:
                                team_ids.append(team_id[0])
                            team_ids = _get_all_inherited_team(cr, uid, team_ids, team_id[0])
                        return team_ids

                    team_ids = _get_all_inherited_team(cr, uid, team_ids, inherit_id)

            teams = self.pool.get('sale.team').browse(cr, uid, team_ids)
            for team in teams:
                team_recs.append({'sale_team_id': team.id, 'commission_rule_id': team.commission_rule_id.id})
        return team_recs

    def onchange_user_id(self, cr, uid, ids, user_id):
        res = {'value': {'sale_team_ids': False}}
        if user_id:
            account_invoice_team = self.pool.get('account.invoice.team')
            if ids:
                account_invoice_team.unlink(cr, uid, account_invoice_team.search(cr, uid, [('invoice_id', 'in', ids)]))
            salespersons = self._get_salesperson_comm(cr, uid, user_id)
            sale_teams = self._get_sale_team_comm(cr, uid, user_id)
            res['value']['sale_team_ids'] = salespersons + sale_teams
        return res

    def create(self, cr, uid, vals, context=None):
        if not vals.get('sale_team_ids', False):
            user_id = vals.get('user_id', False)
            salespersons = self._get_salesperson_comm(cr, uid, user_id)
            sale_teams = self._get_sale_team_comm(cr, uid, user_id)
            records = []
            for record in salespersons + sale_teams:
                records.append([0, False, record])
            vals.update({'sale_team_ids': records})
        return super(account_invoice, self).create(cr, uid, vals, context=context)

    # If invoice state changed, update commission line
    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        if 'state' in vals:
            # Get commission line ids from these invoice ids
            line_ids = self.pool.get('commission.worksheet.line').search(cr, uid, [('invoice_id', 'in', ids)])
            if line_ids:
                self.pool.get('commission.worksheet.line').update_commission_line_status(cr, uid, line_ids, context=context)
        return res

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
