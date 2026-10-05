# -*- coding: utf-8 -*-
"""Install-time repair of the Studio server actions broken by the 15->17
migration (v17.0.1.0.44).

BugFix-Studio-Misc ships three idempotent repairs as migration scripts:
  17.0.0.0.109  object_write: back-fill update_path from update_field_id
                (KeyError '' in _traverse_path when the action fires)
  17.0.0.0.110  object_write: evaluation_type='equation' for Python values
  17.0.0.0.111  next_activity: user field / responsible user from Clear-DB
Migration scripts only run on UPGRADE, so every fresh install (dev envs and
production copies alike) kept those actions broken: e.g. saving a Purchase
Request on the staging copy raised KeyError '' in action 4669.

This meta module depends on every Jinasena repo and so loads last; running
the same three scripts here covers the actions of every repo (BugFix-
Maintenance included, which loads after BugFix-Studio-Misc). Each script
touches only rows that are still broken. ORM only.
"""
import importlib.util
import logging
import os

from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)

REPAIRS = ('17.0.0.0.109', '17.0.0.0.110', '17.0.0.0.111')


def repair_studio_server_actions(env):
    base = get_module_path('BugFix-Studio-Misc')
    if not base:
        _logger.warning("Jinasena_All: BugFix-Studio-Misc not found; server-action repair skipped")
        return
    for version in REPAIRS:
        path = os.path.join(base, 'migrations', version, 'post-migrate.py')
        if not os.path.exists(path):
            _logger.warning("Jinasena_All: repair script %s missing", path)
            continue
        spec = importlib.util.spec_from_file_location('jinasena_all_repair_%s' % version.replace('.', '_'), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(env.cr, 'jinasena_all_install')   # any non-empty version runs it
        _logger.info("Jinasena_All: ran server-action repair %s", version)


def post_init_hook(env):
    repair_studio_server_actions(env)
