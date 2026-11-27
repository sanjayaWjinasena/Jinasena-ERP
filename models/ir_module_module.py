# -*- coding: utf-8 -*-
"""Cascade-upgrade override for the Jinasena_All meta module.

When the user clicks Upgrade on Jinasena_All (or triggers
button_immediate_upgrade from anywhere), expand the recordset to include
every currently-installed module in the meta's declared depends list, so a
single click reloads data files across the whole Jinasena stack.

Rationale: Odoo's stock upgrade cascades DOWNWARD to reverse-deps, not
UPWARD to deps. This override closes that gap for the specific case of the
Jinasena_All meta.
"""
from odoo import models
from odoo.modules.module import load_information_from_description_file

META_MODULE = 'Jinasena_All'


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def _jinasena_all_expand(self):
        """If this recordset includes Jinasena_All, return the same set
        plus every installed module in its declared depends list.
        Otherwise return self unchanged."""
        if not any(m.name == META_MODULE for m in self):
            return self
        try:
            manifest = load_information_from_description_file(META_MODULE)
        except Exception:
            return self
        dep_names = list(manifest.get('depends') or [])
        if not dep_names:
            return self
        installed_deps = self.sudo().search([
            ('name', 'in', dep_names),
            ('state', '=', 'installed'),
        ])
        return (self | installed_deps).with_context(self.env.context)

    def button_immediate_upgrade(self):
        return super(IrModuleModule, self._jinasena_all_expand()).button_immediate_upgrade()

    def button_upgrade(self):
        return super(IrModuleModule, self._jinasena_all_expand()).button_upgrade()
