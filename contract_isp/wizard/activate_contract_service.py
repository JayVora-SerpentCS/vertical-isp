# -*- coding: utf-8 -*-
# © 2013 Savoirfaire-Linux Inc. (<www.savoirfairelinux.com>).
# © 2016-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import api, fields, models, _


class contract_service_activate(models.TransientModel):

    _name = 'contract.service.activate'

    @api.model
    def default_get(self, fields):
        res = super(contract_service_activate, self).default_get(fields)
        if self._context.get('active_model', '') == 'contract.service':
            active_id = self._context.get('active_id')
            contract_service = self.env['contract.service'].browse(active_id)
            res.update({'account_id': contract_service.account_id.id,
                        'service_id': contract_service.id})
        return res

    activation_date = fields.Datetime('Activation Date',
                                      default=fields.datetime.now())
    account_id = fields.Many2one('account.analytic.account',
                                 'Account')
    service_id = fields.Many2one('contract.service',
                                 'Service')

    @api.multi
    def activate(self):
        contract_service_obj = self.env['contract.service']
        contract_service = contract_service_obj.browse(self.service_id.id)
        activation_date = datetime.date(
            int(self.activation_date[:4]),
            int(self.activation_date[5:7]),
            int(self.activation_date[8:10]))
        contract_service.write({
            'activation_date': self.activation_date,
            'state': 'active'
        })
        if contract_service.analytic_line_type == 'r':
            contract_service.create_analytic_line(mode='prorata',
                                      date=activation_date)
        return True

    @api.constrains('activation_date')
    def check_future_date(self):
        today = datetime.datetime.utcnow().date()
        for wiz in self:
            act_date = datetime.datetime.strptime(
                wiz.activation_date, DEFAULT_SERVER_DATETIME_FORMAT,
            ).date()
            if act_date > today:
                raise Warning(_('You cannot activate a service in future.'))
                return False
        return True


class contract_service_deactivate(models.TransientModel):

    _name = 'contract.service.deactivate'

    @api.model
    def default_get(self, fields):
        res = super(contract_service_deactivate, self).default_get(fields)
        if self._context.get('active_model', '') == 'contract.service':
            active_id = self._context.get('active_id')
            contract_service = self.env['contract.service'].browse(active_id)
            res.update({'account_id': contract_service.account_id.id,
                        'service_id': contract_service.id})
        return res

    deactivation_date = fields.Datetime('Deactivation Date',
                                        default=fields.datetime.now())
    account_id = fields.Many2one('account.analytic.account', 'Account')
    service_id = fields.Many2one('contract.service', 'Service')

    @api.multi
    def deactivate(self):
        context = self._context or {}
        context = dict(context)
        contract_service_obj = self.env['contract.service']
        context.update({'deactivation_date': self.deactivation_date})
        contract_service_obj.action_desactivate([self.service_id.id],
                                                context=context)
        # If we activate again, we will need a new activation line, as
        # we will have refunded any extra, and will need to bill in
        # advance again.
        self.service_id.write({
            'activation_line_generated': False
        })
        self._create_refund_lines()
        return True

    @api.multi
    def _create_refund_lines(self):
        contract_service_obj = self.env['contract.service']
        deactivate_date = datetime.datetime.strptime(
            self.deactivation_date,
            DEFAULT_SERVER_DATETIME_FORMAT,
        ).date()
        contract_service_obj.create_refund_line([self.service_id.id],
            mode='prorata', date=deactivate_date)

    @api.constrains('deactivation_date')
    def _check_future_date(self):
        today = datetime.datetime.utcnow().date()
        for wiz in self:
            act_date = datetime.datetime.strptime(
                wiz.deactivation_date, DEFAULT_SERVER_DATETIME_FORMAT,
            ).date()
            if act_date > today:
                raise Warning(_('You cannot deactivate a '
                                'service in the future.'))
                return False
        return True
