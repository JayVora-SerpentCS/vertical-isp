# -*- coding: utf-8 -*-
# © 2013 Savoirfaire-Linux Inc. (<www.savoirfairelinux.com>).
# © 2016-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import calendar
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def date_interval(start_date, month_end=True, date_format='%m/%d/%Y'):
    if month_end:
        end_date = datetime.date(start_date.year,
                                 start_date.month,
                                 calendar.monthrange(start_date.year,
                                                     start_date.month)[1])
    else:
        end_date = add_months(start_date, 1) - datetime.timedelta(days=1)
    return start_date, end_date


def format_interval(start, end, date_format=DEFAULT_SERVER_DATE_FORMAT):
    return '(%s - %s)' % (start.strftime(date_format),
                          end.strftime(date_format))


def operation_date(date=None, context=None):
    if context is None:
        context = {}
    if date is None:
        date = context.get("operation_date", datetime.date.today())
    if not isinstance(date, datetime.date):
        date = datetime.datetime.strptime(
            date,
            DEFAULT_SERVER_DATE_FORMAT,
        ).date()
    return date


class res_company(models.Model):

    _inherit = "res.company"

    @api.multi
    def _days(self):
        return tuple([(str(x), str(x)) for x in range(1, 29)])

    parent_account_id = fields.Many2one('account.analytic.account',
                                        'Parent Analytic Account')
    cutoff_day = fields.Selection(_days, 'Cutoff day')
#    default_journal_id = fields.Many2one('account.analytic.journal',
#                                         'Default Journal')


class res_partner(models.Model):

    _inherit = 'res.partner'

    partner_analytic_account_id = fields.Many2one('account.analytic.account',
                                                  'Partner Analytic Account')

    @api.model
    def create(self, vals):
        account_analytic_account = self.env['account.analytic.account']
        company_obj = self.env['res.company']
        company = company_obj._company_default_get()
        ret = super(res_partner, self).create(vals)
        parent_id = company.parent_account_id and company.parent_account_id.id
        account = {
            'name': vals['name'],
            'parent_id': parent_id,
            'type': 'view',
            'partner_id': ret.id,
            'user_id': self._uid
        }
        account_id = account_analytic_account.create(account)
        ret.write({'partner_analytic_account_id': account_id.id})
        return ret


class product_product(models.Model):

    _inherit = 'product.product'

    analytic_line_type = fields.Selection((('r', 'Recurrent'),
                                           ('x', 'Exception'),
                                           ('o', 'One time')),
                                          'Type in contract')
    require_activation = fields.Boolean(string='Require activation')


class contract_service(models.Model):

    _name = 'contract.service'

    @api.depends('price', 'unit_price')
    def _get_product_price(self):
        partner_id = self.account_id.partner_id.id
        pricelist_id = self.account_id.partner_id.property_product_pricelist
        if self.product_id and partner_id:
            self.unit_price = pricelist_id.price_get(self.product_id.id, 1,
                                                partner_id)[pricelist_id.
                                                            id]
        else:
            self.unit_price = None

    @api.depends('unit_price', 'qty')
    def _get_total_product_price(self):
        self.price = self.unit_price * self.qty

    activation_date = fields.Datetime('Activation date')
    duration = fields.Integer('Duration')
    deactivation_date = fields.Datetime('Deactivation Date')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    qty = fields.Float('Qty', digits_compute=dp.get_precision
                       ('Product Unit of Measure'), default=1)
    category_id = fields.Many2one('product.category', 'Product Category',
                                  default=1)
    name = fields.Char('Description')
    analytic_line_type = fields.Selection((('r', 'Recurrent'),
                                           ('x', 'Exception'),
                                           ('o', 'One time')),
                                          'Type')
    require_activation = fields.Boolean('Require activation')
    account_id = fields.Many2one('account.analytic.account', 'Contract')
    unit_price = fields.Float(compute='_get_product_price',
                              digits_compute=dp.get_precision('Product Price'),
                              string='Unit Price')
    price = fields.Float(compute='_get_total_product_price', type='float',
                         digits_compute=dp.get_precision('Product Price'),
                         string='Price')
    activation_line_generated = fields.Boolean('Activation Line Generated?',
                                               default=False)
    state = fields.Selection((('draft', 'Waiting for activating'),
                              ('active', 'Active'),
                              ('inactive', 'Inactive')),
                             'State', default='draft')

    @api.onchange('product_id')
    def on_change_product_id(self):
        product = self.product_id
        if product:
            self.analytic_line_type = product.analytic_line_type
            self.require_activation = product.require_activation
            self.category_id = product.categ_id.id
            self.unit_price = product.list_price
            if self.analytic_line_type in ('r', 'o'):
                self.duration = 0
            else:
                self.duration = 1

    @api.onchange('qty', 'price')
    def on_change_qty(self):
        if self.qty:
            self.price = self.qty * self.price

    @api.model
    def _prorata_rate(self, days_used, days_in_month):
        """ Returns a rate to compute prorata invoices.
        Current method is days_used / days_in_month, rounded DOWN
        to 2 digits
        """
        return (100 * days_used // days_in_month) / 100.0

    @api.multi
    def _get_prorata_interval_rate(self, change_date):
        """ Get the prorata interval and price rate.

        Returns a tuple (start_date, end_date, price percent)
        """
        month_days = calendar.monthrange(change_date.year,
                                         change_date.month)[1]
#        start_date = add_months(change_date, 1)
        start_date = change_date
        end_date = start_date.replace(day=month_days)
        used_days = month_days - change_date.day
        ptx = self._prorata_rate(used_days, month_days)
        return start_date, end_date, ptx

    @api.multi
    def _get_prorata_interval_rate_deactivate(self, change_date):
        start_date, end_date, ptx = self.\
        _get_prorata_interval_rate(change_date)
        ptx = ptx * -1
        return start_date, end_date, ptx

    def _get_date_format(self, obj):
        partner_lang = obj.account_id.partner_id.lang
        res_lang_obj = self.env['res.lang']
        query = [
            ('code', '=', partner_lang),
            ('active', '=', True)
        ]
        lang_id = res_lang_obj.search(query)
        if lang_id:
            date_format = lang_id.date_format
        else:
            date_format = '%Y/%m/%d'
        return date_format

    @api.multi
    def create_analytic_line(self, mode='manual', date=None):
        context = dict(self._context)
        date = operation_date(date, context)
        if type(self.ids) is int:
            self.ids = [self.ids]
        ret = []
        record = {}
        account_analytic_line_obj = self.env['account.analytic.line']
        for line in self:
            date_format = self._get_date_format(line)
            start, end = None, None
            next_month = None
            amount = line.price
            if line.analytic_line_type == 'r':
                if mode == 'prorata':
                    activation_date = date
                    start, end, ptx = self._get_prorata_interval_rate(
                        activation_date)
                    amount = amount * ptx
                elif mode == 'cron':
                    next_month = add_months(date, 1)
                    next_month = datetime.date(
                        next_month.year,
                        next_month.month,
                        1)
                    start, end = date_interval(next_month, False)
                    end
                elif mode == 'manual':
                    start, end = date_interval(date, False)
                    end

                elif mode == 'subscription':
                    line.write({'activation_line_generated': True})

            if start and end:
                interval = format_interval(start, end, date_format)
            else:
                interval = ''

            general_account_id = line.product_id.property_account_expense_id.\
            id or line.product_id.categ_id.property_account_expense_categ_id.id
            record = {
                'name': ' '.join([line.product_id.name,
                                  line.name or '',
                                  interval]),
                'amount': (amount * -1),
                'account_id': line.account_id.id,
                'user_id': self._uid,
                'general_account_id': general_account_id,
                'product_id': line.product_id.id,
                'contract_service_id': line.id,
                'to_invoice': 1,
                'unit_amount': line.qty,
                'is_prorata': mode == 'prorata',
                'date': (next_month or date).strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'journal_id': 1
            }
            if line.analytic_line_type == 'x':
                new_duration = line.duration - 1
                line.write({'duration': new_duration})
                if new_duration <= 0:
                    line.unlink()
                    record['contract_service_id'] = False
            elif line.analytic_line_type == 'o':
                if line.duration > 0:
                    line.write({'duration': line.duration - 1})
                else:
                    # Do not create an already billed line
                    continue
            if 'default_type' in context:
                context.pop('default_type')
            ret.append(account_analytic_line_obj.create(record).id)
        return ret

    @api.multi
    def create_refund_line(self, ids,
                           mode='manual',
                           date=None):
        context = self._context
        context = context or {}
        date = operation_date(date, context)

        if type(ids) is int:
            ids = [ids]
        ret = []
        record = {}
        account_analytic_line_obj = self.env['account.analytic.line']
        for line in self.browse(ids):
            if any((line.analytic_line_type != 'r',
                    mode != "prorata")):
                # Not handled for now, only pro-rata deactivate
                continue
            date_format = self._get_date_format(line)
            deactivation_date = date
            start, end, ptx = self.\
            _get_prorata_interval_rate_deactivate(deactivation_date)
            amount = line.product_id.list_price * ptx
            interval = format_interval(start, end,
                                       date_format=date_format)
            general_account_id = (
                line.product_id.property_account_expense_id.id or
                line.product_id.categ_id.property_account_expense_categ_id.id
            )
            record = {
                'name': ' '.join([line.product_id.name,
                                  line.name or '',
                                  interval]),
                'amount': (amount * -1) * line.qty,
                'account_id': line.account_id.id,
                'user_id': self._uid,
                'general_account_id': general_account_id,
                'product_id': line.product_id.id,
                'contract_service_id': line.id,
                'to_invoice': 1,
                'unit_amount': line.qty,
                'is_prorata': mode == 'prorata',
                'date': date.strftime('%Y-%m-%d'),
                'journal_id': 1
            }
            if 'default_type' in context:
                context.pop('default_type')
            ret.append(account_analytic_line_obj.create(record).id)
        return ret

    @api.model
    def create(self, values):
        if not values["require_activation"]:
            values["state"] = 'active'
            values["activation_date"] = fields.datetime.now()
        return super(contract_service, self).create(values)

    @api.multi
    def action_desactivate(self, ids, context):
        values = {'state': 'inactive'}
        if "deactivation_date" in context:
            values["deactivation_date"] = context["deactivation_date"]
        else:
            values["deactivation_date"] = fields.datetime.now()
        contract_service_rec = self.browse(ids)
        contract_service_rec.write(values)
        return True


class account_analytic_account(models.Model):

    _inherit = "account.analytic.account"

    contract_service_ids = fields.One2many('contract.service',
                                           'account_id',
                                           'Services')
    use_contract_services = fields.Boolean('Contract services', default=False)

#    state = fields.Selection([('template', 'Template'),
#                              ('draft', 'New'),
#                              ('open', 'In Progress'),
#                              ('pending', 'Suspended'),
#                              ('close', 'Closed'),
#                              ('cancelled', 'Cancelled')],
#                             'Status', required=True,
#                             track_visibility='onchange')

#         No on_change_partner_id defined in analytic base module.
#    @api.model
#    def on_change_partner_id(self, partner_id, name,
#                             code=None):
#        res = {}
#        if partner_id:
#            partner = self.env['res.partner'].browse(partner_id)
#            if partner.user_id:
#                res['manager_id'] = partner.user_id.id
#            if not name:
#                if code:
#                    res['name'] = code
#                else:
#                    res['name'] = _('Contract: ') + partner.name
#            # Use pricelist from customer
#            res['pricelist_id'] = partner.property_product_pricelist.id
#        return {'value': res}

    @api.multi
    def create_analytic_lines(self):
        mode = 'manual'
        context = self._context
        if context and context.get('create_analytic_line_mode', False):
            mode = context.get('create_analytic_line_mode')
        contract_service_obj = self.env['contract.service']
        contract_service_ids = contract_service_obj.search([])
        if contract_service_ids:
            for contract_serv in contract_service_ids:
                contract_serv.create_analytic_line(mode=mode)
        return {}

#    This method is not used in any module.
    @api.multi
    def create_refund_lines(self):
        ids, context = self.env.args
        context = context or {}
        mode = context.get('create_analytic_line_mode', 'manual')
        contract_service_obj = self.env['contract.service']
        query = [
            ('account_id', 'in', ids),
            ('state', '=', 'inactive'),
            # only recurrent is handled in refund right now
            ('analytic_line_type', 'in', ('r',)),
        ]
        contract_service_ids = contract_service_obj.search(query,
                                                           order='account_id',
                                                           context=context)
        if contract_service_ids:
            contract_service_obj.create_refund_line(contract_service_ids,
                                                    mode=mode,
                                                    context=context)
        return {}

#        No parent_id field on account.analytic.account in v9(base module).
#    def create(self, cr, uid, values, context=None):
#        if values.get('use_contract_services'):
#            values['name'] = values['code']
#            partner_obj = self.pool.get('res.partner')
#            partner_analytic_data = partner_obj.read(
#                cr, uid, values['partner_id'],
#                fields=['partner_analytic_account_id'],
#                context=context)
#            if partner_analytic_data:
#                values['parent_id'] =\
#                 partner_analytic_data.get('partner_analytic_account_id')
#                print ""
#        return super(account_analytic_account, self).create(cr, uid, values,
#                                                           context)


class account_analytic_line(models.Model):

    _inherit = "account.analytic.line"

    contract_service_id = fields.Many2one('contract.service', 'Service')
    is_prorata = fields.Boolean('Prorata', defaults=False)
