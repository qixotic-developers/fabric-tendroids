"""
Benchmark: Compare deformation methods by measuring execution time

This bypasses VSync by timing the actual compute, not frame rate.
"""

import time

import carb

results = { }


def benchmark_python_loop():
  """Benchmark original Python loop implementation."""
  from qixotic.tendroids.poc import POCController

  poc = POCController()
  poc.start()

  # Warm up
  for _ in range(10):
    poc.bubble.y = 100.0
    poc.tendroid.apply_deformation(poc.deformer, 100.0, 15.0)

  # Benchmark
  iterations = 100
  start = time.perf_counter()
  for i in range(iterations):
    bubble_y = 20.0 + (i % 160)
    poc.tendroid.apply_deformation(poc.deformer, bubble_y, 15.0)
  end = time.perf_counter()

  poc.clear()

  total_ms = (end - start) * 1000
  per_frame_ms = total_ms / iterations
  theoretical_fps = 1000.0 / per_frame_ms

  results['python'] = per_frame_ms
  carb.log_warn(f"  Python loops: {per_frame_ms:.3f} ms/frame ({theoretical_fps:.0f} theoretical fps)")
  return per_frame_ms


def benchmark_numpy():
  """Benchmark NumPy vectorized implementation."""
  from qixotic.tendroids.poc.numpy_controller import NumpyController

  poc = NumpyController()
  poc.start()

  # Warm up
  for _ in range(10):
    poc.tendroid.apply_deformation(100.0, 15.0)

  # Benchmark
  iterations = 100
  start = time.perf_counter()
  for i in range(iterations):
    bubble_y = 20.0 + (i % 160)
    poc.tendroid.apply_deformation(bubble_y, 15.0)
  end = time.perf_counter()

  poc.clear()

  total_ms = (end - start) * 1000
  per_frame_ms = total_ms / iterations
  theoretical_fps = 1000.0 / per_frame_ms

  results['numpy'] = per_frame_ms
  carb.log_warn(f"  NumPy vectorized: {per_frame_ms:.3f} ms/frame ({theoretical_fps:.0f} theoretical fps)")
  return per_frame_ms


def benchmark_warp():
  """Benchmark Warp GPU implementation."""
  try:
    from qixotic.tendroids.poc import WarpController

    poc = WarpController()
    poc.start()

    # Warm up (important for GPU - JIT compile)
    for _ in range(10):
      poc.tendroid.apply_deformation(100.0, 15.0)

    # Benchmark
    iterations = 100
    start = time.perf_counter()
    for i in range(iterations):
      bubble_y = 20.0 + (i % 160)
      poc.tendroid.apply_deformation(bubble_y, 15.0)
    end = time.perf_counter()

    poc.clear()

    total_ms = (end - start) * 1000
    per_frame_ms = total_ms / iterations
    theoretical_fps = 1000.0 / per_frame_ms

    results['warp'] = per_frame_ms
    carb.log_warn(f"  Warp GPU: {per_frame_ms:.3f} ms/frame ({theoretical_fps:.0f} theoretical fps)")
    return per_frame_ms
  except Exception as e:
    carb.log_warn(f"  Warp GPU: FAILED - {e}")
    return None


def run_benchmarks():
  """Run all benchmarks."""
  carb.log_warn("=" * 60)
  carb.log_warn("  DEFORMATION BENCHMARK (100 iterations each)")
  carb.log_warn("  Measuring actual compute time, bypasses VSync")
  carb.log_warn("=" * 60)
  carb.log_warn("")

  benchmark_python_loop()
  benchmark_numpy()
  benchmark_warp()

  carb.log_warn("")
  carb.log_warn("-" * 60)

  if 'python' in results and 'numpy' in results:
    speedup = results['python'] / results['numpy']
    carb.log_warn(f"  NumPy speedup vs Python: {speedup:.1f}x")

  if 'python' in results and 'warp' in results and results['warp']:
    speedup = results['python'] / results['warp']
    carb.log_warn(f"  Warp speedup vs Python: {speedup:.1f}x")

  carb.log_warn("")
  carb.log_warn("  NOTE: VSync caps display at 75fps regardless of compute speed")
  carb.log_warn("=" * 60)


run_benchmarks()
