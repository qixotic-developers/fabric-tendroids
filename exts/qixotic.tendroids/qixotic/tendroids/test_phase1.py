"""
Phase 1 Test Script - FastMeshUpdater C++ Extension
====================================================

Verifies basic pybind11 functionality and Windows + CLion + VS2022 toolchain.
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Add Python DLL directory to PATH for module loading."""
    python_dir = Path(sys.executable).parent
    python_dll_dir = str(python_dir)
    
    # Add Python directory to PATH if not already there
    if python_dll_dir not in os.environ['PATH']:
        os.environ['PATH'] = python_dll_dir + os.pathsep + os.environ['PATH']
        print(f"Added Python directory to PATH: {python_dll_dir}")

def find_cpp_module():
    """Locate the compiled C++ module."""
    cpp_dir = Path(__file__).parent / "cpp"
    
    search_paths = [
        # MSVC build directories (prioritize these)
        cpp_dir / "build-msvc" / "Release",
        cpp_dir / "build-msvc" / "Debug",
        cpp_dir / "build-msvc",
        # CLion build directories with Release subdirectory
        cpp_dir / "cmake-build-release" / "Release",
        cpp_dir / "cmake-build-release" / "Debug",
        cpp_dir / "cmake-build-release",
        cpp_dir / "cmake-build-relwithdebinfo" / "Release",
        cpp_dir / "cmake-build-relwithdebinfo",
        cpp_dir / "cmake-build-debug" / "Debug",
        cpp_dir / "cmake-build-debug",
        # Standard build directories
        cpp_dir / "_build" / "Release",
        cpp_dir / "_build" / "Debug",
        cpp_dir / "_build",
        cpp_dir / "build" / "Release",
        cpp_dir / "build" / "Debug",
        cpp_dir / "build",
        cpp_dir,
    ]
    
    for path in search_paths:
        if path.exists():
            pyd_file = path / "fast_mesh_updater.pyd"
            if pyd_file.exists():
                print(f"Found module at: {pyd_file}")
                sys.path.insert(0, str(path))
                return True
    
    print("\nSearched in:")
    for path in search_paths:
        exists = "[OK]" if path.exists() else "[--]"
        print(f"  {exists} {path}")
    
    return False

def test_import():
    """Test that we can import the C++ module."""
    try:
        import fast_mesh_updater
        print("[PASS] Successfully imported fast_mesh_updater module")
        print(f"  Module version: {fast_mesh_updater.__version__}")
        return fast_mesh_updater
    except ImportError as e:
        print(f"[FAIL] Failed to import: {e}")
        print("\nTroubleshooting:")
        print("  This usually means a DLL is missing. Common causes:")
        print("  1. Python DLL not found (should be fixed by this script)")
        print("  2. Visual C++ Redistributable missing")
        print("  3. Build configuration mismatch (Debug vs Release)")
        print("\nTry:")
        print("  1. Install Visual C++ Redistributable 2022")
        print("  2. Rebuild in Release mode instead of Debug")
        print("  3. Check CLion build output for errors")
        return None

def test_module_function(module):
    """Test module-level function."""
    try:
        result = module.hello_world()
        expected = "Hello from C++ FastMeshUpdater module!"
        if result == expected:
            print(f"[PASS] hello_world() = '{result}'")
            return True
        else:
            print(f"[FAIL] hello_world() returned unexpected: '{result}'")
            return False
    except Exception as e:
        print(f"[FAIL] hello_world() failed: {e}")
        return False

def test_class_creation(module):
    """Test class instantiation."""
    try:
        updater = module.FastMeshUpdater()
        print("[PASS] FastMeshUpdater instance created")
        return updater
    except Exception as e:
        print(f"[FAIL] Failed to create instance: {e}")
        return None

def test_get_version(updater):
    """Test simple string return."""
    try:
        version = updater.get_version()
        print(f"[PASS] get_version() = '{version}'")
        return True
    except Exception as e:
        print(f"[FAIL] get_version() failed: {e}")
        return False

def test_hello_world_method(updater):
    """Test instance method that returns string."""
    try:
        result = updater.hello_world()
        if "Hello from C++" in result and "FastMeshUpdater" in result:
            print(f"[PASS] hello_world() = '{result}'")
            return True
        else:
            print(f"[FAIL] Unexpected hello_world() result: '{result}'")
            return False
    except Exception as e:
        print(f"[FAIL] hello_world() failed: {e}")
        return False

def test_add_numbers(updater):
    """Test integer parameters and return."""
    try:
        result = updater.add_numbers(42, 58)
        expected = 100
        if result == expected:
            print(f"[PASS] add_numbers(42, 58) = {result}")
            return True
        else:
            print(f"[FAIL] add_numbers(42, 58) = {result}, expected {expected}")
            return False
    except Exception as e:
        print(f"[FAIL] add_numbers() failed: {e}")
        return False

def test_echo_array(updater):
    """Test list/vector passing between Python and C++."""
    try:
        input_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = updater.echo_array(input_data)
        expected = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        if result == expected:
            print(f"[PASS] echo_array({input_data}) = {result}")
            return True
        else:
            print(f"[FAIL] echo_array() = {result}, expected {expected}")
            return False
    except Exception as e:
        print(f"[FAIL] echo_array() failed: {e}")
        return False

def main():
    """Run all Phase 1 tests."""
    print("=" * 70)
    print("FastMeshUpdater Phase 1 Tests - Hello World")
    print("=" * 70)
    print()
    
    # Setup Python DLL path
    setup_python_path()
    print()
    
    # Find and add module to path
    if not find_cpp_module():
        print("\n[FAIL] Could not locate compiled C++ module")
        print("  Please build the extension first")
        return False
    
    print()
    
    # Test import
    module = test_import()
    if not module:
        return False
    
    print()
    print("-" * 70)
    print("Testing module-level functions...")
    print("-" * 70)
    
    test_module_function(module)
    
    print()
    print("-" * 70)
    print("Testing FastMeshUpdater class...")
    print("-" * 70)
    
    # Test class
    updater = test_class_creation(module)
    if not updater:
        return False
    
    print()
    
    # Test all methods
    all_passed = True
    all_passed &= test_get_version(updater)
    all_passed &= test_hello_world_method(updater)
    all_passed &= test_add_numbers(updater)
    all_passed &= test_echo_array(updater)
    
    print()
    print("=" * 70)
    if all_passed:
        print("[SUCCESS] All tests PASSED - Phase 1 complete!")
        print()
        print("Your C++ extension is working!")
        print()
        print("Next steps:")
        print("  - Phase 2: Add numpy array support")
        print("  - Phase 3: USD/Fabric stage integration")
        print("  - Phase 4: Batch vertex updates")
    else:
        print("[FAILED] Some tests FAILED - check output above")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
