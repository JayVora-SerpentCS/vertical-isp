.. image:: https://img.shields.io/badge/license-AGPLv3-blue.svg
   :target: https://www.gnu.org/licenses/agpl.html
   :alt: License: AGPL-3

====================
Product Dependencies
====================

Allows products to have other products/categories as dependencies.

* This module is primarily used by the contract_isp_wizard module to create
  product/service packages based on product inter-dependencies.

* It's aim is to provide the basic structure so that other modules can build
  sales wizards with decision trees based on each product dependency tree.

* This module is not related to the manufacturing process or the
  Bill of Materials.

Installation
=============
No external library is used.

Configuration
==============
To configure this module you need to:

* while creating product from Contract service you can include Dependencies in Product form.

Usage
======

This module is for product dependencies.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/158/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/vertical-isp/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
vertical-isp/issues/new?body=module:%20
product_dependencies%0Aversion:%20
9.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Savoirfaire-Linux Inc. <www.savoirfairelinux.com>
* Juan Ignacio Úbeda <juani@aizean.com
* Serpent Consulting Services Pvt. Ltd. <support@serpentcs.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
