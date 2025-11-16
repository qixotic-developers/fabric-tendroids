"""
Performance Diagnostic Tool for Tendroids

Analyzes the vertex update pipeline to find bottlenecks.
"""

import time
import carb
import warp as wp
import numpy as np
from pxr import Gf, Vt


def profile_data_conversion():
    """Profile the vertex data conversion pipeline."""
    
    # Simulate a typical Tendroid mesh
    num_segments = 16
    radial_res = 16
    num_vertices = (num_segments + 1) * radial_res
    
    carb.log_info("=" * 70)
    carb.log_info(f"Performance Diagnostic: {num_vertices} vertices per Tendroid")
    carb.log_info("=" * 70)
    
    # Create test data
    vertices_data = [(float(i), float(i+1), float(i+2)) for i in range(num_vertices)]
    warp_array = wp.array(vertices_data, dtype=wp.vec3, device="cuda")
    
    iterations = 100
    
    # Test 1: GPU to CPU transfer
    start = time.perf_counter()
    for _ in range(iterations):
        deformed_data = warp_array.numpy()
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / iterations) * 1000
    carb.log_info(f"GPU→CPU transfer (numpy()): {avg_time_ms:.3f} ms/frame")
    
    # Test 2: Current method - numpy to Gf.Vec3f list
    deformed_data = warp_array.numpy()
    start = time.perf_counter()
    for _ in range(iterations):
        gf_list = [Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in deformed_data]
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / iterations) * 1000
    carb.log_info(f"Numpy→Gf.Vec3f list: {avg_time_ms:.3f} ms/frame")
    
    # Test 3: Gf.Vec3f list to Vt.Vec3fArray
    start = time.perf_counter()
    for _ in range(iterations):
        vt_array = Vt.Vec3fArray(gf_list)
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / iterations) * 1000
    carb.log_info(f"Gf.Vec3f list→Vt.Vec3fArray: {avg_time_ms:.3f} ms/frame")
    
    # Test 4: OPTIMIZED - Direct numpy to Vt.Vec3fArray
    start = time.perf_counter()
    for _ in range(iterations):
        deformed_data = warp_array.numpy()
        # Convert numpy array to flat list, then to Vt.Vec3fArray
        vt_array = Vt.Vec3fArray.FromBuffer(deformed_data)
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / iterations) * 1000
    carb.log_info(f"GPU→Vt.Vec3fArray (OPTIMIZED): {avg_time_ms:.3f} ms/frame")
    
    carb.log_info("=" * 70)
    carb.log_info("Analysis per 30 Tendroids:")
    carb.log_info("=" * 70)
    
    # Calculate total overhead for 30 Tendroids
    deformed_data = warp_array.numpy()
    
    # Current method
    t1 = time.perf_counter()
    for _ in range(30):
        gf_list = [Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in deformed_data]
        vt_array = Vt.Vec3fArray(gf_list)
    elapsed_current = (time.perf_counter() - t1) * 1000
    
    # Optimized method  
    t1 = time.perf_counter()
    for _ in range(30):
        vt_array = Vt.Vec3fArray.FromBuffer(deformed_data)
    elapsed_optimized = (time.perf_counter() - t1) * 1000
    
    speedup = elapsed_current / elapsed_optimized if elapsed_optimized > 0 else 0
    
    carb.log_info(f"Current pipeline: {elapsed_current:.2f} ms/frame")
    carb.log_info(f"Optimized pipeline: {elapsed_optimized:.2f} ms/frame")
    carb.log_info(f"Speedup: {speedup:.1f}x")
    carb.log_info(f"FPS impact at 60fps budget: {(elapsed_current - elapsed_optimized) / 16.67 * 100:.1f}% of frame")
    
    carb.log_info("=" * 70)


if __name__ == "__main__":
    profile_data_conversion()
