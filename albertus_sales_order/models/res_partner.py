# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################

from odoo import api, fields, models, _, Command


class ResPartner(models.Model):
    _inherit = 'res.partner'

    devisi_id = fields.Many2many('res.devisi','res_partner_rel',string='Divisi',required=True)
    check_credit = fields.Boolean('Check Credit')
    credit_limit_on_hold  = fields.Boolean('Credit limit on hold')
    credit_limit = fields.Float('Credit Limit')
    credit_used = fields.Float('Credit Used',readonly=True)
    credit_balance = fields.Float('Credit Balance',compute='_check_balance',store=True,readonly=True)
    user_id = fields.Many2one('res.users',string='Sales Person')


    @api.depends('credit_used','credit_limit')
    def _check_balance(self):
        for alldata in self:
            alldata.credit_balance = alldata.credit_limit - alldata.credit_used