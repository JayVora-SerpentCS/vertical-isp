# -*- coding: utf-8 -*-
# © 2013 Savoirfaire-Linux Inc. (<www.savoirfairelinux.com>).
# © 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models


class ProductDependency(models.Model):

    _name = 'product.dependency'

    name = fields.Char('Name')
    ptype = fields.Selection([('product', 'Product'),
                              ('category', 'Category')], string='Type',
                             default='product')
    product_id = fields.Many2one('product.product',
                                 string='Product Dependency')
    category_id = fields.Many2one('product.category',
                                  string='Category Dependency')
    auto = fields.Boolean(string='Automatically added')

    @api.onchange('ptype')
    def onchange_type(self):
        if self.ptype == 'product':
            self.category_id = None
        elif self.ptype == 'category':
            self.product_id = None
        self.name = ''

    @api.onchange('product_id')
    def onchange_product_id(self):
        product_name = ''
        if self.product_id:
            product_name = self.product_id.name
        self.name = product_name

    @api.onchange('category_id')
    def onchange_category_id(self):
        category_name = ''
        if self.category_id:
            category_name = self.category_id.name
        self.name = category_name


class ProductProduct(models.Model):

    _inherit = 'product.product'

    dependency_ids = fields.Many2many('product.dependency',
                                      'product_product_dependency_rel',
                                      'dependency_id', 'product_id',
                                      string='Dependencies')
