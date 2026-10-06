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

Staging_Migration also restores, on production copies, the active flag the
Studio originals had before the repos took them over (the repo data carries
Clear-DB's flag; production's current one wins), and deletes the duplicates
older installs created (see delete_rebound_copies).
"""
import importlib.util
import json
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


KEEP_ACTIVE = 'staging_adopt.keep_active.'


def restore_production_active(env):
    """staging_adopt recorded [model, id, active] for each adopted Studio record
    whose active flag differs from the repo's; put production's flag back."""
    Param = env['ir.config_parameter'].sudo()
    for param in Param.search([('key', '=like', KEEP_ACTIVE + '%')]):
        restored = 0
        for model, res_id, active in json.loads(param.value or '[]'):
            if model not in env:
                continue
            rec = env[model].sudo().with_context(active_test=False).browse(res_id).exists()
            if rec and rec.active != active:
                rec.active = active
                restored += 1
        _logger.info("Jinasena_All: %s restored production active flag on %d records",
                     param.key[len(KEEP_ACTIVE):], restored)
        param.value = '[]'


PREFIX = 'staging_adopt.rebound_copies.'
# dependants before what they point at
ORDER = ['base.automation', 'ir.cron', 'ir.ui.menu', 'ir.actions.server', 'ir.actions.report', 'ir.actions.act_window',
         'mail.template', 'ir.filters', 'ir.default', 'ir.rule', 'ir.model.access', 'ir.ui.view']


def _still_used(env, rec):
    if rec._name == 'ir.ui.view':
        return bool(rec.with_context(active_test=False).inherit_children_ids)
    if rec._name == 'ir.ui.menu':
        return bool(rec.with_context(active_test=False).child_id)
    if rec._name.startswith('ir.actions.'):
        if 'studio.approval.rule' in env and env['studio.approval.rule'].with_context(active_test=False).search_count(
                [('action_id', '=', rec.id)]):
            return True
        return bool(env['ir.ui.menu'].with_context(active_test=False).search_count(
            [('action', '=', '%s,%d' % (rec._name, rec.id))]))
    return False


def delete_rebound_copies(env):
    """Delete the repo-created duplicates each repo archived after moving its
    xmlid onto the Studio original (staging_adopt.archive_rebound_copies)."""
    cr = env.cr
    Param = env['ir.config_parameter'].sudo()
    IMD = env['ir.model.data'].sudo()
    for param in Param.search([('key', '=like', PREFIX + '%')]):
        copies = json.loads(param.value or '[]')
        copies.sort(key=lambda c: (ORDER.index(c[0]) if c[0] in ORDER else len(ORDER), -c[1]))
        kept, deleted = [], 0
        for model, res_id in copies:
            if model not in env:
                continue
            rec = env[model].sudo().with_context(active_test=False).browse(res_id).exists()
            if not rec:
                continue
            if IMD.search_count([('model', '=', model), ('res_id', '=', res_id)]) or _still_used(env, rec):
                kept.append([model, res_id])
                continue
            try:
                with cr.savepoint():
                    rec.unlink()
                deleted += 1
            except Exception as e:  # noqa: BLE001 - keep it archived, retry next upgrade
                _logger.warning("Jinasena_All: could not delete duplicate %s,%s: %s", model, res_id, e)
                kept.append([model, res_id])
        param.value = json.dumps(kept)
        _logger.info("Jinasena_All: %s deleted %d repo-created duplicates, %d kept archived",
                     param.key[len(PREFIX):], deleted, len(kept))


def post_init_hook(env):
    repair_studio_server_actions(env)
    restore_production_active(env)
