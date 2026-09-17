# -*- coding: utf-8 -*-
{
    'name': 'Jinasena : Meta : ERP',
    'version': '17.0.1.0.5',
    'summary': 'Meta-module: installing this pulls all 18 Jinasena companion modules in topological order.',
    'description': """
Jinasena_All — Meta-Module
==========================

Installing this ONE module triggers Odoo to install all 18 Jinasena
companion modules in the correct topological order, resolving all
declared dependencies automatically.

Modules pulled (18):
    - bank-data
    - seed_master_data_and_settings
    - BugFix-Approvals
    - BugFix-Analytics
    - BugFix-HR
    - BugFix-Maintenance
    - BugFix-Accounting
    - BugFix-Custom-Reports
    - BugFix-Stock
    - BugFix-Purchase
    - BugFix-Sales
    - BugFix-MRP
    - BugFix-Project
    - BugFix-Studio-Misc  (runs post_init_hook to restore 9 cross-repo M2M refs)
    - Fix-repair
    - Fix-Repair-Wizard-Nav
    - Jinasena_Local_Purchase
    - Jinasena_Masterdata_Reporting
    - studio_usermodel_migration

Contains no code — only declarative depends. Empty models/, no data
files. Uninstalling this module leaves the companion modules installed
(standard Odoo behavior — reverse deps are not auto-removed).
""",
    'author': 'Jinasena Agricultural Machinery (Pvt) Ltd.',
    'category': 'Extra Tools',
    'license': 'LGPL-3',
    'depends': [
        'bank-data',
        'seed_master_data_and_settings',
        'BugFix-Approvals',
        'BugFix-Analytics',
        'BugFix-HR',
        'BugFix-Maintenance',
        'BugFix-Accounting',
        'BugFix-Custom-Reports',
        'BugFix-Stock',
        'BugFix-Purchase',
        'BugFix-Sales',
        'BugFix-MRP',
        'BugFix-Project',
        'BugFix-Studio-Misc',
        'Fix-repair',
        'Fix-Repair-Wizard-Nav',
        # 'Fix-Repair-Clear_DB' — reference-only mini-module (same 'name'
        # as Fix-repair, only 1 view). Redundant with Fix-repair (full).
        'Jinasena_Local_Purchase',
        'Jinasena_Masterdata_Reporting',  # transitively required by BugFix-Stock/Sales/MRP/Project
        'studio_usermodel_migration',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
