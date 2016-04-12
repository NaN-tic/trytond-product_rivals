# This file is part product_rivals module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool

from trytond.config import config
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, Bool


__all__ = ['ProductAppRivals']
DIGITS = config.getint('product', 'price_decimal', default=4)


class ProductAppRivals(ModelSQL, ModelView):
    'Product App Rivals'
    __name__ = 'product.app.rivals'

    name = fields.Char('Name', required=True)
    app = fields.Selection('get_app', 'APP')
    app_uri = fields.Char('App URI',
        states={
            'required': Bool(Eval('app')),
        }, depends=['app'])
    scheduler = fields.Boolean('Scheduler',
        help='Active by crons (import)')
    tax_included = fields.Boolean('Tax Included')
    formula_min_price = fields.Char('Formula Min Price',
        help='Eval expression to save minnium rival price')
    formula_max_price = fields.Char('Formula Max Price',
        help='Eval expression to save maximum rival price')

    @classmethod
    def __setup__(cls):
        super(ProductAppRivals, cls).__setup__()
        cls._buttons.update({
            'update_prices': {},
            })

    @staticmethod
    def default_scheduler():
        return True

    @classmethod
    def get_app(cls):
        '''APP Engines'''
        res = [('', '')]
        return res

    @classmethod
    @ModelView.button
    def update_prices(cls, apps):
        for a in apps:
            if hasattr(cls,  'update_prices_%s' % a.app):
                update_prices = getattr(a,  'update_prices_%s' % a.app)
                update_prices()

    @classmethod
    def cron_rivals(cls):
        '''Cron rivals'''
        apps = cls.search([
            ('scheduler', '=', True),
            ])
        cls.update_prices(apps)
        return True

    def get_context_formula(self, record):
        return {
            'names': {
                'record': record,
            },
            'functions': {
                'Decimal': Decimal,
                },
            }

    def get_price_without_tax(self, product, price_with_tax):
        Tax = Pool().get('account.tax')
        taxes = [Tax(t) for t in product.get_taxes('customer_taxes_used')]
        tax_amount = Tax.reverse_compute(price_with_tax, taxes)
        return tax_amount.quantize(Decimal(str(10.0 ** -DIGITS)))

    def get_price_with_tax(self, product, price_without_tax):
        Tax = Pool().get('account.tax')
        taxes = [Tax(t) for t in product.get_taxes('customer_taxes_used')]
        tax_amount = Tax.compute(taxes, price_without_tax, 1.0)
        tax_amount = sum([t['amount'] for t in tax_amount], Decimal('0.0'))
        return price_without_tax + tax_amount
