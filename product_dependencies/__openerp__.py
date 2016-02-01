# -*- coding: utf-8 -*-
# © 2013 Savoirfaire-Linux Inc. (<www.savoirfairelinux.com>).
# © 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    'name': 'Product Dependencies',
    'version': '9.0.1.0.0',
    'category': 'Product Management',
    'summary': """Allows products to have other products/categories\
     as dependencies.""",
    'contributors': ['Juan Ignacio Úbeda <juani@aizean.com>'],
    'author': "Savoir-faire Linux Inc, Serpent Consulting Services Pvt. Ltd.,\
    Odoo Community Association (OCA)",
    'website': 'www.savoirfairelinux.com',
    'license': 'LGPL-3',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_dependencies_view.xml'
    ],
    'installable': True,
    'application': False,
}
