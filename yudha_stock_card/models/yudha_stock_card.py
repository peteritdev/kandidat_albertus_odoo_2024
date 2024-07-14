# -*- coding : utf-8 -*-
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA

from odoo import api, fields, models, _
import time
import logging
_logger = logging.getLogger(__name__)


class yudha_StockCard(models.Model):
    _name = "yudha.stock.card"

    date_start = fields.Date("Date Start", required=True, default=lambda *a: time.strftime("%Y-%m-%d"))
    date_end = fields.Date("Date End", required=True, default=lambda *a: time.strftime("%Y-%m-%d"))
    location_id = fields.Many2one('stock.location', 'Location', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    detail_ids = fields.One2many('yudha.stock.card.line','detail_id',string='Detail Stock Card',auto_join=True)

    def action_process(self):
        for move in self:
            line_obj=self.env['yudha.stock.card.line'].search([('detail_id','=',self.id)])
            line_obj.unlink()
            move.detail_ids = []
            dataku = self.get_report_details()
            move.detail_ids = self.get_report_details()


    def get_report_details(self):
        qty_balance=0
        mysql = """select sum(t1.qty_done) as qty_awal from (select sum(qty_done) as qty_done from stock_move_line where product_id=%s and location_dest_id=%s
                    and cast(date ::timestamp AT time zone 'UTC' as DATE) < %s
                    union
                    select sum(qty_done*-1) as qty_done from stock_move_line where product_id=%s and location_id=%s and cast(date ::timestamp AT time zone 'UTC' as DATE) < %s) t1
                    """
        self.env.cr.execute(mysql, (self.product_id.id, self.location_id.id,self.date_start, self.product_id.id, self.location_id.id,self.date_start,))
        qty_awal = self.env.cr.fetchone()[0] or 0.0

        mysql = """select id,reference,date,picking_id,move_id,product_id,product_uom_id,qty_done,location_id,location_dest_id from stock_move_line where product_id=%s and location_dest_id=%s
            and cast(date ::timestamp AT time zone 'UTC' as DATE) between %s and %s
            union
            select id,reference,date,picking_id,move_id,product_id,product_uom_id,qty_done*-1,location_id,location_dest_id from stock_move_line where product_id=%s and location_id=%s
            and cast(date ::timestamp AT time zone 'UTC' as DATE) between %s and %s
            order by date
            """
        self.env.cr.execute(mysql,(self.product_id.id,self.location_id.id,self.date_start,self.date_end, self.product_id.id,self.location_id.id,self.date_start,self.date_end,))
        result = self.env.cr.dictfetchall()
        hasil = {}
        semua_hasil = self.env['yudha.stock.card.line']
        hasil = {
                'detail_id': self.id,
                'name': 'Beginning Balance',
                'qty_balance': qty_awal
        }
        semua_hasil |= self.env['yudha.stock.card.line'].new(hasil)
        qty_balance = qty_awal

        if result:
            for res in result:
                name = res['reference']
                date = res['date']
                picking_id = res['picking_id']
                move_id = self.env['stock.picking'].browse(res['move_id'])
                product_id = res['product_id']
                product_uom_id = res['product_uom_id']
                qty_done = res['qty_done']
                qty_balance = qty_balance + qty_done
                location_id = res['location_id']
                location_dest_id = res['location_dest_id']
                hasil = {
                         'name':name,
                         'date': date,
                         'picking_id': picking_id,
                         'move_id': move_id,
                         'product_uom_id': product_uom_id,
                         'qty_done': qty_done,
                         'qty_balance': qty_balance,
                         'location_id': location_id,
                         'location_dest_id': location_dest_id
                }
                semua_hasil |= self.env['yudha.stock.card.line'].new(hasil)
        return semua_hasil


class yudha_StockCardLine(models.Model):
    _name 	= "yudha.stock.card.line"

    detail_id = fields.Many2one('yudha.stock.card', string="Detail Id", required=False,store=True,index=True )
    name = fields.Char("Description")
    move_id = fields.Many2one('stock.move', string='Stock Move')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    date = fields.Date("Date")
    qty_done = fields.Float("Qty")
    qty_balance = fields.Float("Balance")
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    location_id = fields.Many2one('stock.location', string='Location Source')
    location_dest_id = fields.Many2one('stock.location',string='Location Target')
