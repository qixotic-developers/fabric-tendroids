"""
Diagnostic script to check Omniverse Python and FastMeshUpdater status

Run this in USD Composer Script Editor to see what's happening.
"""

import sys
import os
import carb


def diagnose_fast_mesh_updater():
    """Print diagnostic information about FastMeshUpdater availability."""
    
    carb.log_info("=" * 80)
    carb.log_info("FastMeshUpdater Diagnostic")
    carb.log_info("=" * 80)
    
    # Python version
    carb.log_info(f"Python version: {sys.version}")
    carb.log_info(f"Python executable: {sys.executable}")
    
    # Check sys.path
    carb.log_info("\nPython sys.path:")
    for i, p in enumerate(sys.path[:5]):  # First 5 entries
        carb.log_info(f"  [{i}] {p}")
    
    # Expected .pyd location
    cpp_dir = r"C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\qixotic\tendroids\cpp"
    
    carb.log_info(f"\nChecking for .pyd files in: {cpp_dir}")
    
    # Check different build directories
    build_dirs = [
        os.path.join(cpp_dir, "build-omniverse", "Release"),
        os.path.join(cpp_dir, "build-vs2022", "Release"),
        os.path.join(cpp_dir, "cmake-build-release"),
        cpp_dir  # Root of cpp directory
    ]
    
    for build_dir in build_dirs:
        pyd_path = os.path.join(build_dir, "fast_mesh_updater.pyd")
        exists = os.path.exists(pyd_path)
        carb.log_info(f"  {pyd_path}")
        carb.log_info(f"    Exists: {exists}")
        
        if exists:
            # Try to get file info
            try:
                size = os.path.getsize(pyd_path)
                carb.log_info(f"    Size: {size:,} bytes")
            except Exception as e:
                carb.log_info(f"    Error getting size: {e}")
    
    # Try importing
    carb.log_info("\nAttempting to import fast_mesh_updater...")
    
    # Add build directory to path temporarily
    test_dir = os.path.join(cpp_dir, "build-vs2022", "Release")
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)
        carb.log_info(f"  Added to sys.path: {test_dir}")
    
    try:
        import fast_mesh_updater
        carb.log_info("  ✅ Import successful!")
        carb.log_info(f"  Module location: {fast_mesh_updater.__file__}")
        carb.log_info(f"  Module version: {fast_mesh_updater.__version__}")
        
        # Try creating instance
        updater = fast_mesh_updater.FastMeshUpdater()
        carb.log_info(f"  ✅ FastMeshUpdater instance created!")
        carb.log_info(f"  Version: {updater.get_version()}")
        
    except ImportError as e:
        carb.log_error(f"  ❌ Import failed: {e}")
        carb.log_info("\n  This usually means:")
        carb.log_info("    1. Module built against wrong Python version")
        carb.log_info("    2. Missing DLL dependencies")
        carb.log_info("    3. Module not found in sys.path")
        
    except Exception as e:
        carb.log_error(f"  ❌ Error: {e}")
    
    carb.log_info("=" * 80)


if __name__ == "__main__":
    diagnose_fast_mesh_updater()
