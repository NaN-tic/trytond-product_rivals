# This file is part product_rivals module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import suite as test_suite
from trytond.modules.company.tests import create_company, set_company
from trytond.pool import Pool
from decimal import Decimal


class ProductRivalsTestCase(ModuleTestCase):
    'Test Product Rivals module'
    module = 'product_rivals'

    @with_transaction()
    def test_rivals_price(self):
        '''Calculate price with tax and without tax'''
        pool = Pool()
        AccountType = pool.get('account.account.type')
        Account = pool.get('account.account')
        Tax = pool.get('account.tax')
        UomCategory = pool.get('product.uom.category')
        ProductUom = pool.get('product.uom')
        Template = pool.get('product.template')
        App = pool.get('product.app.rivals')

        company = create_company()
        with set_company(company):
            account_type, = AccountType.create([{
                    'name': 'Account Type',
                    'company': company.id,
                    }])
            account, = Account.create([{
                    'name': 'Account',
                    'kind': 'other',
                    'type': account_type.id,
                    'company': company.id,
                    }])
            tax, = Tax.create([{
                    'name': 'Tax %s' % Decimal('.10'),
                    'description': 'Tax %s' % Decimal('.10'),
                    'type': 'percentage',
                    'rate': Decimal('.10'),
                    'invoice_account': account.id,
                    'credit_note_account': account.id,
                    }])

            category, = UomCategory.create([{
                    'name': 'Units',
                    }])
            unit, = ProductUom.create([{
                    'name': 'Unit',
                    'symbol': 'u',
                    'category': category.id,
                    'rate': 1,
                    'factor': 1,
                    }])

            list_price = Decimal(20.5)
            product, = Template.create([{
                    'name': 'P1',
                    'type': 'goods',
                    'list_price': list_price,
                    'cost_price': Decimal(10),
                    'default_uom': unit.id,
                    'customer_taxes': [('add', [tax.id])],
                    'products': [('create', [{
                                    'code': '1',
                                    }])]
                    }])

            app = App()
            app.name = 'Test APP'

            without_tax = app.get_price_without_tax(product, list_price)
            self.assertEqual(without_tax, Decimal('18.6364'))

            with_tax = app.get_price_with_tax(product, list_price)
            self.assertEqual(with_tax, Decimal('22.5500'))


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            ProductRivalsTestCase))
    return suite
