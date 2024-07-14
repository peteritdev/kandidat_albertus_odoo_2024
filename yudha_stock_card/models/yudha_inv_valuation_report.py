# -*- coding : utf-8 -*-
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA

import time
from odoo import api, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_round as round


class yudha_inv_valuation_Rpt(models.AbstractModel):
    _name = 'report.yudha_stock_card.inventory_valuation_report_main'


    def get_lines(self, data):
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        wh_id = data['form']['wh_id']
        lok_id = data['form']['lok_id']
        grp_by = data['form']['grp_by']
        flter_by = data['form']['flter_by']
        lines = []
        line_list = []
        StockMove = self.env['stock.move']
        prod_sama  =[]
        domain = [
                    ('date', '>=', start_date),
                    ('date', '<=', end_date)]
        tglawal = "stm.date >= '%s 00:00:00'" % (start_date)
        tglakhir ="stm.date <= '%s 24:00:00'" % (end_date)
        lokasal = "stm.location_id in (%s)" %(tuple(lok_id))
        lokakhir = "stm.location_dest_id in (%s)"%(tuple(lok_id))
        if grp_by:
            company_id = self.env.user.company_id.id
            domain.append(('company_id', '=', company_id))
        if flter_by == 'product':
            query_str = """
                SELECT stm.product_id
                FROM stock_move stm  
                WHERE %s and  %s and  %s or %s
                GROUP BY stm.product_id
            """
        elif flter_by == 'category':
            query_str = """
                SELECT stm.product_id
                FROM stock_move stm 
                WHERE %s and  %s and  %s or %s
                GROUP BY pp.categ_id
            """
        else:
            query_str = """
                SELECT stm.product_id
                FROM stock_move stm
                WHERE %s and  %s and  %s or %s

            """
        myquery = query_str % (tglawal,tglakhir,lokasal,lokakhir)
        self.env.cr.execute(myquery)
        for value in self.env.cr.dictfetchall():
                dataku ={'product_id': value['product_id']}
                line_list.append(dataku)
        if line_list:
            for product in line_list:
                total_amount = 0
                #if flter_by =='product':
                if  product['product_id'] not in prod_sama:
                    date = "'%s 24:00:00'" % (start_date)
                    mylok ="%s" %(tuple(lok_id))
                    myprod = self.env['product.product'].browse(product['product_id'])
                    prod_sama.append(myprod.id)
                    prod_id = myprod.id
                    myprodt ="%s" % (prod_id)
                    sal_qty = self._get_sale(prod_id,myprod.uom_id.id,start_date,end_date)
                    val_sal = sal_qty * myprod.standard_price
                    beg_ball = self._get_beggin_bal(prod_id,myprod.uom_id.id,date,tuple(lok_id))
                    val_bal = beg_ball  * myprod.standard_price
                    tdate1 ="'%s 00:00:00'" % (start_date)
                    tdate2 ="'%s 24:00:00'" % (end_date)
                    tdate = "date >= '%s 00:00:00' and date <= '%s 24:00:00'" % (start_date,end_date)
                    lok_gue =[]
                    for allok in lok_id:
                        lok_gue.append("'%s'," % str(allok))
                    rec_bal = self._get_reciev_bal(prod_id,myprod.uom_id.id,tdate1,tdate2,tuple(lok_id))
                    rev_Val = rec_bal * myprod.standard_price
                    mylok1 = "location_id in (%s)" % (tuple(lok_id))
                    int_qty = self._get_internal_bal(prod_id,myprod.uom_id.id,tdate1,tdate2,tuple(lok_id))
                    int_val =  int_qty * myprod.standard_price
                    adj_qty = self._get_adjustment_bal(prod_id,myprod.uom_id.id,tdate1,tdate2,tuple(lok_id))
                    adj_val = adj_qty * myprod.standard_price
                    akhir_qty = (beg_ball +rec_bal) -(sal_qty+int_qty)
                    akhir_val = akhir_qty *myprod.standard_price
                    hasil = {'prod_name': myprod.name,
                              'cost_met': myprod.categ_id.property_cost_method,
                             'beg_bal': beg_ball,
                             'val_bal':val_bal,
                             'rec_bal': rec_bal,
                             'rec_val': rev_Val,
                             'sal_qty': sal_qty,
                             'sal_val': val_sal,
                             'int_qty': int_qty,
                             'int_val': int_val,
                             'adj_qty': adj_qty,
                             'adj_val': adj_val,
                             'akhir_qty': akhir_qty,
                             'akhir_val': akhir_val,
                             }
                    lines.append(hasil)
        else:
            raise UserError('Record does not exists')
        return lines

    def _get_beggin_bal(self,prodid,uom_id,date,lokid):
        if not prodid:
            return 0.0
        domain = [('product_id','=',prodid),
                  ('date','<',date),
                  ('location_dest_id','in',lokid)]
        mystm = self.env['stock.move'].search(domain)
        qty_quant = 0
        if mystm:
            tot_qty = 0.0
            for allstm in mystm:
                tot_qty += allstm.product_uom_qty
            qty = self.convert_uom_qty(prodid, uom_id, tot_qty)
            qty_quant = qty
        else:
            qty_quant = 0
        return qty_quant

    def _get_reciev_bal(self,prodid,uom_id,tglin,tglout,lokid):
        if not prodid:
            return 0.0
        domain = [('product_id','=',prodid),
                  ('date','>=',tglin),
                  ('date','<=',tglout),
                  ('location_dest_id','in',lokid)]
        mystm = self.env['stock.move'].search(domain)
        qty_quant =0
        if mystm:
            tot_qty =0.0
            for allstm in mystm:
                tot_qty += allstm.product_uom_qty
            qty = self.convert_uom_qty(prodid,uom_id,tot_qty)
            qty_quant = qty
        else:
            qty_quant = 0
        return qty_quant

    def _get_internal_bal(self,prodid,uom_id,tglin,tglout,lokid):
        if not prodid:
            return 0.0
        domain = [('product_id','=',prodid),
                  ('date','>=',tglin),
                  ('date','<=',tglout),
                  ('location_id','in',lokid)]
        mystm = self.env['stock.move'].search(domain)
        qty_quant =0
        if mystm:
            tot_qty =0.0
            for allstm in mystm:
                tot_qty += allstm.product_uom_qty
            qty = self.convert_uom_qty(prodid,uom_id,tot_qty)
            qty_quant = qty
        else:
            qty_quant = 0
        return qty_quant

    def _get_adjustment_bal(self,prodid,uom_id,tglin,tglout,lokid):
        if not prodid:
            return 0.0
        domain = [('product_id','=',prodid),
                  ('date','>=',tglin),
                  ('date','<=',tglout),
                  ('reference','ilike','INV:')]
        mystm = self.env['stock.move'].search(domain)
        qty_quant = 0
        if mystm:
            tot_qty = 0.0
            for allstm in mystm:
                tot_qty += allstm.product_uom_qty
            qty = self.convert_uom_qty(prodid, uom_id, tot_qty)
            qty_quant = qty
        else:
            qty_quant = 0
        return qty_quant


    def _get_sale(self,prod_id,uom_id,tglin,tglout):
        if not prod_id:
            return 0.0
        domain = [('date_order', '>=', tglin),
                  ('date_order', '<=', tglout)]
        mystm = self.env['sale.order'].search(domain)
        qty_quant = 0
        if mystm:
            for alline in mystm:
                for allorder in alline.order_line:
                    if allorder.product_id.id == prod_id:
                        tot_qty = 0.0
                        for allstm in mystm:
                            tot_qty += allorder.product_uom_qty
                        qty = self.convert_uom_qty(prod_id, uom_id, tot_qty)
                        qty_quant = qty
        else:
            qty_quant = 0
        return qty_quant



    def convert_uom_qty(self, product_id,sm_uom_id,qty):
        product = self.env['product.product'].browse(product_id)
        uom 	= self.env['uom.uom'].browse(sm_uom_id)
        if product_id == 45:
            print ('ini')
        if uom.id != product.uom_id.id:
            factor = product.uom_id.factor / uom.factor
        else:
            factor = 1.0
        converted_qty = qty * factor
        return converted_qty


    @api.model
    def _get_report_values(self, docids, data=None):
        mymodel = self.env['yudha_inventory_valuation.report'].browse(docids)
        data['form']= {}
        data['form'].update(mymodel.read(['date_start', 'date_end', 'wh_id','lok_id','grp_by','flter_by'])[0])
        docs = mymodel
        product_det = {}
        product_det = self.get_lines(data)
        docargs = {
            'doc_ids' : docids,
            'doc_model': 'yudha_inventory_valuation.report',
            'data': data,
            'docs': docs,
            'time': time,
            'lines': product_det,
        }
        return docargs


