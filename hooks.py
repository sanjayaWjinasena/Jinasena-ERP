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
        restored, failed = 0, []
        for model, res_id, active in json.loads(param.value or '[]'):
            if model not in env:
                continue
            rec = env[model].sudo().with_context(active_test=False).browse(res_id).exists()
            if rec and rec.active != active:
                try:
                    with env.cr.savepoint():
                        rec.active = active
                    restored += 1
                except Exception as e:  # noqa: BLE001 - e.g. a view that no longer validates
                    failed.append([model, res_id, active])
                    _logger.warning("Jinasena_All: could not restore active=%s on %s,%s: %s", active, model, res_id, e)
        _logger.info("Jinasena_All: %s restored production active flag on %d records, %d failed",
                     param.key[len(KEEP_ACTIVE):], restored, len(failed))
        param.value = json.dumps(failed)


PARKED = 'staging_adopt.parked_views'


def reactivate_parked_views(env):
    """Switch back on the Studio child views the repos archived while rewriting the
    views they took over (staging_adopt._park_studio_children). Runs after every
    repo has loaded, so all fields exist. One savepoint each; failures stay
    archived and listed in the parameter."""
    Param = env['ir.config_parameter'].sudo()
    parked = json.loads(Param.get_param(PARKED) or '[]')
    if not parked:
        return
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    failed = []
    for view in Views.browse(parked).exists():
        if view.active:
            continue
        try:
            with env.cr.savepoint():
                view.active = True
        except Exception as e:  # noqa: BLE001
            failed.append(view.id)
            _logger.warning("Jinasena_All: parked view %s (%s) could not be switched back on: %s", view.id, view.name, e)
    Param.set_param(PARKED, json.dumps(failed))
    _logger.info("Jinasena_All: switched %d parked Studio views back on, %d failed: %s",
                 len(parked) - len(failed), len(failed), failed)


PREFIX = 'staging_adopt.rebound_copies.'
# dependants before what they point at
ORDER = ['studio.approval.rule', 'base.automation', 'ir.cron', 'ir.ui.menu', 'ir.actions.server', 'ir.actions.report', 'ir.actions.act_window',
         'mail.template', 'ir.filters', 'ir.default', 'ir.rule', 'ir.model.access', 'ir.ui.view']


def _still_used(env, rec):
    if rec._name == 'studio.approval.rule':
        return bool(rec.with_context(active_test=False).entry_ids)     # approval history is data
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


# --- remove Studio from production copies --------------------------------------

STUDIO = 'studio_customization'
OURS = ('BugFix', 'Fix-', 'Jinasena', 'studio_usermodel', 'seed_master', 'bank-data')
# dependants before what they point at; fields / models / selections are never deleted (live data)
SWEEP = ['studio.approval.rule', 'base.automation', 'ir.cron', 'ir.ui.menu', 'ir.actions.server', 'ir.actions.report',
         'ir.actions.act_window', 'ir.actions.client', 'mail.template', 'ir.filters', 'ir.default', 'ir.rule',
         'ir.model.access', 'ir.ui.view', 'res.groups']
NEVER_DELETE = ('ir.model', 'ir.model.fields', 'ir.model.fields.selection')
STUDIO_REPORT = 'staging_adopt.studio_removal'


def _replacements(env):
    """(model, production id, create_date) -> repo xmlid, from every installed
    repo's staging_adopt_map.json (built from the SHIPPED_ARTIFACTS report)."""
    out = {}
    for module in env['ir.module.module'].sudo().search([('state', '=', 'installed')]).mapped('name'):
        path = get_module_path(module, display_warning=False)
        path = path and os.path.join(path, 'staging_adopt_map.json')
        if not path or not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            for xmlid, by_model in json.load(f).items():
                for model, sources in by_model.items():
                    for n, created in sources:
                        out.setdefault((model, n, created), '%s.%s' % (module, xmlid))
    return out


def _referring_fields(env, model):
    relations = [model] + (['ir.actions.actions'] if model.startswith('ir.actions.') else [])
    for field in env['ir.model.fields'].sudo().search([
            ('relation', 'in', relations), ('ttype', 'in', ('many2one', 'many2many')), ('store', '=', True)]):
        if field.model not in env or field.model == 'ir.model.data':
            continue
        Model = env[field.model].sudo().with_context(active_test=False)
        if Model._abstract or Model._transient or field.name not in Model._fields:
            continue
        yield Model, field


def _references(env, model, res_id):
    """What (outside ir.model.data) still points at model,res_id."""
    found = []
    for Model, field in _referring_fields(env, model):
        n = Model.search_count([(field.name, '=', res_id)])
        if n:
            found.append('%s.%s (%d)' % (field.model, field.name, n))
    if model.startswith('ir.actions.'):
        n = env['ir.ui.menu'].sudo().with_context(active_test=False).search_count(
            [('action', '=', '%s,%d' % (model, res_id))])
        if n:
            found.append('ir.ui.menu.action (%d)' % n)
    return found


def _migrate_references(env, model, old_id, new_id):
    """Data migration: move every stored many2one / many2many reference (users
    in a group, approval entries, child views, menus, buttons ...) from the
    Studio record to the repo-owned record that replaced it."""
    for Model, field in _referring_fields(env, model):
        recs = Model.search([(field.name, '=', old_id)])
        if recs:
            recs.write({field.name: new_id} if field.ttype == 'many2one'
                       else {field.name: [(3, old_id), (4, new_id)]})
    if model.startswith('ir.actions.'):
        menus = env['ir.ui.menu'].sudo().with_context(active_test=False).search(
            [('action', '=', '%s,%d' % (model, old_id))])
        if menus:
            menus.write({'action': '%s,%d' % (model, new_id)})


def remove_studio(env):
    """Leave nothing owned by Studio on a production copy, carefully.

    * Repo-owned records that still carry their old studio_customization
      xmlid next to the repo's: only the Studio xmlid is removed (the record
      is the repo's now).
    * Records Studio shares with an Odoo module (base, web_studio, ...) and
      records entered by hand (no xmlid / __export__ only): not touched.
    * Pure Studio records (owned by studio_customization only):
        - replaced by a repo record (same production id + create_date in the
          SHIPPED_ARTIFACTS map): their data is migrated first - every
          reference moves to the repo record - then the Studio record is
          deleted;
        - no repo record to migrate to: never deleted (it is production
          functionality the port missed); reported under 'not_ported' to be
          ported.
    * Fields, models and selection values are never deleted (live data); any
      still Studio-only are reported.
    One savepoint per record; full report in ir.config_parameter
    staging_adopt.studio_removal.
    """
    cr = env.cr
    IMD = env['ir.model.data'].sudo()
    repl = _replacements(env)
    report = {'studio_xmlid_removed': 0, 'migrated_then_deleted': {}, 'not_ported': {},
              'kept_after_error': {}, 'never_deleted': {}}
    rows = IMD.search_read([('module', '=', STUDIO)], ['model', 'res_id'])
    owners = {}
    for row in IMD.search_read([('model', 'in', sorted({r['model'] for r in rows}))], ['module', 'model', 'res_id']):
        owners.setdefault((row['model'], row['res_id']), set()).add(row['module'])
    # 1. repo-owned records: drop the Studio xmlid only
    shared = IMD.browse([r['id'] for r in rows
                         if any(m.startswith(OURS) for m in owners.get((r['model'], r['res_id']), ()))])
    report['studio_xmlid_removed'] = len(shared)
    shared.unlink()
    # 2. pure Studio records
    pure = {}
    for r in rows:
        if owners.get((r['model'], r['res_id']), set()) <= {STUDIO, '__export__'}:
            pure.setdefault(r['model'], set()).add(r['res_id'])
    for model in NEVER_DELETE:
        if pure.get(model):
            report['never_deleted'][model] = sorted(pure.pop(model))
    for model in SWEEP + sorted(set(pure) - set(SWEEP)):
        if model not in pure or model not in env:
            continue
        Model = env[model].sudo().with_context(active_test=False)
        for rec in Model.browse(sorted(pure[model], reverse=True)).exists():
            created = rec.create_date.strftime('%Y-%m-%d %H:%M:%S') if rec.create_date else ''
            target = repl.get((model, rec.id, created))
            target = target and env.ref(target, raise_if_not_found=False)
            label = [rec.id, rec.display_name]
            try:
                with cr.savepoint():
                    if model == 'studio.approval.rule':
                        # approval history cannot move to a rule with other settings; adoption handles these
                        report['not_ported'].setdefault(model, []).append(label + ['approval rule: report only'])
                        continue
                    if target and target._name == model and target.id != rec.id:
                        _migrate_references(env, model, rec.id, target.id)
                        rec.unlink()
                        report['migrated_then_deleted'].setdefault(model, []).append(label + [target.id])
                        continue
                    # no repo record to migrate to: not ported yet - never delete working functionality
                    report['not_ported'].setdefault(model, []).append(label + _references(env, model, rec.id))
            except Exception as e:  # noqa: BLE001 - keep it, report it
                report['kept_after_error'].setdefault(model, []).append(label + ['error: %s' % e])
    env['ir.config_parameter'].sudo().set_param(STUDIO_REPORT, json.dumps(report, default=str))
    _logger.info("Jinasena_All remove_studio: Studio xmlid removed from %d repo-owned records; "
                 "migrated then deleted %s; NOT PORTED (kept) %s; kept after error %s; never deleted %s",
                 report['studio_xmlid_removed'],
                 {m: len(v) for m, v in report['migrated_then_deleted'].items()},
                 {m: len(v) for m, v in report['not_ported'].items()},
                 {m: len(v) for m, v in report['kept_after_error'].items()},
                 {m: len(v) for m, v in report['never_deleted'].items()})


def post_init_hook(env):
    repair_studio_server_actions(env)
    reactivate_parked_views(env)
    restore_production_active(env)
    remove_studio(env)
