{
    "name": "Jinasena : Meta : ERP",
    "version": "17.0.1.0.44",
    "summary": "Meta-module: installing this pulls all 18 Jinasena companion modules; "
    "upgrading it cascades to every declared dep.",
    "author": "Jinasena Agricultural Machinery (Pvt) Ltd.",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "depends": [
        "bank-data",
        "seed_master_data_and_settings",
        "BugFix-Approvals",
        "BugFix-Analytics",
        "BugFix-HR",
        "BugFix-Maintenance",
        "BugFix-Accounting",
        "BugFix-Custom-Reports",
        "BugFix-Stock",
        "BugFix-Purchase",
        "BugFix-Sales",
        "BugFix-MRP",
        "BugFix-Project",
        "BugFix-Studio-Misc",
        "Fix-repair",
        "Fix-Repair-Wizard-Nav",
        # 'Fix-Repair-Clear_DB' — reference-only mini-module (same 'name'
        # as Fix-repair, only 1 view). Redundant with Fix-repair (full).
        "Jinasena_Local_Purchase",
        # transitively required by BugFix-Stock/Sales/MRP/Project
        "Jinasena_Masterdata_Reporting",
        "studio_usermodel_migration",
        # 3rd-party; needs `dropbox` Python pkg (shipped via sibling
        # requirements.txt). Depending on it here means a cascade upgrade
        # of Jinasena_All installs it + unblocks the dropbox.auth.code
        # model / view / ACL audit items.
        "auto_database_backup",
        # NOTE: Jinasena_TestDataMigration + Jinasena_MasterData_* are
        # test-env-only modules. Never depend on them from this meta.
    ],
    "data": [],
    # v17.0.1.0.44: repair Studio server actions broken by the 15->17 migration
    # on install too (BugFix-Studio-Misc's repairs only ran on upgrade).
    "post_init_hook": "post_init_hook",
    "application": False,
}
