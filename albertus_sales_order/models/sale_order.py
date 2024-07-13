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

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.credit_limit_on_hold:
                msg = "Customer '" + self.partner_id.name + "' is on credit limit hold."
                return {'warning':
                            {'title': 'Credit Limit On Hold', 'message': msg
                             }
                        }
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


