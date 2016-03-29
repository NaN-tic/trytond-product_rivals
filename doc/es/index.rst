Producto. Rivales
#################

Gestiona los precios de tus rivales (la competencia).

* Precio mínimo/máximo de los rivales en el producto
* Rivales (nombre) con sus precios en el producto.

Filtrar precios de los rivales (min/max)
----------------------------------------

Si dispones de la información del precio mínimo/máximo de los rivales,
y desea filtar estos valores, puede diseñar una fórmula para omitir estos
precios y así no se guardarán.

Ejemplo:

min_price > record.cost_price * Decimal(1.10)

En este ejemplo, el mínimo precio es superior al precio de coste * 1.10,
se guardará este precio en el producto.

En el caso de precio máximo, puede usar esta formula:

max_price > record.list_price * Decimal(1.10)
