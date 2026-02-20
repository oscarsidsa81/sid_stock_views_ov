# -*- coding: utf-8 -*-
import json
import re
from odoo import api, SUPERUSER_ID


def _stable_view_xml_name(model, inherit_name, ov_name, vtype, priority):
    """Genera un nombre de xml_id estable (independiente de IDs numéricos de BD)."""
    import hashlib
    key = f"{model}|{inherit_name or ''}|{ov_name}|{vtype}|{priority or ''}".encode("utf-8")
    h = hashlib.sha1(key).hexdigest()[:10]
    m = re.sub(r"[^a-zA-Z0-9]+", "_", (model or "view")).strip("_").lower()
    return f"view_{m}_{h}"


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
    """Devuelve un xmlid resoluble para la acción.

    Preferencia:
      1) Si la acción ya tiene xmlid en cualquier módulo => usarlo (portable).
      2) Si no tiene => crear sid_stock_actions_ov.action_<id> apuntando a ir.actions.actions (fallback).
    """
    IMD = env["ir.model.data"].sudo()
    action_id = int(action_id)

    # 1) ¿Ya existe xmlid en algún módulo?
    existing_any = IMD.search([
        ("res_id", "=", action_id),
        ("model", "in", ["ir.actions.actions", "ir.actions.act_window", "ir.actions.server"]),
    ], limit=1)
    if existing_any:
        return f"{existing_any.module}.{existing_any.name}"

    # 2) Crear fallback propio
    xml_name = f"action_{action_id}"
    existing = IMD.search([("module", "=", "sid_stock_actions_ov"), ("name", "=", xml_name)], limit=1)
    if existing:
        return f"sid_stock_actions_ov.{xml_name}"

    IMD.create({
        "module": "sid_stock_actions_ov",
        "name": xml_name,
        "model": "ir.actions.actions",
        "res_id": action_id,
        "noupdate": True,
    })
    # IMPORTANTÍSIMO: asegurar que el xmlid existe en BD antes de validar la vista
    env.cr.flush()

    return f"sid_stock_actions_ov.{xml_name}"


def _convert_action_names(env, arch):
    def repl(m):
        prefix, name, suffix = m.group(1), m.group(2), m.group(3)

        # Caso: ya viene como referencia por xmlid en formato %(... )d
        # Ej: name="%(__export__.ir_act_window_1025_xxxxx)d"
        if name.startswith('%(') and name.endswith(')d'):
            inner = name[2:-2]
            # __export__.xxx -> resolve a res_id y sustituir
            if inner.startswith('__export__.'):
                export_name = inner.split('__export__.', 1)[1]
                imd = env['ir.model.data'].sudo().search([
                    ('module', '=', '__export__'),
                    ('name', '=', export_name),
                ], limit=1)
                if imd and imd.model in ('ir.actions.actions', 'ir.actions.server', 'ir.actions.act_window'):
                    xmlid = _ensure_action_xmlid(env, imd.res_id)
                    return f'{prefix}%({xmlid})d{suffix}'
            # Si no lo tocamos, devolvemos tal cual
            return m.group(0)
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
    # __file__ apunta al propio hooks.py dentro del addon.
    # NO subir dos niveles (eso nos saca a /home/odoo/src/user) y rompe el path.
    import os
    module_path = os.path.dirname(__file__)
    defs_path = os.path.join(module_path, "data", "ov_views.json")
    with open(defs_path, "r", encoding="utf-8") as f:
        defs = json.load(f)

    # Crear nuevas vistas SID y desactivar las OV antiguas (para evitar duplicidad)
    IMD = env["ir.model.data"].sudo()

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

        # Asignar xmlid estable para la vista creada (NO basado en ID numérico)
        xml_name = _stable_view_xml_name(model, inherit_name, ov_name, vtype, priority)
        if not IMD.search([("module", "=", "sid_stock_views_ov"), ("name", "=", xml_name)], limit=1):
            IMD.create({
                "module": "sid_stock_views_ov",
                "name": xml_name,
                "model": "ir.ui.view",
                "res_id": new_view.id,
                "noupdate": True,
            })

        # asegurar persistencia antes de validar siguientes vistas
        env.cr.flush()

    # Desactivar vistas OV antiguas sin xmlid propio (o con __export__)
    to_disable = View.search([("name", "=like", "OV -%"), ("model", "ilike", "stock.")])
    for v in to_disable:
        # si tiene xmlid de módulo real (no __export__), no tocamos
        imd = env["ir.model.data"].sudo().search([("model", "=", "ir.ui.view"), ("res_id", "=", v.id)], limit=1)
        if imd and imd.module not in ("__export__",):
            continue
        v.active = False
