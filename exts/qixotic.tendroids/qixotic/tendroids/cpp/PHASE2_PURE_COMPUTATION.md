# C++ Pure Computation Integration - Phase 2

## Overview

**Goal**: Get 5-10x performance improvement by moving vertex computation to C++, while keeping USD updates in Python (since Kit SDK doesn't provide C++ USD libraries).

**Architecture**:
```
┌─────────────────┐
│  Python Layer   │
│  - USD updates  │
│  - Scene mgmt   │
└────────┬────────┘
         │ numpy arrays (zero-copy)
┌────────▼────────┐
│   C++ Layer     │
│  - Vertex math  │
│  - Wave compute │
│  - AVX2 SIMD    │
└─────────────────┘
```

## What Was Built

### C++ Components

1. **fast_mesh_updater.h/cpp**
   - `batch_compute_vertices()` - Processes all tubes in one tight loop
   - `compute_tube_vertices()` - Single tube computation
   - Performance tracking with microsecond precision
   - Optimized for cache efficiency

2. **python_bindings.cpp**
   - pybind11 interface for numpy arrays
   - Zero-copy memory sharing between Python/C++
   - Direct pointer access to numpy buffers

3. **CMakeLists.txt**
   - Pure computation mode (no USD dependencies)
   - MSVC optimization flags: `/O2`, `/Ob2`, `/Oi`, `/Ot`, `/GL`, `/fp:fast`, `/arch:AVX2`
   - Link-time code generation (`/LTCG`)

### Python Components

4. **cpp_batch_updater.py**
   - `CppBatchMeshUpdater` class
   - Registers meshes and maintains base geometry
   - Calls C++ for vertex computation
   - Updates USD with computed results

5. **cpp_batch_test_controller.py**
   - Test harness for 15 tube batch
   - Scene creation and animation loop
   - Performance monitoring

6. **test_scenarios.py**
   - Added `BATCH_15_CPP` test phase
   - Configuration: 15 tubes, 16 segments, 12 radial segments

7. **test_window.py**
   - Added "Run C++ Batch 15" button
   - Integrated with existing test UI

## Build Instructions

### Option 1: Quick Build (Recommended)
```batch
cd C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\qixotic\tendroids\cpp
build_quick.bat
```

### Option 2: CLion
1. Open `cpp/` folder in CLion
2. Tools → CMake → Reset Cache and Reload Project
3. Build → Build Project (Ctrl+F9)

### Option 3: Manual
```batch
cd cpp
mkdir _build && cd _build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
cmake --install .
```

## Testing

1. **Build the C++ extension** (see above)
2. **Restart USD Composer** (to load the new .pyd)
3. **Open test window**: Extensions → Qixotic Tendroids → Warp Tests
4. **Click "Run C++ Batch 15"** in the "🎯 C++ Accelerated Tests" section

## Expected Performance

### Baseline (Warp/Python)
- Batch 15: ~4-5 fps
- Per-frame overhead: ~15-20ms

### Target (C++ Computation)
- Batch 15: ~30-60 fps
- Per-frame overhead: ~1-3ms for vertex math
- USD updates: ~10ms (unavoidable Python overhead)

## Performance Monitoring

The C++ updater tracks:
- `total_calls` - Number of update cycles
- `total_vertices` - Total vertices processed
- `total_time_ms` - Cumulative computation time
- `avg_time_ms` - Average time per update

Access via:
```python
stats = cpp_updater.get_stats()
print(f"C++ avg: {stats['avg_time_ms']:.3f}ms")
```

## Next Steps After FPS Testing

If C++ shows good results (~5x speedup):
1. Add CUDA/Warp integration for even faster batch processing
2. Implement proper swept torus geometry in C++
3. Add transparency/material support

If C++ doesn't show sufficient improvement:
1. Fall back to Fabric-only approach (BATCH_15_TUBES)
2. Focus on reducing USD notification overhead
3. Consider frame-skipping strategies

## Key Design Decisions

1. **No USD in C++**: Kit SDK doesn't provide C++ USD libraries, so we use Python for all USD operations
2. **Numpy zero-copy**: Direct memory sharing between Python and C++ for maximum efficiency
3. **Batch processing**: Single C++ call processes all tubes to minimize Python/C++ crossing overhead
4. **AVX2 SIMD**: Enabled for automatic vectorization of vertex math

## Files Modified/Created

### C++ Files
- `cpp/CMakeLists.txt` - Pure computation build configuration
- `cpp/src/fast_mesh_updater.h` - C++ interface
- `cpp/src/fast_mesh_updater.cpp` - Vertex computation implementation
- `cpp/src/python_bindings.cpp` - pybind11 bindings
- `cpp/build_quick.bat` - Quick build script

### Python Files
- `warp_test/cpp_batch_updater.py` - C++ updater wrapper
- `warp_test/cpp_batch_test_controller.py` - Test controller
- `warp_test/test_scenarios.py` - Added BATCH_15_CPP scenario
- `warp_test/test_window.py` - Added C++ test button

## Troubleshooting

### C++ extension not found
- Run `build_quick.bat`
- Restart USD Composer after building
- Check that `fast_mesh_updater.pyd` exists in `qixotic/tendroids/`

### Build errors
- Verify Visual Studio 2022 is installed
- Check Python 3.10 is available
- Ensure pybind11 is installed: `pip install pybind11`

### Runtime errors
- Check Console for "[CppBatchUpdater]" messages
- Verify C++ extension loaded successfully
- Check for version mismatch between .pyd and Python

## Success Criteria

✅ C++ extension compiles without errors
✅ fast_mesh_updater.pyd appears in qixotic/tendroids/
✅ Test window shows "Run C++ Batch 15" button
✅ Test runs without crashes
✅ FPS significantly improved over Batch 15 Tubes baseline

**Current Status**: Ready for FPS testing!
