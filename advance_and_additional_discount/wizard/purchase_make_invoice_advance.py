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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class purchase_advance_payment_inv(osv.osv_memory):
    _name = "purchase.advance.payment.inv"
    _description = "Purchase Advance Payment Invoice"

    _columns = {
        'advance_payment_method': fields.selection(
            [('percentage', 'Percentage'), ('fixed', 'Fixed price (deposit)')],
            'What do you want to invoice?', required=False,
            help="""Use Percentage to invoice a percentage of the total amount.
                Use Fixed Price to invoice a specific amount in advance."""),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'),
            help="The amount to be invoiced in advance."),
    }

    _defaults = {
        'amount': 0.0,
    }

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        purchase_obj = self.pool.get('purchase.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        wizard = self.browse(cr, uid, ids[0], context)
        purchase_ids = context.get('active_ids', [])
        advance_type = context.get('advance_type', False)
        advance_label = advance_type == 'deposit' and 'Deposit' or 'Advance'

        result = []
        for purchase in purchase_obj.browse(cr, uid, purchase_ids, context=context):
            res = {}
            # Case Advance
            if advance_type == 'advance':
                prop = ir_property_obj.get(cr, uid,
                            'property_account_advance_supplier', 'res.partner', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, purchase.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                            _('There is no advance supplier account defined as global property.'))
                res['account_id'] = account_id
            # Case Deposit
            if advance_type == 'deposit':
                prop = ir_property_obj.get(cr, uid,
                            'property_account_deposit_supplier', 'res.partner', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, purchase.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                            _('There is no deposit customer account defined as global property.'))
                res['account_id'] = account_id

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise osv.except_osv(_('Incorrect Data'),
                    _('The value of %s Amount must be positive.') % (advance_label))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = purchase.amount_net * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = _("%s of %s %%") % (advance_label, wizard.amount)

            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    #TODO: should find a way to call formatLang() from rml_parse
                    symbol = purchase.pricelist_id.currency_id.symbol
                    if purchase.pricelist_id.currency_id.position == 'after':
                        res['name'] = _("%s of %s %s") % (advance_label, inv_amount, symbol)
                    else:
                        res['name'] = _("%s of %s %s") % (advance_label, symbol, inv_amount)

            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': purchase.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': 1.0,
                'discount': False,
                'uos_id': False,
                'product_id': False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in purchase.order_line[0].taxes_id])],
                'account_analytic_id': False,
                'is_advance': advance_type == 'advance' and True or False,
                'is_deposit': advance_type == 'deposit' and True or False
            }
            inv_values = {
                'name': purchase.partner_ref or purchase.name,
                'origin': purchase.name,
                'type': 'in_invoice',
                'reference': False,
                'account_id': purchase.partner_id.property_account_payable.id,
                'partner_id': purchase.partner_id.id,
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': purchase.pricelist_id.currency_id.id,
                'comment': '',
                'payment_term': purchase.payment_term_id.id,
                'fiscal_position': purchase.fiscal_position.id or purchase.partner_id.property_account_position.id,
                'is_advance': advance_type == 'advance' and True or False,
                'is_deposit': advance_type == 'deposit' and True or False
            }
            result.append((purchase.id, inv_values))
        return result

    def _create_invoices(self, cr, uid, inv_values, purchase_id, context=None):
        context['type'] = 'in_invoice'
        inv_obj = self.pool.get('account.invoice')
        purchase_obj = self.pool.get('purchase.order')
        inv_id = inv_obj.create(cr, uid, inv_values, context=context)
        inv_obj.button_reset_taxes(cr, uid, [inv_id], context=context)
        # add the invoice to the purchase order's invoices
        purchase_obj.write(cr, uid, [purchase_id], {'invoice_ids': [(4, inv_id)]}, context=context)
        return inv_id

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active purchase orders """
        purhcase_obj = self.pool.get('purchase.order')
        wizard = self.browse(cr, uid, ids[0], context)
        purchase_id = context.get('active_id', False)

        inv_ids = []
        for purhcase_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, purhcase_id, context=context))

        # Update advance and deposit
        if wizard.advance_payment_method in ['percentage', 'fixed']:
            advance_percent = 0.0
            advance_amount = 0.0
            amount_deposit = 0.0
            if purchase_id:
                purchase = purhcase_obj.browse(cr, uid, purchase_id)
                advance_type = context.get('advance_type', False)
                if advance_type == 'advance':
                    # calculate the percentage of advancement
                    if wizard.advance_payment_method == 'percentage':
                        advance_percent = wizard.amount
                        advance_amount = (wizard.amount / 100) * purchase.amount_net
                    elif wizard.advance_payment_method == 'fixed':
                        advance_amount = wizard.amount
                        advance_percent = (wizard.amount / purchase.amount_net) * 100
                if advance_type == 'deposit':
                    # calculate the amount of deposit
                    if wizard.advance_payment_method == 'percentage':
                        amount_deposit = (wizard.amount / 100) * purchase.amount_net
                    elif wizard.advance_payment_method == 'fixed':
                        amount_deposit = wizard.amount
                if advance_amount > purchase.amount_net or amount_deposit > purchase.amount_net:
                    raise osv.except_osv(_('Amount Error!'),
                            _('Amount > Purchase Order amount!'))
                # write back to sale_order
                purhcase_obj.write(cr, uid, [purchase_id], {'advance_percentage': advance_percent})
                purhcase_obj.write(cr, uid, [purchase_id], {'amount_deposit': amount_deposit})

        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def open_invoices(self, cr, uid, ids, invoice_ids, context=None):
        """ open a view on one of the given invoice_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Advance Invoice'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': invoice_ids[0],
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': "{'type': 'in_invoice'}",
            'type': 'ir.actions.act_window',
        }

purchase_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
