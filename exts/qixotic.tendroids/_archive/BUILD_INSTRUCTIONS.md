# C++ Extension Build Instructions

## Current Status
The C++ pure computation extension is ready but needs to be built.

## Why C++?
Current bottleneck analysis (from Batch 15 test):
- Warp kernel (GPU): ~1.4ms ✓ Already fast
- Python tuple conversion: ~30ms ✗ **BOTTLENECK**
- Total: ~32ms = 24 fps

C++ will eliminate the tuple conversion, targeting ~33-40 fps.

## Build Method (Use CLion)

### Steps:
1. **Open project in CLion**:
   - File → Open → Browse to: `C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\qixotic\tendroids\cpp`

2. **Configure CMake**:
   - CLion should auto-detect CMakeLists.txt
   - Wait for CMake configuration to complete
   - Check bottom panel for "CMake project loaded successfully"

3. **Build**:
   - Build → Build Project (Ctrl+F9)
   - Or click the hammer icon in toolbar
   - Wait for compilation (~30-60 seconds)

4. **Verify output**:
   - Look for: `fast_mesh_updater.pyd` in build output directory
   - It should be in: `cpp/cmake-build-release/` or similar

5. **Copy to Python directory** (if not auto-installed):
   ```batch
   copy cpp\cmake-build-release\fast_mesh_updater.pyd qixotic\tendroids\
   ```

6. **Restart USD Composer**

7. **Test**:
   - Extensions → Qixotic Tendroids → Warp Tests
   - Click "Run C++ Batch 15"
   - Watch console for: `[CppBatchUpdater] C++ extension loaded successfully`

## Expected Results

**Before (Current - Batch 15)**:
- 24.1 fps (32ms/frame)
- Computation: 1.4ms
- Python tuple conversion: 30ms

**After (C++ Batch 15)**:
- Target: 33-40 fps (~25-30ms/frame)
- Computation: 0.3ms (C++)
- Direct memory write: 5-10ms
- **70-80% improvement over tuple conversion**

## Troubleshooting

### CMake errors
- Ensure Visual Studio 2022 is installed
- Ensure Python 3.10 is in PATH
- Install pybind11: `pip install pybind11`

### Build errors
- Check CLion's "CMake" tab for detailed errors
- Verify Python3_FOUND in CMake output
- Verify pybind11_FOUND in CMake output

### .pyd not found at runtime
- Check file exists: `qixotic\tendroids\fast_mesh_updater.pyd`
- File size should be ~200-500 KB
- Restart Composer after copying file

### Import errors
- Python version mismatch (must be 3.10)
- Architecture mismatch (must be x64)
- Missing MSVC runtime (install Visual C++ redistributables)

## Alternative: Skip C++ for Now

If build issues persist, the current Batch 15 performance (24 fps) is actually pretty good!
Next optimization path would be:
1. Direct GPU memory writes (skip numpy conversion entirely)
2. Reduce USD notification overhead
3. Frame skipping / adaptive update rates

Both paths can get us to 60 fps, just different approaches.
