from . import models

# Exponer el hook en el namespace del paquete para que Odoo pueda resolver
# post_init_hook="post_init_create_sid_stock_views_ov" vía getattr(py_module, ...)
from .hooks import post_init_create_sid_stock_views_ov  # noqa: F401
