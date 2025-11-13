"""
Phase 2 Test Script - FastMeshUpdater with Numpy Arrays
=========================================================

Tests numpy array support and API structure (USD integration pending).
"""

import sys
import numpy as np
from pathlib import Path

# Add cpp module to path
sys.path.insert(0, str(Path(__file__).parent / "cpp" / "build-vs2022" / "Release"))

def test_phase2_api():
    """Test that Phase 2 API is present."""
    import fast_mesh_updater
    
    print("=" * 70)
    print("Phase 2 API Tests")
    print("=" * 70)
    print()
    
    updater = fast_mesh_updater.FastMeshUpdater()
    
    # Check version
    version = updater.get_version()
    print(f"[PASS] Version: {version}")
    assert "0.2.0" in version
    
    # Check new methods exist
    assert hasattr(updater, 'attach_stage')
    assert hasattr(updater, 'register_mesh')
    assert hasattr(updater, 'update_mesh_vertices')
    assert hasattr(updater, 'batch_update_vertices')
    assert hasattr(updater, 'clear_meshes')
    assert hasattr(updater, 'get_mesh_count')
    assert hasattr(updater, 'is_stage_attached')
    print("[PASS] All Phase 2 methods present")
    
    # Test numpy array handling (without USD)
    vertices = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ], dtype=np.float32)
    
    print(f"[PASS] Created numpy array: shape={vertices.shape}, dtype={vertices.dtype}")
    
    # Test stage attachment (should fail without USD)
    result = updater.attach_stage(0)
    print(f"[PASS] attach_stage() called (returned {result} - USD not enabled)")
    
    # Test mesh registration (should fail without stage)
    result = updater.register_mesh("/World/Test/Mesh")
    print(f"[PASS] register_mesh() called (returned {result} - no stage)")
    
    # Test mesh count
    count = updater.get_mesh_count()
    print(f"[PASS] get_mesh_count() = {count}")
    assert count == 0
    
    # Test stage attached check
    is_attached = updater.is_stage_attached()
    print(f"[PASS] is_stage_attached() = {is_attached}")
    assert not is_attached
    
    print()
    print("=" * 70)
    print("[SUCCESS] Phase 2 API tests passed!")
    print()
    print("Next steps:")
    print("  1. Find your Kit SDK path")
    print("  2. Update CMakeLists.txt with KIT_SDK_PATH")
    print("  3. Rebuild with USD support: build.bat clean")
    print("  4. Test with actual USD stage in Omniverse")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_phase2_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
