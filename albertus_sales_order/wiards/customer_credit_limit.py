# -*- coding : utf-8 -*-
#########################################################################################
# Author    => Albertus Restiyanto Pramayudha                                           #
# email     => xabre0010@gmail.com                                                      #
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/     #
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA                 #
#########################################################################################


from odoo import api, fields, models


class customer_limit_wizard(models.TransientModel):
    _name = "customer.limit.wizard"
    _description = 'Customer Credit Limit Wizard'

    def set_credit_limit_state(self):
        order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_id.state = 'credit_limit'
        order_id.exceeded_amount = self.exceeded_amount
        # order_id.send_mail_approve_credit_limit()
        partner_id = self.partner_id
        if partner_id.parent_id:
            partner_id = partner_id.parent_id
        partner_id.credit_limit_on_hold = self.credit_limit_on_hold
        return True

    current_sale = fields.Float('Current Quotation')
    exceeded_amount = fields.Float('Exceeded Amount')
    credit = fields.Float('Total Receivable')
    partner_id = fields.Many2one('res.partner', string="Customer")
    credit_limit = fields.Float(related='partner_id.credit_limit', string="Credit Limit")
    sale_orders = fields.Char("Sale Orders")
    invoices = fields.Char("Invoices")
    credit_limit_on_hold = fields.Boolean('Credit Limit on Hold')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: