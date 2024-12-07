# -*- coding: utf-8 -*-
{
    'name': "Pos Multi Currency Payment",
    'version': '1.0',
    'summary': 'User can do payment in multiple-currency on POS Screen',
    'description': """
        The User will get the option to pay in multiple-currency on the PaymentScreen.
        This payment in multi-currency will be reflected on receipt as well as backend.
    """,
    'category': 'Point Of Sale',
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'www.synconics.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_config_settings.xml',
        'views/pos_order_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'sync_pos_currency/static/src/**/*'
        ],
    },
    'images': [
        'static/description/main_screen.png'
    ],
    'price': 40,
    'currency': 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
