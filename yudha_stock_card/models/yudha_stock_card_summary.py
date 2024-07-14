# -*- coding : utf-8 -*-
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA

from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


SC_STATES = [('draft', 'Draft'), ('open', 'Open'), ('done', 'Done')]

class yudha_stock_card_summary(models.Model):
    _name = "yudha.stock.summary"
    _rec_name = "location_id"

    ref				= fields.Char("Number")
    date_start		= fields.Date("Date Start", required=True, default=lambda *a : time.strftime("%Y-%m-%d"))
    date_end		= fields.Date("Date End", required=True, default=lambda *a : time.strftime("%Y-%m-%d"))
    location_id		= fields.Many2one('stock.location', 'Location', required=True)
    line_ids		= fields.One2many( 'yudha.stock.summary.line', 'stock_summary_id','Details', ondelete="cascade")
    breakdown_sn	= fields.Boolean("Breakdown Lot/Serial Number?")
    state			= fields.Selection( SC_STATES, 'Status',readonly= True,required=True, default="draft")
    user_id			= fields.Many2one('res.users', 'Created', default=lambda self: self.env.user)


    def action_calculate(self):
        cr = self.env.cr
        sc=self
        cr.execute("delete from yudha_stock_summary_line where stock_summary_id=%s" % sc.id)

        if sc.breakdown_sn:
            self.beginning_lines_sn()
            self.mutasi_lines_sn()
        else:
            self.beginning_lines_nosn()
            self.mutasi_lines_nosn()

        self.update_balance()
        return


    def beginning_lines_sn(self):
        date = "date < '%s 24:00:00'" % (self.date_start)
        line_type = "beg"
        self.process_lines_sn(line_type, date)

    def mutasi_lines_sn(self):
        date = "m.date >= '%s 00:00:00' and m.date <= '%s 24:00:00'" % (self.date_start, self.date_end)
        line_type = "mut"
        self.process_lines_sn(line_type, date)


    def process_lines_sn(self, line_type, date):
        sql = "select m.product_id, m.product_uom, lot_id, sum(q.quantity)\
                from \
                stock_quant q \
                left join product_product pp on q.product_id = pp.id \
                join stock_move m on m.product_id=pp.id \
                where %s \
                and %s \
                group by q.lot_id,m.product_id,m.product_uom  \
                order by m.product_id "
        if line_type == "beg":
            self.fill_product_data(sql)
            self.update_starting(sql)
        if line_type == "mut":
            self.update_incoming(sql)
            self.update_outgoing(sql)

        return

    def fill_product_data(self, sql):
        cr =self.env.cr
        stock_summary_line = self.env['yudha.stock.summary.line']

        date = "m.date <= '%s 24:00:00'" % (self.date_end)
        loc = "(m.location_id = %s or m.location_dest_id=%s)" % (self.location_id.id, self.location_id.id)
        cr.execute(sql % (date, loc))
        res = cr.fetchall()
        if not res or res[0] == None:
            return False
        for beg in res:
            product_id 		= beg[0]
            product_uom_id	= beg[1]
            lot_id 			= beg[2]
            qty 			= beg[3]
            data = {
                "stock_summary_id"	: self.id,
                "product_id"		: product_id,
                "product_uom_id"	: product_uom_id,
                "lot_id"			: lot_id,
            }
            stock_summary_line |= self.env['yudha.stock.summary.line'].create(data)
        self.line_ids = stock_summary_line.ids

    def update_starting(self, sql):
        cr =self.env.cr
        date = "m.date < '%s 00:00:00'" % (self.date_start)
        loc = "m.location_dest_id=%s" % (self.location_id.id)
        cr.execute(sql % (date, loc))
        res = cr.fetchall()
        if not res or res[0] == None:
            return False
        for beg in res:
            product_id 		= beg[0]
            sm_uom_id		= beg[1]
            lot_id 			= beg[2]
            if lot_id is None:
                lot_id = " is null"
            else:
                lot_id = "=%s"  % (lot_id)
            qty 			= beg[3]

            qty, product_uom_id = self.convert_uom_qty(product_id, sm_uom_id,qty)

            sql2 = "update yudha_stock_summary_line set \
                        qty_start = %s \
                        where stock_summary_id=%s and product_id=%s and lot_id %s" % \
                   (qty, self.id, product_id, lot_id)
            cr.execute(sql2)

    def update_incoming(self, sql):
        cr =self.env.cr
        date = "m.date >= '%s 00:00:00' and m.date <='%s 24:00:00'" % (self.date_start, self.date_end)
        loc = "m.location_dest_id=%s" % (self.location_id.id)
        cr.execute(sql % (date, loc))
        res = cr.fetchall()
        if not res or res[0] is None:
            return False
        for beg in res:
            product_id 		= beg[0]
            sm_uom_id		= beg[1]
            lot_id 			= beg[2]
            if lot_id is None:
                lot_id = " is null"
            else:
                lot_id = "=%s"  % (lot_id)
            qty 			= beg[3]

            qty, product_uom_id = self.convert_uom_qty(product_id, sm_uom_id,qty)

            sql2 = "update yudha_stock_summary_line set \
                        qty_in = %s \
                        where stock_summary_id=%s and product_id=%s and lot_id %s" % \
                   (qty, self.id, product_id, lot_id)
            cr.execute(sql2)

    def update_outgoing(self, sql):
        cr =self.env.cr
        date = "m.date >= '%s 00:00:00' and m.date <='%s 24:00:00'" % (self.date_start, self.date_end)
        loc = "m.location_id=%s" % (self.location_id.id)
        cr.execute(sql % (date, loc))
        res = cr.fetchall()
        if not res or res[0] is None:
            return False
        for beg in res:
            product_id 		= beg[0]
            sm_uom_id		= beg[1]
            lot_id 			= beg[2]
            if lot_id is None:
                lot_id = " is null"
            else:
                lot_id = "=%s"  % (lot_id)
            qty 			= beg[3]

            qty, product_uom_id = self.convert_uom_qty(product_id, sm_uom_id,qty)

            sql2 = "update yudha_stock_summary_line set \
                        qty_out = %s \
                        where stock_summary_id=%s and product_id=%s and lot_id %s" % \
                   (qty, self.id, product_id, lot_id)
            cr.execute(sql2)

    def beginning_lines_nosn(self):
        date = "date < '%s 24:00:00'" % (self.date_start)
        self.process_lines_nosn('beg', date)



    def mutasi_lines_nosn(self):
        date = "date >= '%s 00:00:00' and date <= '%s 24:00:00'" % (self.date_start, self.date_end)
        self.process_lines_nosn('mut', date)


    def process_lines_nosn(self, line_type, date):
        cr =self.env.cr
        stock_summary_line = self.env['yudha.stock.summary.line']

        sql = "select product_id,\
                    product_uom,\
                    sum(product_uom_qty) \
                    from stock_move as m \
                    where %s and %s = %s \
                    and state = 'done' \
                    group by product_id,product_uom \
                    order by product_id"

        # incoming
        cr.execute(sql % (date, "location_dest_id", self.location_id.id))
        res = cr.fetchall()
        if not res or res[0] == 'None':
            return
        if line_type=="beg":
            for beg in res:
                product_id = beg[0]
                sm_uom_id = beg[1]
                qty = beg[2]
                qty,product_uom_id = self.convert_uom_qty(product_id, sm_uom_id, qty )
                data = {
                    "stock_summary_id"	: self.id,
                    "product_id"		: product_id,
                    "product_uom_id"	: product_uom_id,
                    "qty_start"			: qty,
                    "qty_in"			: 0,
                    "qty_out"			: 0,
                    "qty_balance"		: 0,
                }
                stock_summary_line |= self.env['yudha.stock.summary.line'].create(data)
            self.line_ids = stock_summary_line.ids
        else:
            for incoming in res:
                product_id = incoming[0]
                sm_uom_id = incoming[1]
                qty = incoming[2]
                qty,product_uom_id = self.convert_uom_qty(product_id, sm_uom_id, qty )

                sql2 = "update yudha_stock_summary_line set \
                                    qty_in = %s \
                                    where stock_summary_id = %s and product_id=%s" % (qty, self.id, product_id)
                cr.execute(sql2)


        # outgoing
        cr.execute(sql % (date, "location_id", self.location_id.id))
        res = cr.fetchall()
        if not res or res[0] == 'None':
            return

        if line_type=="beg":
            for beg in res:
                product_id = beg[0]
                sm_uom_id = beg[1]
                qty = beg[2]
                qty,product_uom_id = self.convert_uom_qty(product_id, sm_uom_id, qty )
                sql2 = "update yudha_stock_summary_line set \
                            qty_start = qty_start - %s \
                            where stock_summary_id = %s and product_id=%s" % (
                    qty, self.id ,product_id )
                cr.execute(sql2)
        else:
            for outgoing in res:
                product_id = outgoing[0]
                sm_uom_id = outgoing[1]
                qty = abs(outgoing[2])
                qty,product_uom_id = self.convert_uom_qty(product_id, sm_uom_id, qty )

                sql2 = "update yudha_stock_summary_line set \
                            qty_out = %s \
                            where stock_summary_id = %s and product_id=%s" % (
                    qty, self.id, product_id)
                cr.execute(sql2)

        # balance
        sql = "update yudha_stock_summary_line set qty_balance = qty_start + qty_in - qty_out \
            where stock_summary_id = %s " % (self.id)
        cr.execute(sql)

    def convert_uom_qty(self, product_id,sm_uom_id,qty):

        product = self.env['product.product'].browse(product_id)
        uom 	= self.env['uom.uom'].browse(sm_uom_id)

        if uom.id != product.uom_id.id:
            factor = product.uom_id.factor / uom.factor
        else:
            factor = 1.0

        converted_qty = qty * factor

        return converted_qty, product.uom_id.id

    def update_balance(self):
        cr =self.env.cr
        sql3 = "update yudha_stock_summary_line set \
            qty_balance =  coalesce( qty_start,0) +  coalesce(qty_in,0) -  coalesce(qty_out,0) \
            where stock_summary_id = %s " % (self.id)
        cr.execute(sql3)

    def action_draft(self):
        # set to "draft" state
        return self.write({'state' :SC_STATES[0][0]})

    def action_confirm(self):
        # set to "confirmed" state
        return self.write({'state' :SC_STATES[1][0]})

    def action_done(self):
        # set to "done" state
        return self.write({'state' :SC_STATES[2][0]})

    @api.model
    def create(self, vals):

        vals['ref']=self.env['ir.sequence'].next_by_code('vit.stock_summary')
        new_id = super(yudha_stock_card_summary, self).create(vals)
        return new_id


class yudha_stock_card_summary_line(models.Model):
    _name 		= "yudha.stock.summary.line"
    _order 		= "product_id"

    name			    = fields.Char("Description")
    stock_summary_id	= fields.Many2one('yudha.stock.summary_id', 'Stock Card')
    product_id	        = fields.Many2one('product.product', 'Product')
    product_uom_id      = fields.Many2one('uom.uom', 'UoM')
    lot_id		        = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    stock_move_id	    = fields.Many2one('stock.move', 'Stock Move')
    #expired_date	    = fields.Datetime(related='lot_id.life_date',string='ED',store=True)
    expired_date	    = fields.Datetime(string='ED',store=True)
    qty_start		    = fields.Float("Start")
    qty_in	        	= fields.Float("Qty In")
    qty_out		        = fields.Float("Qty Out")
    qty_balance	        = fields.Float("Balance")


