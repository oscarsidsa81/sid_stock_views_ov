# -*- coding: utf-8 -*-
import json
import re
from odoo import api, SUPERUSER_ID


_FIELD_MAP = {
    # stock.picking
    "x_asignado": "sid_asignado",
    "x_completado": "sid_completado",
    "x_enviar": "sid_enviar",
    "x_modifica": "sid_modifica",
    "x_motivo": "sid_motivo",
    "x_pagina_final": "sid_pagina_final",
    "x_cliente": "sid_cliente",
    "x_studio_pedido_cliente": "sid_pedido_cliente",
    # stock.move / stock.quant / etc (solo donde exista sid_*)
    "x_pasillo": "sid_pasillo",
    "x_alto": "sid_alto",
    "x_lado": "sid_lado",
    "x_largo": "sid_largo",
}

# Reemplaza name="1198" type="action" por name="%(sid_stock_actions_ov.action_1198)d"
_RE_ACTION_BTN = re.compile(r'(\btype="action"[^>]*\bname=")([^"]+)(")', re.IGNORECASE)

def _ensure_action_xmlid(env, action_id):
    """Asegura xmlid sid_stock_actions_ov.action_<id> sobre ir.actions.actions.<id>"""
    IMD = env["ir.model.data"].sudo()
    xml_name = f"action_{action_id}"
    existing = IMD.search([("module", "=", "sid_stock_actions_ov"), ("name", "=", xml_name)], limit=1)
    if existing:
        return f"sid_stock_actions_ov.{xml_name}"
    # Nota: en Odoo los IDs de acciones viven en ir.actions.actions
    # y los registros específicos (ir.actions.server/act_window/...) comparten ese id.
    # Creamos el xmlid apuntando a ir.actions.actions.
    IMD.create({
        "module": "sid_stock_actions_ov",
        "name": xml_name,
        "model": "ir.actions.actions",
        "res_id": int(action_id),
        "noupdate": True,
    })
    return f"sid_stock_actions_ov.{xml_name}"

def _convert_action_names(env, arch):
    def repl(m):
        prefix, name, suffix = m.group(1), m.group(2), m.group(3)
        # numérico
        if name.isdigit():
            xmlid = _ensure_action_xmlid(env, int(name))
            return f'{prefix}%({xmlid})d{suffix}'
        # __export__.xxx -> resolve a res_id y sustituir
        if name.startswith("__export__."):
            imd = env["ir.model.data"].sudo().search([("module", "=", "__export__"), ("name", "=", name.split("__export__.")[1])], limit=1)
            if imd and imd.model == "ir.actions.actions":
                xmlid = _ensure_action_xmlid(env, imd.res_id)
                return f'{prefix}%({xmlid})d{suffix}'
            # si es server action (ir.actions.server), también tiene id de acción en ir.actions.actions (mismo id)
            if imd and imd.model in ("ir.actions.server", "ir.actions.act_window"):
                xmlid = _ensure_action_xmlid(env, imd.res_id)
                return f'{prefix}%({xmlid})d{suffix}'
        return m.group(0)
    return _RE_ACTION_BTN.sub(repl, arch)

def _convert_fields(env, arch, model_name):
    # sustituir solo si el campo destino existe en el modelo
    Model = env[model_name].sudo()
    for src, dst in _FIELD_MAP.items():
        if src in Model._fields and dst in Model._fields:
            arch = re.sub(rf'\bname="{re.escape(src)}"\b', f'name="{dst}"', arch)
            arch = re.sub(rf"\bname='{re.escape(src)}'\b", f"name='{dst}'", arch)
    return arch

def post_init_create_sid_stock_views_ov(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    View = env["ir.ui.view"].sudo()

    # cargar definiciones
    import os
    module_path = os.path.dirname(os.path.dirname(__file__))
    defs_path = os.path.join(module_path, "data", "ov_views.json")
    with open(defs_path, "r", encoding="utf-8") as f:
        defs = json.load(f)

    # Crear nuevas vistas SID y desactivar las OV antiguas (para evitar duplicidad)
    for d in defs:
        ov_name = d["name"]
        model = d["model"]
        vtype = d["type"]
        inherit_name = d.get("inherit_name")
        priority = d.get("priority") or 16
        arch = d["arch_db"] or "<data/>"

        parent = None
        if inherit_name:
            parent = View.search([("name", "=", inherit_name), ("model", "=", model), ("type", "=", vtype)], limit=1)
        if not parent and inherit_name:
            parent = View.search([("name", "=", inherit_name)], limit=1)

        if not parent:
            # si no localizamos el padre, saltamos esta vista (no rompemos instalación)
            continue

        sid_name = ov_name.replace("OV -", "SID -").replace("OV-", "SID-").strip()

        # si ya existe, no duplicar
        exists = View.search([("name", "=", sid_name), ("model", "=", model), ("type", "=", vtype), ("inherit_id", "=", parent.id)], limit=1)
        if exists:
            continue

        arch2 = _convert_fields(env, arch, model)
        arch2 = _convert_action_names(env, arch2)

        new_view = View.create({
            "name": sid_name,
            "type": vtype,
            "model": model,
            "inherit_id": parent.id,
            "mode": "extension",
            "priority": priority,
            "arch_db": arch2,
            "active": True,
        })

        # Asignar xmlid estable para la vista creada
        env["ir.model.data"].sudo().create({
            "module": "sid_stock_views_ov",
            "name": f"view_{new_view.id}",
            "model": "ir.ui.view",
            "res_id": new_view.id,
            "noupdate": True,
        })

    # Desactivar vistas OV antiguas sin xmlid propio (o con __export__)
    to_disable = View.search([("name", "=like", "OV -%"), ("model", "ilike", "stock.")])
    for v in to_disable:
        # si tiene xmlid de módulo real (no __export__), no tocamos
        imd = env["ir.model.data"].sudo().search([("model", "=", "ir.ui.view"), ("res_id", "=", v.id)], limit=1)
        if imd and imd.module not in ("__export__",):
            continue
        v.active = False
