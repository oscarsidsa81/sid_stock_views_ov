# SID Stock Views OV

Módulo de **Odoo 15** para personalizar vistas, acciones y menús del flujo de almacén de SID.

Su objetivo principal es mejorar la operativa diaria de logística con:

- vistas de `stock.picking` y `stock.move` adaptadas a operación,
- accesos directos para escenarios de asignación concretos,
- acciones servidor para navegar entre albaranes relacionados (origen/destino),
- filtros y agrupaciones orientados a trabajo en curso.

---

## 1) Alcance funcional

Este módulo **no crea nuevos modelos**: se centra en interfaz y navegación sobre modelos estándar de inventario (`stock.picking`, `stock.move`, `stock.quant`).

Incluye:

- herencia de la vista formulario de albarán (`stock.view_picking_form`),
- nuevas vistas árbol y búsqueda para albaranes y movimientos,
- acciones de ventana para listados operativos,
- menús de acceso rápido bajo **Inventario > Asignación**,
- dos acciones servidor para abrir albaranes previos/siguientes enlazados por movimientos.

---

## 2) Dependencias

Dependencias declaradas en el manifiesto:

- `stock`
- `sid_stock_actions_ov`
- `sid_stock_base`
- `oct_customize_reports`

> Si alguna dependencia no está instalada, Odoo no permitirá instalar este módulo.

---

## 3) Qué cambia en la interfaz

### 3.1 Formulario de albarán (`stock.picking`)

Se extiende la vista de formulario para mostrar/ajustar campos clave operativos:

- asignación (`sid_asignado`),
- cliente y pedido de cliente (`sid_cliente`, `pedido_cliente`),
- resumen de avance (`qty_done_pct`, `sid_completado`),
- ajustes visuales y decoraciones en líneas de operación,
- controles de edición/lectura según estado.

También se incorporan en líneas de operaciones:

- columna de familia,
- widget toggle para actividad,
- orden por `id`,
- resaltado visual según completitud/cancelación.

### 3.2 Lista principal de albaranes (Madrid entregas/devoluciones)

Se define una vista árbol optimizada para planificación diaria, con columnas de:

- prioridad,
- avance porcentual,
- resumen de alcance,
- flags de envío/completado,
- asignado,
- pedido, cliente, fechas, transportista, pesos y estado.

Incluye botones directos en cada fila para abrir:

- **Albaranes origen**,
- **Albaranes destino**.

### 3.3 Vista y búsqueda de movimientos (`stock.move`)

Se agrega una vista árbol dedicada a asignación por línea con:

- campos de referencia/pedido/familia/actividad,
- edición masiva (`multi_edit`),
- badge de estado,
- decoración de retraso cuando la fecha ya venció.

Y una búsqueda con filtros prácticos:

- Ready / To Do / Done,
- Incoming / Outgoing / Inventory,
- líneas con actividades,
- agrupaciones por producto, pedido, albarán, ubicaciones, estado y fechas.

### 3.4 Búsqueda extendida en albaranes

Se amplía la búsqueda estándar de picking para añadir:

- búsqueda por cliente SID (`sid_cliente`),
- búsqueda/agrupación por pedido-grupo (`group_id`),
- searchpanel por transportista y dirección.

### 3.5 Vista de certificados

Se incorpora una vista árbol específica para el flujo de **Certificados**, reutilizable desde su acción dedicada.

---

## 4) Acciones servidor incluidas

### `sid_act_server_picking_origen`
Devuelve los albaranes **precedentes** al actual, siguiendo la relación:

- `move_lines.move_dest_ids.picking_id`

### `sid_act_server_picking_destino`
Devuelve los albaranes **siguientes** al actual, siguiendo la relación:

- `move_lines.move_orig_ids.picking_id`

Ambas acciones abren una ventana `tree,form` filtrada por los IDs encontrados.

---

## 5) Acciones de ventana y menús

### Menú raíz

- **Asignación** (hijo de `Inventario`).

### Entradas principales

1. Madrid: Picking / Asignación por línea
2. Madrid: Picking y Recepciones
3. Madrid: Entregas y Devoluciones
4. Puertollano: Entregas y Devoluciones
5. Certificados
6. Devoluciones y Errores (en reportes de almacén)

Cada opción aplica dominios concretos por estado, tipo de operación y/o equipo comercial para mostrar únicamente el conjunto relevante para cada operación.

---

## 6) Instalación

1. Copiar el módulo en el `addons_path` de Odoo.
2. Actualizar lista de aplicaciones.
3. Instalar **SID Stock Views OV**.

Desde línea de comandos (ejemplo):

```bash
./odoo-bin -d <base_datos> -u sid_stock_views_ov
```

---

## 7) Recomendaciones de uso

- Validar primero en entorno de pruebas, ya que se alteran vistas críticas de logística.
- Revisar permisos/grupos de usuarios de Inventario antes de liberar a producción.
- Si se cambian `xml_id` de otros módulos dependientes, ajustar dominios y referencias de este módulo.

---

## 8) Estructura del módulo

```text
sid_stock_views_ov/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── server_actions.xml
│   └── view_actions.xml
├── views/
│   └── stock_picking_views_ov.xml
└── static/
    └── description/
        ├── icon.png
        └── index.html
```

---

## 9) Versión

Versión actual declarada: **15.0.1.1.0**.

