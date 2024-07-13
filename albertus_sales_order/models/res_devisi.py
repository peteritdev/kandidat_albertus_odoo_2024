# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################

from odoo import fields, models, api, tools, _
from odoo.osv import expression

class ResDevisi(models.Model):
    _name = "res.devisi"
    _description = "Devisi"
    _rec_name = 'name'


    name = fields.Char(required=True)
    pricelist_id = fields.Many2one(
            comodel_name='product.pricelist',
            string="Pricelist",
            tracking=1,
            help="If you change the pricelist, only newly added lines will be affected.")
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        tracking=2,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ))

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        for alldata in self:
            if not alldata.pricelist_id:
                return
            alldata.pricelist_id.write({'devisi_id': alldata.id})