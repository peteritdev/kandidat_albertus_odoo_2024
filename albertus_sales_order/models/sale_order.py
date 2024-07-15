# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################


from odoo import api, fields, models, _, Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    devisi_id = fields.Many2one('res.devisi', string='Divisi', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True, readonly=False, change_default=True, index=True,
        tracking=1,
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id)),('devisi_id','=',devisi_id)]")

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, precompute=True, check_company=True, required=True,  # Unrequired company
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('devisi_id','=',devisi_id)]",
        help="If you change the pricelist, only newly added lines will be affected.")
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,
        tracking=2,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ))
    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string="Delivery Address",
        store=True, readonly=False, required=True, precompute=True,
        domain="['|',('id','=',partner_id),('id','child_of', [partner_id])]")
    pickup_methode = fields.Selection([('delivery','Delivery'),
                                       ('take_in_plant','Take In Plant')],string='Pickup Methode',default='delivery',ondelete='cascade')
    validity_date = fields.Date(
        string="Expiration",
        compute=False,
        store=True, readonly=False, copy=False, precompute=True,)

    is_overdue = fields.Boolean('Is Overdue', default=False)

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     if self.partner_id:
    #         if self.partner_id.credit_limit_on_hold:
    #             msg = "Customer '" + self.partner_id.name + "' is on credit limit hold."
    #             return {'warning':
    #                         {'title': 'Credit Limit On Hold', 'message': msg
    #                          }
    #                     }
    @api.onchange('pricelist_id')
    def _compute_unit_price_with_pricelist(self):
        for order in self:
            for line in order.order_line:
                if line.product_id and order.pricelist_id:
                    pricelist_id = order.pricelist_id
                    new_list_price = pricelist_id._get_product_price(line.product_id, line.product_uom_qty)
                    if new_list_price != 0.0:
                        final_price = new_list_price
                    else:
                        final_price = line.product_id.with_company(order.company_id).lst_price
                    line.write({
                        'price_unit': final_price,
                        'discount': 0.0
                    })


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if res:
            res.update({
                'pricelist_id': self.pricelist_id.id,
                'currency_id': self.pricelist_id.currency_id.id
            })
        return res

    @api.onchange('carrier_id')
    def hitung_potongan(self):
        for alldata in self:
            if not alldata.carrier_id:
                return
            if not alldata.order_line:
                return
            for alines in alldata.order_line:
                totprice = alines.price_subtotal
                alines.price_subtotal = totprice - 10000

    @api.onchange('product_uom_qty','price_unit')
    def hitung_potongan_harga(self):
        for alldata in self:
            alldata.price_subtotal = (alldata.product_uom_qty *  alldata.price_unit) -1000 - alldata.discount

    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()
        partner_id = self.partner_id
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
        partner_ids = [partner_id.id]
        for partner in partner_id.child_ids:
            partner_ids.append(partner.id)

        if partner_id.check_credit and sum([x.days for x in self.payment_term_id.line_ids]) > 0:
            domain = [
                ('order_id.partner_id', 'in', partner_ids),
                ('order_id.state', 'in', ['sale','done'])]
            order_lines = self.env['sale.order.line'].search(domain)

            order = []
            to_invoice_amount = 0.0
            for line in order_lines:
                not_invoiced = line.product_uom_qty - line.qty_invoiced
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(
                    price, line.order_id.currency_id,
                    not_invoiced,
                    product=line.product_id, partner=line.order_id.partner_id)
                if line.order_id.id not in order:
                    if line.order_id.invoice_ids:
                        for inv in line.order_id.invoice_ids:
                            if inv.state == 'draft':
                                order.append(line.order_id.id)
                                break
                    else:
                        order.append(line.order_id.id)

                to_invoice_amount += taxes['total_included']

            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '!=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                to_invoice_amount += taxes['total_included']

            # We sum from all the invoices lines that are in draft and not linked
            # to a sale order
            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            draft_invoice_lines_amount = 0.0
            invoice = []
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                draft_invoice_lines_amount += taxes['total_included']
                if line.move_id.id not in invoice:
                    invoice.append(line.move_id.id)

            draft_invoice_lines_amount = "{:.2f}".format(draft_invoice_lines_amount)
            to_invoice_amount = "{:.2f}".format(to_invoice_amount)
            draft_invoice_lines_amount = float(draft_invoice_lines_amount)
            to_invoice_amount = float(to_invoice_amount)
            available_credit = partner_id.credit_limit - partner_id.credit - to_invoice_amount - draft_invoice_lines_amount
            if available_credit ==0.0:
                msg = "Customer '" + partner_id.name + "' Credit Limit Is Exceeded!."
                return {'warning':
                            {'title': 'Credit Limit Is Exceed', 'message': msg
                             }
                        }

            partner_id.write({'credit_used': partner_id.credit + to_invoice_amount + draft_invoice_lines_amount,
                              'credit_balance': available_credit})
            if self.amount_total > available_credit:
                imd = self.env['ir.model.data']
                exceeded_amount = (
                                              to_invoice_amount + draft_invoice_lines_amount + partner_id.credit + self.amount_total) - partner_id.credit_limit
                exceeded_amount = "{:.2f}".format(exceeded_amount)
                exceeded_amount = float(exceeded_amount)
                vals_wiz = {
                    'partner_id': partner_id.id,
                    'sale_orders': str(len(order)) + ' Sale Order Worth : ' + str(to_invoice_amount),
                    'invoices': str(len(invoice)) + ' Draft Invoice worth : ' + str(draft_invoice_lines_amount),
                    'current_sale': self.amount_total or 0.0,
                    'exceeded_amount': exceeded_amount,
                    'credit': partner_id.credit,
                    'credit_limit_on_hold': partner_id.credit_limit_on_hold,
                }
                # wiz_id = self.env['customer.limit.wizard'].create(vals_wiz)
                # action = imd.xmlid_to_object('dev_customer_credit_limit.action_customer_limit_wizard')
                # form_view_id = imd.xmlid_to_res_id('dev_customer_credit_limit.view_customer_limit_wizard_form')
                # return {
                #     'name': action.name,
                #     'help': action.help,
                #     'type': action.type,
                #     'views': [(form_view_id, 'form')],
                #     'view_id': form_view_id,
                #     'target': action.target,
                #     'context': action.context,
                #     'res_model': action.res_model,
                #     'res_id': wiz_id.id,
                # }
            else:
                self.action_confirm()
        elif partner_id.check_credit and self.payment_term_id.line_ids.days <= 0:
            self.action_confirm()
        elif not partner_id.check_credit:
            self.action_confirm()

        return res


