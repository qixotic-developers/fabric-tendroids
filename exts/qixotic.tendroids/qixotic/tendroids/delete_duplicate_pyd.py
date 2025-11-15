"""
Quick Fix - Delete Duplicate .pyd Files NOW
==========================================

Run this immediately to fix the FastMeshUpdater double-import issue.
"""

import os
from pathlib import Path

def delete_duplicates():
    """Delete duplicate .pyd files from build directories."""
    
    base_dir = Path(__file__).parent / "cpp"
    
    duplicate_paths = [
        base_dir / "build-vs2022" / "Release" / "fast_mesh_updater.pyd",
        base_dir / "build-omniverse" / "Release" / "fast_mesh_updater.pyd",
        base_dir / "cmake-build-release" / "fast_mesh_updater.pyd",
    ]
    
    deleted = []
    not_found = []
    errors = []
    
    for pyd_path in duplicate_paths:
        if pyd_path.exists():
            try:
                pyd_path.unlink()
                deleted.append(str(pyd_path))
                print(f"✓ DELETED: {pyd_path}")
            except Exception as e:
                errors.append(f"{pyd_path}: {e}")
                print(f"✗ ERROR deleting {pyd_path}: {e}")
        else:
            not_found.append(str(pyd_path))
            print(f"- Not found: {pyd_path}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Deleted: {len(deleted)}")
    print(f"Not found: {len(not_found)}")
    print(f"Errors: {len(errors)}")
    
    if deleted:
        print("\n⚠ IMPORTANT: RESTART Omniverse Composer now!")
        print("Python has cached the module - restart is required.")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    return len(deleted) > 0

if __name__ == "__main__":
    print("=" * 70)
    print("FastMeshUpdater Quick Fix - Delete Duplicates")
    print("=" * 70)
    print()
    
    success = delete_duplicates()
    
    if success:
        print("\n✓ Cleanup complete - RESTART Omniverse now")
    else:
        print("\n✓ No duplicates found")
