# -*- coding: utf-8 -*-
# © 2013 Savoirfaire-Linux Inc. (<www.savoirfairelinux.com>).
# © 2016-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Contract ISP',
    'version': '9.0.1.0.0',
    'category': 'Contract Management',
    'summary': """Manage Product service based contracts""",
    'author': "Savoir-faire Linux Inc, Serpent Consulting Services Pvt. Ltd.,\
    Odoo Community Association (OCA)",
    'website': 'www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'depends': ['sale', 'account_voucher'],
    'data': [
        'security/contract_isp_security.xml',
        'security/ir.model.access.csv',
        'wizard/activate_contract_service.xml',
        'views/contract_isp_view.xml',
        'views/contract_isp_data.xml',
        'views/contract_isp_workflow.xml',
    ],
    'installable': True,
    'application': False,
}
