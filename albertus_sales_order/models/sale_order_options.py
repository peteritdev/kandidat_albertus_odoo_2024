# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################


from odoo import api, fields, models, _, Command


class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    devisi_id = fields.Many2one('res.devisi', related='order_id.devisi_id',string='Divisi', required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        domain="[('devisi_id','=',devisi_id),('sale_ok', '=', True)]")
