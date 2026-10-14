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

Information
-----------

* Technical name: ``Jinasena_All``
* Version: ``17.0.1.0.44``
* Depends on: ``bank-data``, ``seed_master_data_and_settings``, ``BugFix-Approvals``, ``BugFix-Analytics``, ``BugFix-HR``, ``BugFix-Maintenance``, ``BugFix-Accounting``, ``BugFix-Custom-Reports``, ``BugFix-Stock``, ``BugFix-Purchase``, ``BugFix-Sales``, ``BugFix-MRP``, ``BugFix-Project``, ``BugFix-Studio-Misc``, ``Fix-repair``, ``Fix-Repair-Wizard-Nav``, ``Jinasena_Local_Purchase``, ``Jinasena_Masterdata_Reporting``, ``studio_usermodel_migration``, ``auto_database_backup``
* Author: Jinasena Agricultural Machinery (Pvt) Ltd.
* License: LGPL-3

Further documentation
---------------------

* Functional documentation: ``Functional_Documentation.md``
* Change history: ``CHANGELOG.md``
