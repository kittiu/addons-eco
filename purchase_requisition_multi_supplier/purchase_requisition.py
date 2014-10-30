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


class purchase_requisition_line(osv.osv):

    _inherit = "purchase.requisition.line"

    def _get_status(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 'draft')
        for line in self.browse(cr, uid, ids, context=context):
            for po in line.po_line_ids:
                if po.state == 'draft' and res[line.id] != 'done':
                    res[line.id] = 'in_purchase'
                else:
                    if po.state == 'confirmed' or po.state == 'done':
                        res[line.id] = 'done'
                    else:
                        if po.state == 'cancel' and res[line.id] != 'done':
                                res[line.id] = 'cancel'
        return res

    _columns = {
        'partner_ids': fields.many2many('res.partner', 'pr_rel_partner',
                                        'pr_line_id',
                                        'partner_id', 'Suppliers', ),
        'selected_flag': fields.boolean("Select"),
        'po_line_ids': fields.many2many('purchase.order.line', 'pr_rel_po',
                                        'pr_id', 'po_id',
                                        'Purchase Line Orders',
                                        ondelete='cascade'),
        'state': fields.function(_get_status, string='Status', readonly=True,
                                 type='selection',
                                 selection=[('draft', 'New'),
                                            ('in_purchase', 'In Progress'),
                                            ('done', 'Purchase Done'),
                                            ('cancel', 'Cancelled')]),
        'name': fields.text('Description', required=True),
    }
    _default = {
        'selected_flag': True,
        'po_line_ids': False,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'po_line_ids': False,
        })
        return super(purchase_requisition_line, self).copy(cr, uid, id, default=default, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        res = super(purchase_requisition_line,
                    self).write(cr, uid, ids, vals, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        # Remove po_line_ids if duplicate data
        if context.get('copying', False):
            vals.update({'po_line_ids': False})
        res_id = super(purchase_requisition_line, self).create(cr, uid, vals, context=context)
        return res_id

    def selected_flag_onchange(self, cr, uid, ids, selected_flag, context=None):
        res = {'value': {'all_selected': True}}
        if not selected_flag:
            res['value'].update({'all_selected': False})
        return res

    def default_get(self, cr, uid, fields, context=None):
        return super(purchase_requisition_line, self).default_get(cr, uid, fields, context=context)

    def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
        res = super(purchase_requisition_line, self).onchange_product_id(cr, uid, ids, product_id, product_uom_id, context=context)
        product_product = self.pool.get('product.product')
        product = product_product.browse(cr, uid, product_id, context=context)
        dummy, name = product_product.name_get(cr, uid, product_id, context=context)[0]
        if product.description_purchase:
            name += '\n' + product.description_purchase
        elif product.description:
            name += '\n' + product.description
        res['value'].update({'name': name})
        return res

purchase_requisition_line()


class purchase_requisition(osv.osv):

    _inherit = 'purchase.requisition'

    def _get_progress_rate(self, cr, uid, ids, field, arg, context=None):
        res = dict.fromkeys(ids, False)
        for req in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                select (sum(po_qty) / sum(pr_qty) * 100) percent from
                (select pr.product_id, pr.product_qty pr_qty,
                coalesce(case when po.product_qty > pr.product_qty then pr.product_qty else po.product_qty end, 0) po_qty from
                (select prl.id pr_line_id, prl.product_id, prl.product_qty from purchase_requisition pr
                join purchase_requisition_line prl on prl.requisition_id = pr.id
                where pr.id = %s) pr
                left outer join
                (select pol.id po_line_id, pol.product_id, pol.product_qty
                from purchase_order_line pol join purchase_order po on po.id = pol.order_id
                where po.state not in ('cancel') and pol.id in
                (select po_id from pr_rel_po a join purchase_requisition_line b on a.pr_id = b.id
                where b.requisition_id = %s)) po
                on pr.product_id = po.product_id) pr_po
            """, (req.id, req.id))
            res[req.id] = cr.fetchone()[0] or 0.0
        return res

    _columns = {
        'all_selected': fields.boolean("All Select(s)"),
        'progress_rate': fields.function(_get_progress_rate, string='Progress Rate', type='float'),
    }
    _default = {
        'all_selected': True,
    }

    def all_selected_onchange(self, cr, uid, ids, all_selected, line_ids, context=None):
        res = {'value': {'line_ids': False}}
        for index in range(len(line_ids)):
            if line_ids[index][0] in (0, 1, 4):
                if line_ids[index][2]:
                    line_ids[index][2].update({'selected_flag': all_selected})
                else:
                    if line_ids[index][0] == 4:
                        line_ids[index][0] = 1
                    line_ids[index][2] = {'selected_flag': all_selected}
        res['value']['line_ids'] = line_ids
        return res

    def update_done(self, cr, uid, ids, context=None):
        pr_recs = self.browse(cr, uid, ids, context=context)
        prs_done = []
        for rec in pr_recs:
            is_done = True
            for line in rec.line_ids:
                is_done = is_done and line.state in ('done', 'cancel')
            if is_done:
                prs_done.append(rec.id)
        self.tender_done(cr, uid, prs_done, context=None)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        context.update({'copying': True})
        return super(purchase_requisition, self).copy(cr, uid, id, default=default, context=context)

    def action_createPO(self, cr, uid, ids, context=None):
        selected = False
        for pr in self.browse(cr, uid, ids, context):
            for line_id in pr.line_ids:
                if line_id.selected_flag:
                    selected = True
        if not selected:
            raise osv.except_osv(_('Warning!'), _('Please select the PR Line(s) at least one line'))
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'purchase_requisition', 'action_purchase_requisition_partner')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        return result

purchase_requisition()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
