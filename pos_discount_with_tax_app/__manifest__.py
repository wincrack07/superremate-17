# -*- coding: utf-8 -*-
{
    "name" : "POS Discount on Taxed/Untaxed Amount",
    "author": "Edge Technologies",
    "version" : "17.0",
    "live_test_url":'https://youtu.be/6NvKJmecGvk',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Point of sale discount with tax amount point of sale discount with untaxed amount pos discount with tax amount pos discount with untaxed amount point of sale discount with tax pos tax discounted point of sale tax discounted amount point of sales discount.',
    "description": """
    
       Using this module you can apply fixed/percentage discount on whole pos order amount or orderline amount with/without tax.
    point of sale discount with tax amount point of sale discount with untaxed amount.
    pos discount with tax amount pos discount with untaxed amount point of sale discount with tax. pos tax discounted point of sale tax discounted amount. point of sale discount with tax calculation pos discount with tax calculation.
    
    """,
    "license" : "OPL-1",
    "depends" : ['base','account','point_of_sale'],
    "data": [
        'views/pos_custom_view.xml',
        'views/account_invoice.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_discount_with_tax_app/static/src/js/Popups/SelectDiscountPopupWidget.js',
            'pos_discount_with_tax_app/static/src/js/Popups/DiscountPopup.js',
            'pos_discount_with_tax_app/static/src/js/ProductScreen/OrderWidget.js',
            'pos_discount_with_tax_app/static/src/js/ProductScreen/ProductScreen.js',
            'pos_discount_with_tax_app/static/src/js/ProductScreen/orderline.js',
            'pos_discount_with_tax_app/static/src/js/ProductScreen/ControlButton/OrderDiscountButton.js',
            'pos_discount_with_tax_app/static/src/js/models.js',

            'pos_discount_with_tax_app/static/src/xml/pos.xml',
            'pos_discount_with_tax_app/static/src/xml/Orderline.xml',
            'pos_discount_with_tax_app/static/src/xml/SelectDiscountPopup.xml',
            'pos_discount_with_tax_app/static/src/xml/DiscountTypePopup.xml',
            'pos_discount_with_tax_app/static/src/xml/OrderDiscountButton/OrderDiscountButton.xml',
        ],
        'web.assets_backend': [
            'pos_discount_with_tax_app/static/src/xml/TaxTotalsField.xml',
        ], 
    },
    "auto_install": False,
    "installable": True,
    "price": 29,
    "currency": 'EUR',
    "category" : "Point of Sale",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
