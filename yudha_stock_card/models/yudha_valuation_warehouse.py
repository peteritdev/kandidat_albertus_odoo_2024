# -*- coding : utf-8 -*-
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class yudha_valuation_warehouse(models.Model):
    _name='valuation.warehouse'

    @api.depends('val_warehouse_ids.qty')
    def _total_all(self):
        Totbrg = 0
        for order in self:
            for line in order.val_warehouse_ids:
                Totbrg += line.qty
            order.update({
                'total_item': Totbrg,
            })

    tgl = fields.Date("Inventory Date")
    stock_location =fields.Many2one('stock.location',string='Warehouse')
    total_item = fields.Float('Total Item', compute='_total_all', track_visibility='onchange')
    val_warehouse_ids = fields.One2many(comodel_name="valuation.warehouse.details", inverse_name="val_warehouse_id", string="Product VaLuation Group", required=False )

    @api.onchange('tgl','stock_location')
    def onchange_tampil_val(self):
        if not self.tgl:
            return
        if not self.stock_location:
            return
        self.val_warehouse_ids = self.Tampil_Barang(self.tgl,self.stock_location.id)

    def Tampil_Barang(self,tglin,kb):
        if not tglin:
            return
        if not kb:
            return
        StockMove = self.env['stock.move']
        hasil = {}
        semua_hasil = []
        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        pquery = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                     FROM account_move_line AS aml left join product_product a on a.id=aml.product_id left join product_template b on a.product_tmpl_id=b.id inner join stock_move sm on aml.move_id=sm.id
                     WHERE aml.product_id IS NOT NULL AND b.type = 'product' AND aml.company_id=%s AND aml.date <= %s and sm.location_dest_id=%s
                 GROUP BY aml.product_id, aml.account_id """
        self.env.cr.execute(pquery, (self.env.user.company_id.id,tglin, kb))
        press = self.env.cr.fetchall()
        for row in press:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        # query = """SELECT a.id,b.uom_id from product_product a inner join product_template b on a.product_tmpl_id=b.id GROUP BY a.id,b.uom_id,b.x_kelompok_barang ORDER BY b.name asc"""
        query = "SELECT aml.product_id, aml.account_id, aml.date, sum(aml.debit) - sum(aml.credit), sum(quantity),array_agg(aml.id) from account_move_line AS aml " \
                "left join product_product a on a.id=aml.product_id " \
                "left join product_template b on a.product_tmpl_id=b.id " \
                "left join stock_move sm on aml.move_id=sm.id " \
                "WHERE aml.product_id IS NOT NULL AND b.type = 'product' AND aml.company_id=%s AND aml.date <= %s and sm.location_dest_id=%s" \
                "GROUP BY aml.product_id, aml.account_id,aml.date"
        self.env.cr.execute(query, (self.env.user.company_id.id, tglin, kb))
        res = self.env.cr.dictfetchall()
        if res != None:
            for allm in res:
                pprod = self.env['product.product'].search([("id", '=', allm['product_id'])])
                if pprod.product_tmpl_id.valuation == 'manual_periodic':
                    domain = [('product_id', '=', allm['product_id']),
                              ('date', '<=', tglin)]
                    moves = StockMove.search(domain)
                    print('move ',moves)
                    hasil = {'tglan': allm['date'],
                             'nama_barang': allm['product_id'],
                             'qty': pprod.qty_available,
                             'values': sum(moves.mapped('value')),
                             'uom': pprod.product_tmpl_id.uom_id.id}
                elif pprod.product_tmpl_id.valuation == 'real_time':
                    valuation_account_id = pprod.product_tmpl_id.categ_id.property_stock_valuation_account_id.id
                    valua, quantity, aml_ids = fifo_automated_values.get((pprod.id, valuation_account_id)) or (
                        0, 0, [])
                    hasil = {
                             'val_warehouse_id': self.id,
                             'tglan': allm['date'],
                             'nama_barang': allm['product_id'],
                             'qty': quantity,
                             'values': valua,
                             'uom': pprod.product_tmpl_id.uom_id.id}

                semua_hasil |= self.env['valuation.warehouse.details'].new(hasil)
        return semua_hasil



class yudha_valuation_warehouse_details(models.Model):
    _name='valuation.warehouse.details'

    val_warehouse_id = fields.Many2one("valuation.warehouse",string='val id')
    tglan =  fields.Date("Date")
    nama_barang = fields.Many2one("product.product", string='Name')
    qty =  fields.Float('Quantity')
    uom = fields.Many2one("uom.uom", string='Unit Of Measure')
    values = fields.Float('Value', digits=dp.get_precision('Product Price'),)

