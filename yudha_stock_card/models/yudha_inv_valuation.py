# -*- coding : utf-8 -*-
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA

from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError, Warning

class yudha_inv_valuation_main(models.TransientModel):
    _name = "yudha_inventory_valuation.report"
    _description = 'Yudha Inventry Valuation VaReport'

    date_start = fields.Date(string="Start Date", required=True, default=lambda *a: time.strftime("%Y-%m-%d"))
    date_end = fields.Date(string="End Date", required=True, default=lambda *a: time.strftime("%Y-%m-%d"))
    wh_id = fields.Many2many(comodel_name='stock.warehouse',string='Warehouse',required=True,store=True)
    lok_id  = fields.Many2many(comodel_name='stock.location',string='Location', required=True)
    grp_by = fields.Boolean('Group By Company')
    flter_by  = fields.Selection([('product', 'Product'),
                                  ('category', 'Category')],dafault='product',string='Filter By')



    def rep_pdf(self):
        return self.env.ref('yudha_stock_card.inv_valuation_report_pdf').report_action(self)

