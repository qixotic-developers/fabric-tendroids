"""
FastMeshUpdater Diagnostic - Fix "PerfStats already registered" Error
====================================================================

This script diagnoses and fixes the double-import issue causing:
"generic_type: type 'PerfStats' is already registered!"

Issue: Multiple copies of fast_mesh_updater.pyd exist, causing double imports
Fix: Ensure only ONE copy in the main extension directory is used
"""

import sys
import os
from pathlib import Path
import carb

def find_all_pyd_files():
    """Locate all fast_mesh_updater.pyd files."""
    extension_root = Path(__file__).parent
    pyd_files = list(extension_root.rglob("fast_mesh_updater.pyd"))
    return pyd_files

def check_sys_path_for_duplicates():
    """Check if sys.path has multiple directories with the .pyd file."""
    conflicts = []
    for path_entry in sys.path:
        pyd_path = Path(path_entry) / "fast_mesh_updater.pyd"
        if pyd_path.exists():
            conflicts.append(str(pyd_path))
    return conflicts

def diagnose_fastmesh_issue():
    """Run complete diagnostic."""
    carb.log_info("=" * 70)
    carb.log_info("[FastMeshDiagnostic] Checking for duplicate .pyd files")
    carb.log_info("=" * 70)
    
    # Find all .pyd files
    all_pyds = find_all_pyd_files()
    carb.log_info(f"\n[FastMeshDiagnostic] Found {len(all_pyds)} .pyd files:")
    for pyd in all_pyds:
        carb.log_info(f"  - {pyd}")
    
    # Check sys.path
    conflicts = check_sys_path_for_duplicates()
    if conflicts:
        carb.log_warn(f"\n[FastMeshDiagnostic] ⚠ Found {len(conflicts)} .pyd files in sys.path:")
        for conflict in conflicts:
            carb.log_warn(f"  - {conflict}")
    
    # Check if already imported
    if 'fast_mesh_updater' in sys.modules:
        module = sys.modules['fast_mesh_updater']
        carb.log_warn(f"\n[FastMeshDiagnostic] Module already loaded from:")
        carb.log_warn(f"  - {module.__file__}")
    
    # Recommendation
    carb.log_info("\n" + "=" * 70)
    carb.log_info("[FastMeshDiagnostic] SOLUTION")
    carb.log_info("=" * 70)
    
    extension_dir = Path(__file__).parent
    main_pyd = extension_dir / "fast_mesh_updater.pyd"
    
    if main_pyd.exists():
        carb.log_info(f"✓ Main .pyd exists: {main_pyd}")
        carb.log_info("\n  This is the ONLY file that should exist.")
        carb.log_info("  Delete all .pyd files in build directories:")
        for pyd in all_pyds:
            if pyd != main_pyd:
                carb.log_info(f"    - DELETE: {pyd}")
    else:
        carb.log_error(f"✗ Main .pyd missing: {main_pyd}")
        carb.log_info("  Copy the latest .pyd from build directory to:")
        carb.log_info(f"    {main_pyd}")
    
    carb.log_info("\n" + "=" * 70)
    
    return {
        'all_pyds': all_pyds,
        'conflicts': conflicts,
        'main_pyd': main_pyd,
        'main_exists': main_pyd.exists()
    }

def auto_fix_duplicates():
    """
    Automatically fix duplicate .pyd issue.
    
    WARNING: This will DELETE build directory .pyd files!
    Only keeps the main extension directory copy.
    """
    carb.log_warn("\n[FastMeshDiagnostic] AUTO-FIX MODE")
    carb.log_warn("This will DELETE duplicate .pyd files in build directories")
    
    extension_dir = Path(__file__).parent
    main_pyd = extension_dir / "fast_mesh_updater.pyd"
    
    all_pyds = find_all_pyd_files()
    deleted = []
    
    for pyd in all_pyds:
        if pyd != main_pyd:
            try:
                pyd.unlink()
                deleted.append(str(pyd))
                carb.log_info(f"  ✓ Deleted: {pyd}")
            except Exception as e:
                carb.log_error(f"  ✗ Failed to delete {pyd}: {e}")
    
    if deleted:
        carb.log_info(f"\n[FastMeshDiagnostic] Deleted {len(deleted)} duplicate files")
        carb.log_info("  Restart Omniverse for changes to take effect")
    else:
        carb.log_info("\n[FastMeshDiagnostic] No duplicates found to delete")
    
    return deleted

if __name__ == "__main__":
    diagnose_fastmesh_issue()
