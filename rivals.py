# This file is part product_rivals module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool
from trytond.config import config
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, Bool
from simpleeval import simple_eval
from trytond.tools import decistmt


__all__ = ['ProductAppRivals']

DIGITS = config.getint('product', 'price_decimal', default=4)
# Add states with third modules
_STATES = {}
_DEPENDS = ['app']


class ProductAppRivals(ModelSQL, ModelView):
    'Product App Rivals'
    __name__ = 'product.app.rivals'

    name = fields.Char('Name', required=True)
    app = fields.Selection('get_app', 'APP')
    app_uri = fields.Char('App URI',
        states={
            'required': Bool(Eval('app')),
        }, depends=['app'])
    app_username = fields.Char('App Username', states=_STATES, depends=_DEPENDS)
    app_password = fields.Char('App Password', states=_STATES, depends=_DEPENDS)
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

    def create_rivals(self, values):
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Rivals = pool.get('product.rivals')

        to_create = []
        to_write = []
        template_write = []
        id_ = self.id

        codes = values.keys()

        for p in Product.search([('code', 'in', codes)]):
            if p.code in values:
                rivals = values[p.code]['rivals']
                product_rivals = {}
                for n in p.rivals:
                    product_rivals[n.name] = n

                for rival in rivals:
                    if self.tax_included:
                        price_w_tax = Decimal(rivals[rival])
                        price = self.get_price_without_tax(p, price_w_tax)
                    else:
                        price = Decimal(rivals[rival])
                        price_w_tax = self.get_price_with_tax(p, price)
                    # TODO write same rival and app?
                    if rival in product_rivals: # write
                        to_write.extend(([product_rivals[rival]], {
                            'price': price,
                            'price_w_tax': price_w_tax,
                            }))
                    else: # create
                        to_create.append({
                            'product': p,
                            'name': rival,
                            'price': price,
                            'price_w_tax': price_w_tax,
                            'app': id_,
                            })

                rival_prices = {}

                # min rivals price
                min_price = values[p.code]['min_price']
                if self.tax_included:
                    min_price = self.get_price_without_tax(p, min_price)
                if min_price and self.formula_min_price:
                        context = self.get_context_formula(p)
                        context['names']['min_price'] = min_price
                        if not simple_eval(decistmt(self.formula_min_price), **context):
                            min_price = None
                if min_price:
                    rival_prices['list_price_min_rival'] = min_price

                # max rivals price
                max_price = values[p.code]['max_price']
                if self.tax_included:
                    max_price = self.get_price_without_tax(p, max_price)
                if max_price and self.formula_max_price:
                        context = self.get_context_formula(p)
                        context['names']['max_price'] = max_price
                        if not simple_eval(decistmt(self.formula_max_price), **context):
                            max_price = None
                if max_price:
                    rival_prices['list_price_max_rival'] = max_price

                # min / max prices (rival prices)
                if rival_prices and p.validate_min_max_price(rival_prices):
                    template_write.extend(([p.template], rival_prices))

        if to_create:
            Rivals.create(to_create)
        if to_write:
            Rivals.write(*to_write)
        if template_write:
            Template.write(*template_write)
