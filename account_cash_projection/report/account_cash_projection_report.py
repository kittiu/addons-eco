# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Ecosoft (<http://www.ecosoft.co.th>)
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

import time
from openerp.report import report_sxw
from account.report.common_report_header import common_report_header

class cash_projection_report(report_sxw.rml_parse, common_report_header):
    
    _name = 'account.cash_projection_balance'

    def __init__(self, cr, uid, name, context):
        super(cash_projection_report, self).__init__(cr, uid, name, context=context)
        self.total_account = []
        self.total_account_account = []        
        self.localcontext.update({
            'time': time,
#            'get_lines_with_out_partner': self._get_lines_with_out_partner,
#            'get_lines': self._get_lines,
#            'get_total': self._get_total,
#            'get_direction': self._get_direction,
#            'get_for_period': self._get_for_period,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
#            'get_partners':self._get_partners,
            'get_account': self._get_account,
            'get_fiscalyear': self._get_fiscalyear,
            'get_target_move': self._get_target_move,
        })

    def set_context(self, objects, data, ids, report_type=None):
        obj_move = self.pool.get('account.move.line')
        ctx = data['form'].get('used_context', {})
        ctx.update({'fiscalyear': False, 'all_fiscalyear': True})
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=ctx)
        
        self.target_move = data['form'].get('target_move', 'all')
        self.date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        self.no_columns = data['form'].get('no_columns', 30)

        self.ACCOUNT_TYPE = ['payable','receivable']
        
        return super(cash_projection_report, self).set_context(objects, data, ids, report_type=report_type)

# ====================================================Cash projection-Operating Activites Start logic=========================================================================
    def _get_lines_accounts_inflow(self, form, account_type=None,account_ids=False): # new method of cash projection
        #account_type this variable will recieve value in list only
        self.ACCOUNT_TYPE = account_type #account_type=['receivable'] or ['payable']
#         res = []
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        self.cr.execute('SELECT DISTINCT account_account.id AS id,\
                    account_account.name AS name \
                FROM res_partner,account_move_line AS l, account_account, account_move am\
                WHERE (l.account_id=account_account.id) \
                    AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s)\
                    AND account_account.active\
                    AND ((reconcile_id IS NULL)\
                       OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND (l.partner_id=res_partner.id)\
                    AND (l.date <= %s)\
                    AND ' + self.query + ' \
                    AND (account_account.id in %s) \
                ORDER BY account_account.name', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, self.date_from,tuple(account_ids),))
        accounts = self.cr.dictfetchall()
        
        for i in range(32):
            self.total_account_account.append(0)

        #
        # Build a string like (1,2,3) for easy use in SQL query
        if account_ids:
            pass
        else:
            account_ids = [x['id'] for x in accounts]
        if not account_ids:
            return []
        # This dictionary will store the debit-credit for all partners, using partner_id as key.

        totals_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(l.debit-l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND ' + self.query + '\
                    AND account_account.active\
                    AND (l.date <= %s)\
                    GROUP BY l.account_id ', (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids), self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            totals_accounts[i[0]] = i[1]
            
        future_past_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(l.debit-l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id=account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s)\
                    AND (COALESCE(l.date_maturity, l.date) < %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND '+ self.query + '\
                    AND account_account.active\
                AND (l.date <= %s)\
                    GROUP BY l.account_id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(account_ids),self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            future_past_accounts[i[0]] = i[1]

        history_accounts = []
        for i in range(self.no_columns):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids),self.date_from,)
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (self.date_from,)
            self.cr.execute('''SELECT l.account_id, SUM(l.debit-l.credit)
                    FROM account_move_line AS l, account_account, account_move am 
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id)
                        AND (am.state IN %s)
                        AND (account_account.type IN %s)
                        AND (l.account_id IN %s)
                        AND ((l.reconcile_id IS NULL)
                          OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    GROUP BY l.account_id''', args_list)
            t = self.cr.fetchall()
            d = {}
            for i in t:
                d[i[0]] = i[1]
            history_accounts.append(d)

        res_accounts = []
        for account in accounts:
            values_accounts = {}

            # Query here is replaced by one query which gets the all the partners their 'before' value
            before = False
            if future_past_accounts.has_key(account['id']):
                before = [ future_past_accounts[account['id']] ]
            self.total_account_account[6] = self.total_account_account[6] + (before and before[0] or 0.0)
            values_accounts['direction'] = before and before[0] or 0.0

            for i in range(self.no_columns):
                during = False
                if history_accounts[i].has_key(account['id']):
                    during = [ history_accounts[i][account['id']] ]
                # Ajout du compteur
                self.total_account_account[(i)] = self.total_account_account[(i)] + (during and during[0] or 0)
                values_accounts[str(i)] = during and during[0] or 0.0
            total = False
            if totals_accounts.has_key( account['id'] ):
                total = [ totals_accounts[account['id']] ]
            values_accounts['total'] = total and total[0] or 0.0
            ## Add for total
            self.total_account_account[(i+1)] = self.total_account_account[(i+1)] + (total and total[0] or 0.0)
            values_accounts['name'] = account['name']
            res_accounts.append(values_accounts)

        total = 0.0
        totals = {}
        for r in res_accounts:
            total += float(r['total'] or 0.0)
            for i in range(self.no_columns)+['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res_accounts


# ====================================================Cash projection-Finance/investing Inflow Activites Start logic=========================================================================
    def _get_lines_accounts_inflow_finance(self, form, account_type=None,account_ids=False): # new method of cash projection
        #account_type this variable will recieve value in list only
        self.ACCOUNT_TYPE = account_type #account_type=['receivable'] or ['payable']
#         res = []
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        self.cr.execute('SELECT DISTINCT account_account.id AS id,\
                    account_account.name AS name \
                FROM res_partner,account_move_line AS l, account_account, account_move am\
                WHERE (l.account_id=account_account.id) \
                    AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND account_account.active\
                    AND ((reconcile_id IS NULL)\
                       OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND (l.partner_id=res_partner.id)\
                    AND (l.date <= %s)\
                    AND ' + self.query + ' \
                    AND (account_account.id in %s) \
                ORDER BY account_account.name', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, self.date_from,tuple(account_ids),))
        accounts = self.cr.dictfetchall()
        
        for i in range(32):
            self.total_account_account.append(0)

        #
        # Build a string like (1,2,3) for easy use in SQL query
        if account_ids:
            pass
        else:
            account_ids = [x['id'] for x in accounts]
        if not account_ids:
            return []
        # This dictionary will store the debit-credit for all partners, using partner_id as key.

        totals_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND ' + self.query + '\
                    AND account_account.active\
                    AND (l.date <= %s)\
                    GROUP BY l.account_id ', (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids), self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            totals_accounts[i[0]] = i[1]
            
        future_past_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id=account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND (COALESCE(l.date_maturity, l.date) < %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND '+ self.query + '\
                    AND account_account.active\
                AND (l.date <= %s)\
                    GROUP BY l.account_id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(account_ids),self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            future_past_accounts[i[0]] = i[1]

        history_accounts = []
        for i in range(self.no_columns):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids),self.date_from,)
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (self.date_from,)
            self.cr.execute('''SELECT l.account_id, SUM(l.credit)
                    FROM account_move_line AS l, account_account, account_move am 
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id)
                        AND (am.state IN %s)
                        AND (account_account.type NOT IN %s)
                        AND (l.account_id IN %s)
                        AND ((l.reconcile_id IS NULL)
                          OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    GROUP BY l.account_id''', args_list)
            t = self.cr.fetchall()
            d = {}
            for i in t:
                d[i[0]] = i[1]
            history_accounts.append(d)

        res_accounts = []
        for account in accounts:
            values_accounts = {}
            # Query here is replaced by one query which gets the all the partners their 'before' value
            before = False
            if future_past_accounts.has_key(account['id']):
                before = [ future_past_accounts[account['id']] ]
            self.total_account_account[6] = self.total_account_account[6] + (before and before[0] or 0.0)
            values_accounts['direction'] = before and before[0] or 0.0

            for i in range(self.no_columns):
                during = False
                if history_accounts[i].has_key(account['id']):
                    during = [ history_accounts[i][account['id']] ]
                # Ajout du compteur
                self.total_account_account[(i)] = self.total_account_account[(i)] + (during and during[0] or 0)
                values_accounts[str(i)] = during and during[0] or 0.0
            total = False
            if totals_accounts.has_key( account['id'] ):
                total = [ totals_accounts[account['id']] ]
            values_accounts['total'] = total and total[0] or 0.0
            ## Add for total
            self.total_account_account[(i+1)] = self.total_account_account[(i+1)] + (total and total[0] or 0.0)
            values_accounts['name'] = account['name']
            res_accounts.append(values_accounts)
        
        total = 0.0
        totals = {}
        for r in res_accounts:
            total += float(r['total'] or 0.0)
            for i in range(self.no_columns)+['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res_accounts



# ====================================================Cash projection-Finance/investing outflow Activites Start logic=========================================================================
    def _get_lines_accounts_outflow_finance(self, form, account_type=None,account_ids=False): # new method of cash projection
        #account_type this variable will recieve value in list only
        self.ACCOUNT_TYPE = account_type #account_type=['receivable'] or ['payable']
#         res = []
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        self.cr.execute('SELECT DISTINCT account_account.id AS id,\
                    account_account.name AS name \
                FROM res_partner,account_move_line AS l, account_account, account_move am\
                WHERE (l.account_id=account_account.id) \
                    AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND account_account.active\
                    AND ((reconcile_id IS NULL)\
                       OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND (l.partner_id=res_partner.id)\
                    AND (l.date <= %s)\
                    AND ' + self.query + ' \
                    AND (account_account.id in %s) \
                ORDER BY account_account.name', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, self.date_from,tuple(account_ids),))
        accounts = self.cr.dictfetchall()
        
        for i in range(32):
            self.total_account_account.append(0)

        #
        # Build a string like (1,2,3) for easy use in SQL query
        if account_ids:
            pass
        else:
            account_ids = [x['id'] for x in accounts]
        if not account_ids:
            return []
        # This dictionary will store the debit-credit for all partners, using partner_id as key.

        totals_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(0-l.debit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND ' + self.query + '\
                    AND account_account.active\
                    AND (l.date <= %s)\
                    GROUP BY l.account_id ', (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids), self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            totals_accounts[i[0]] = i[1]
            
        future_past_accounts = {}
        self.cr.execute('SELECT l.account_id, SUM(0-l.debit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id=account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type NOT IN %s)\
                    AND (COALESCE(l.date_maturity, l.date) < %s)\
                    AND (l.account_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND '+ self.query + '\
                    AND account_account.active\
                AND (l.date <= %s)\
                    GROUP BY l.account_id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(account_ids),self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            future_past_accounts[i[0]] = i[1]

        history_accounts = []
        for i in range(self.no_columns):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(account_ids),self.date_from,)
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (self.date_from,)
            self.cr.execute('''SELECT l.account_id, SUM(0-l.debit)
                    FROM account_move_line AS l, account_account, account_move am 
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id)
                        AND (am.state IN %s)
                        AND (account_account.type NOT IN %s)
                        AND (l.account_id IN %s)
                        AND ((l.reconcile_id IS NULL)
                          OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    GROUP BY l.account_id''', args_list)
            t = self.cr.fetchall()
            d = {}
            for i in t:
                d[i[0]] = i[1]
            history_accounts.append(d)

        res_accounts = []
        for account in accounts:
            values_accounts = {}

            # Query here is replaced by one query which gets the all the partners their 'before' value
            before = False
            if future_past_accounts.has_key(account['id']):
                before = [ future_past_accounts[account['id']] ]
            self.total_account_account[6] = self.total_account_account[6] + (before and before[0] or 0.0)
            values_accounts['direction'] = before and before[0] or 0.0

            for i in range(self.no_columns):
                during = False
                if history_accounts[i].has_key(account['id']):
                    during = [ history_accounts[i][account['id']] ]
                # Ajout du compteur
                self.total_account_account[(i)] = self.total_account_account[(i)] + (during and during[0] or 0)
                values_accounts[str(i)] = during and during[0] or 0.0
            total = False
            if totals_accounts.has_key( account['id'] ):
                total = [ totals_accounts[account['id']] ]
            values_accounts['total'] = total and total[0] or 0.0
            ## Add for total
            self.total_account_account[(i+1)] = self.total_account_account[(i+1)] + (total and total[0] or 0.0)
            values_accounts['name'] = account['name']
            res_accounts.append(values_accounts)

        total = 0.0
        totals = {}
        for r in res_accounts:
            total += float(r['total'] or 0.0)
            for i in range(self.no_columns)+['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res_accounts


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
