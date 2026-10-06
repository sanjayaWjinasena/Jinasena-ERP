# -*- coding: utf-8 -*-
"""Staging_Migration, every upgrade (runs after all repos reloaded, since
Jinasena_All depends on all of them): put production's active flag back on
the Studio originals the repos took over, then delete the repo-created
duplicates the repos archived (hooks.restore_production_active /
hooks.delete_rebound_copies), then remove what is left of Studio
(hooks.remove_studio). ORM only."""
import importlib.util
import os

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec = importlib.util.spec_from_file_location('jinasena_all_hooks_000', os.path.join(root, 'hooks.py'))
    hooks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hooks)
    env = api.Environment(cr, SUPERUSER_ID, {})
    hooks.restore_production_active(env)
    hooks.delete_rebound_copies(env)
    hooks.remove_studio(env)
