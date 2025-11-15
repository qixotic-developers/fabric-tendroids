"""
FastMeshUpdater Fix - Delete Duplicates (Works from anywhere)
============================================================

Automatically finds the extension directory and deletes duplicate .pyd files.
"""

import os
import sys
from pathlib import Path

def find_extension_dir():
    """Find the qixotic.tendroids extension directory."""
    
    # Check if we're already in the extension
    for path in sys.path:
        path_obj = Path(path)
        if 'qixotic.tendroids' in str(path_obj):
            # Found it - navigate to extension root
            parts = path_obj.parts
            try:
                idx = parts.index('qixotic.tendroids')
                ext_dir = Path(*parts[:idx+1])
                if ext_dir.exists():
                    return ext_dir
            except (ValueError, IndexError):
                pass
    
    # Try common locations
    common_paths = [
        Path(r'C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids'),
        Path.home() / 'Dev' / 'Omniverse' / 'fabric-tendroids' / 'exts' / 'qixotic.tendroids',
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    return None

def delete_duplicates(ext_dir):
    """Delete duplicate .pyd files from build directories."""
    
    cpp_dir = ext_dir / 'qixotic' / 'tendroids' / 'cpp'
    
    if not cpp_dir.exists():
        print(f"ERROR: cpp directory not found at {cpp_dir}")
        return False
    
    print(f"Extension directory: {ext_dir}")
    print(f"C++ directory: {cpp_dir}")
    print()
    
    duplicate_paths = [
        cpp_dir / "build-vs2022" / "Release" / "fast_mesh_updater.pyd",
        cpp_dir / "build-omniverse" / "Release" / "fast_mesh_updater.pyd",
        cpp_dir / "cmake-build-release" / "fast_mesh_updater.pyd",
    ]
    
    deleted = []
    not_found = []
    errors = []
    
    for pyd_path in duplicate_paths:
        print(f"Checking: {pyd_path}")
        if pyd_path.exists():
            try:
                pyd_path.unlink()
                deleted.append(str(pyd_path))
                print(f"  ✓ DELETED")
            except Exception as e:
                errors.append(f"{pyd_path}: {e}")
                print(f"  ✗ ERROR: {e}")
        else:
            not_found.append(str(pyd_path))
            print(f"  - Not found")
    
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
    
    # Also check the main .pyd
    main_pyd = ext_dir / 'qixotic' / 'tendroids' / 'fast_mesh_updater.pyd'
    print(f"\nMain .pyd file: {main_pyd}")
    if main_pyd.exists():
        print(f"  ✓ Exists (size: {main_pyd.stat().st_size} bytes)")
    else:
        print(f"  ✗ MISSING - This is a problem!")
        print(f"     Copy from build directory after deleting duplicates")
    
    return len(deleted) > 0

if __name__ == "__main__":
    print("=" * 70)
    print("FastMeshUpdater Fix - Delete Duplicate .pyd Files")
    print("=" * 70)
    print()
    
    ext_dir = find_extension_dir()
    
    if not ext_dir:
        print("ERROR: Could not find qixotic.tendroids extension directory")
        print("\nSearched in sys.path and common locations.")
        print("Please run this script from within the extension directory.")
        sys.exit(1)
    
    success = delete_duplicates(ext_dir)
    
    if success:
        print("\n" + "=" * 70)
        print("✓ CLEANUP COMPLETE")
        print("=" * 70)
        print("\nNEXT STEPS:")
        print("1. CLOSE Omniverse Composer completely")
        print("2. RESTART Omniverse Composer")
        print("3. Load Tendroids extension")
        print("4. Check console for: [TendroidBuilder] FastMeshUpdater loaded successfully")
        print("5. Run stress test again")
    else:
        print("\n✓ No duplicates found to delete")
        print("\nThe PerfStats error may be caused by something else.")
        print("Try restarting Omniverse Composer anyway.")
