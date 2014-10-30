from openerp.osv import fields, osv


class AdditionalDiscountable(object):

    _line_column = 'order_line'
    _tax_column = 'tax_id'

    def record_currency(self, record):
        """Return currency browse record from a browse record.

        Default implementation is for sale/purchase order.
        """
        return record.pricelist_id.currency_id

    def _amount_all_generic(self, cls, cr, uid, ids, field_name, arg,
                            context=None):
        """Generic overload of the base method to add discount infos

        This is a generic version that needs to be passed the caller class (for
        super).
        For now it can be applied to sale.order, purchase.order and
        account.invoice, using the methods and attrs of AdditionalDiscountable
        """
        cur_obj = self.pool.get('res.currency')
        res = super(cls, self)._amount_all(cr, uid, ids, field_name, arg, context)

        for record in self.browse(cr, uid, ids, context=context):
            # Taxes are applied line by line, we cannot apply a
            # discount on taxes that are not proportional
            if not all(t.type == 'percent'
                       for line in getattr(record, self._line_column)
                       for t in getattr(line, self._tax_column)):
                raise osv.except_osv(_('Discount error'),
                                     _('Unable (for now) to compute a global '
                                       'discount with non percent-type taxes'))
            o_res = res[record.id]

            cur = self.record_currency(record)

            def cur_round(value):
                """Round value according to currency."""
                return cur_obj.round(cr, uid, cur, value)

            # add discount
            amount_untaxed = sum(line.price_subtotal
                                 for line in getattr(record, self._line_column))
            add_disc = record.add_disc
            add_disc_amt = cur_round(amount_untaxed * add_disc / 100)
            o_res['add_disc_amt'] = add_disc_amt
            o_res['amount_net'] = o_res['amount_untaxed'] - add_disc_amt
            o_res['amount_total'] = o_res['amount_net'] + o_res['amount_tax']

        return res

    # Kittiu: Same as the above but only use for invoice to correct the Tax amount
    # Note that we do not correct the Tax amount, as it is already in tax table.
    def _amount_invoice_generic(self, cls, cr, uid, ids, field_name, arg,
                            context=None):
        """Generic overload of the base method to add discount infos

        This is a generic version that needs to be passed the caller class (for
        super).
        For now it can be applied to sale.order, purchase.order and
        account.invoice, using the methods and attrs of AdditionalDiscountable
        """
        cur_obj = self.pool.get('res.currency')
        res = super(cls, self)._amount_all(cr, uid, ids, field_name, arg, context)

        for record in self.browse(cr, uid, ids, context=context):
            # Taxes are applied line by line, we cannot apply a
            # discount on taxes that are not proportional
            if not all(t.type == 'percent'
                       for line in getattr(record, self._line_column)
                       for t in getattr(line, self._tax_column)):
                raise osv.except_osv(_('Discount error'),
                                     _('Unable (for now) to compute a global '
                                       'discount with non percent-type taxes'))
            o_res = res[record.id]

            cur = self.record_currency(record)

            def cur_round(value):
                """Round value according to currency."""
                return cur_obj.round(cr, uid, cur, value)

            # add discount
            amount_untaxed = sum(line.price_subtotal
                                 for line in getattr(record, self._line_column))
            add_disc = record.add_disc
            add_disc_amt = cur_round(amount_untaxed * add_disc / 100)
            o_res['add_disc_amt'] = add_disc_amt
            o_res['amount_net'] = o_res['amount_untaxed'] - add_disc_amt

            # add advance amount, if is_advance = True and advance_percentage > 0
            o_res['amount_advance'] = 0.0
            o_res['amount_deposit'] = 0.0
            o_res['amount_beforetax'] = o_res['amount_net']

            #Modify BY DRB, get order from stock picking
            order = False
            #order = order or record.picking_ids and (record.picking_ids[0].sale_id or record.picking_ids[0].purchase_id)
            order = order or (record.sale_order_ids and record.sale_order_ids[0]) or (record.purchase_order_ids and record.purchase_order_ids[0])
            if order:
#             if record.sale_order_ids or record.purchase_order_ids:
#                 order = record.sale_order_ids and record.sale_order_ids[0] or record.purchase_order_ids[0]
                if not record.is_advance:
                    advance_percentage = order.advance_percentage
                    if advance_percentage:
                        o_res['amount_advance'] = cur_round(o_res['amount_net'] * advance_percentage / 100)
                        o_res['amount_beforetax'] = cur_round(o_res['amount_beforetax']) - cur_round(o_res['amount_advance'])
                if not record.is_deposit:
                    # Deposit will occur only in the last invoice (invoice that make it 100%)
                    #this_invoice_rate = order.amount_net and cur_round(o_res['amount_beforetax']) * 100 / order.amount_net or 0.0
                    #amount_deposit = order.invoiced_rate + this_invoice_rate >= 100.0 and order.amount_deposit or False
                    amount_deposit = order.invoiced_rate >= 100.0 and order.amount_deposit or False
                    if amount_deposit:
                        o_res['amount_deposit'] = amount_deposit
                        o_res['amount_beforetax'] = o_res['amount_beforetax'] - o_res['amount_deposit']

            # add retention amount, if is_retention = True and retention_percentage > 0
            o_res['amount_beforeretention'] = o_res['amount_beforetax'] + o_res['amount_tax']
            o_res['amount_retention'] = 0.0
            if record.sale_order_ids:
                order = record.sale_order_ids and record.sale_order_ids[0]
                if record.is_retention:
                    retention_percentage = order.retention_percentage
                    if retention_percentage:
                        o_res['amount_retention'] = (o_res['amount_net'] * retention_percentage / 100)

            o_res['amount_total'] = o_res['amount_beforeretention'] - o_res['amount_retention']

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
