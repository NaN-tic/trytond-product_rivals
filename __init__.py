# This file is part product_rivals module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .rivals import *
from .product import *

def register():
    Pool.register(
        Template,
        ProductAppRivals,
        Product,
        ProductRivals,
        module='product_rivals', type_='model')


