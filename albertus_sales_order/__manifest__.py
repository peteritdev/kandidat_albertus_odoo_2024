# -*- coding : utf-8 -*-
#################################################################################
# Author    => Albertus Restiyanto Pramayudha
# email     => xabre0010@gmail.com
# linkedin  => https://www.linkedin.com/in/albertus-restiyanto-pramayudha-470261a8/
# youtube   => https://www.youtube.com/channel/UCCtgLDIfqehJ1R8cohMeTXA
#################################################################################
{
    'name': "Albertus Sales Order",
    'summary': "Albertus Sales Order",
    'description': """
            Albertus Sales Order
    """,
    'author': "Albertus Restiyanto Pramayudha",
    'website': "http://www.yourcompany.com",
    "support": "xabre0010@gmail.com",
    'category': 'Human Resource',
    'version': '0.1',
    'license': 'LGPL-3',
    'price': 0,
    'currency': 'USD',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management','stock','contacts','delivery'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_devisi_data.xml',
        'data/delivery_data.xml',
        'views/res_devisi.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/product_template.xml',
        'wizards/customer_credit_limit.xml',

    ],
    'assets': {
            'web.assets_backend': [
            ],
    },
    # only loaded in demonstration mode
    'demo': [
    ],
    "images": ["static/description/banner.png"],
}