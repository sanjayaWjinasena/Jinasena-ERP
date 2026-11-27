# -*- coding: utf-8 -*-
"""v17.0.1.0.44: run the Studio server-action repairs on databases that
already have Jinasena_All installed (see hooks.py). Idempotent. ORM only."""
import importlib

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    importlib.import_module('odoo.addons.Jinasena_All.hooks').repair_studio_server_actions(env)
