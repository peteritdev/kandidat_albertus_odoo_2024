# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################

from odoo import api, fields, models, _, Command

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    devisi_id = fields.Many2one('res.devisi',string='Divisi')