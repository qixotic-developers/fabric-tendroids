"""
GPU Bubble Physics Integration Example

Shows how to modify scene manager to use GPU-accelerated bubble physics.
Copy these patterns into your existing scene/manager.py.
"""

# ============================================================================
# STEP 1: Import GPU bubble system
# ============================================================================

from qixotic.tendroids.v2.bubbles import create_gpu_bubble_system, BubblePhysicsAdapter


# ============================================================================
# STEP 2: Initialize in SceneManager.__init__
# ============================================================================

class SceneManager:
    def __init__(self, stage, config=None):
        # ... existing initialization ...
        
        # NEW: Initialize GPU bubble system
        self.use_gpu_bubbles = True  # Feature flag
        self.gpu_bubble_adapter = None
        
        # Keep existing bubble manager for fallback
        self.bubble_manager = V2BubbleManager(stage, bubble_config)
    
    def _initialize_gpu_bubbles(self):
        """Initialize GPU bubble system after tendroids are created."""
        if not self.use_gpu_bubbles or not self.tendroids:
            return
        
        try:
            self.gpu_bubble_adapter = create_gpu_bubble_system(
                self.tendroids,
                self.bubble_config
            )
            carb.log_info("[GPU] Bubble physics initialized")
        except Exception as e:
            carb.log_error(f"[GPU] Failed to initialize bubbles: {e}")
            self.use_gpu_bubbles = False


# ============================================================================
# STEP 3: Modify spawn_tendroids to initialize GPU
# ============================================================================

def spawn_tendroids(self, count: int, area_size: tuple = (400, 400), 
                   radius_range: tuple = (8.0, 12.0)):
    # ... existing spawn code creates self.tendroids list ...
    
    # After tendroids are created:
    # self.tendroids = [...]  # Your existing spawn logic
    
    # NEW: Initialize GPU bubbles after spawn
    if self.use_gpu_bubbles:
        self._initialize_gpu_bubbles()
    
    carb.log_info(f"[Scene] Spawned {count} tendroids")


# ============================================================================
# STEP 4: Modify _on_update to use GPU path
# ============================================================================

def _on_update(self, dt: float):
    if not self.tendroids:
        return
    
    # Update wave motion
    if self.wave_controller:
        self.wave_controller.update(dt)
        wave_state = self.wave_controller.get_wave_state()
    else:
        wave_state = None
    
    # === GPU BUBBLE PATH ===
    if self.use_gpu_bubbles and self.gpu_bubble_adapter:
        # Update all bubble physics on GPU in one batch
        self.gpu_bubble_adapter.update_gpu(
            dt=dt,
            config=self.bubble_config,
            wave_state=wave_state
        )
        
        # Get results from GPU
        bubble_positions = self.gpu_bubble_adapter.get_bubble_positions()
        bubble_phases = self.gpu_bubble_adapter.get_bubble_phases()
        
        # Update visuals (TODO: move to Fabric in Phase 2)
        self._update_bubble_visuals_from_gpu(bubble_positions, bubble_phases)
    
    # === CPU BUBBLE PATH (fallback) ===
    else:
        self.bubble_manager.update(dt, self.tendroids, self.wave_controller)
    
    # Rest of update logic unchanged
    self._update_stats(dt)


# ============================================================================
# STEP 5: Add helper for visual updates
# ============================================================================

def _update_bubble_visuals_from_gpu(self, positions: dict, phases: dict):
    """
    Update bubble sphere visuals from GPU physics results.
    
    Args:
        positions: Dict[tendroid_name] -> (x, y, z)
        phases: Dict[tendroid_name] -> phase_int
    """
    for name, pos in positions.items():
        # Get bubble state from existing manager
        if name in self.bubble_manager._bubbles:
            state = self.bubble_manager._bubbles[name]
            
            # Update world position
            state.world_pos = list(pos)
            
            # Update visual transform (still uses USD Python API)
            if state.translate_op:
                from pxr import Gf
                state.translate_op.Set(Gf.Vec3d(*pos))
            
            # Handle visibility based on phase
            phase = phases.get(name, 0)
            if phase == 1 and self.bubble_config.hide_until_clear:
                # Rising - hide if configured
                from pxr import UsdGeom
                if state.sphere_prim:
                    UsdGeom.Imageable(state.sphere_prim).MakeInvisible()
            elif phase > 1:
                # Exiting/released - always visible
                from pxr import UsdGeom
                if state.sphere_prim:
                    UsdGeom.Imageable(state.sphere_prim).MakeVisible()


# ============================================================================
# STEP 6: Cleanup on destroy
# ============================================================================

def destroy(self):
    # ... existing cleanup ...
    
    # NEW: Cleanup GPU resources
    if self.gpu_bubble_adapter:
        self.gpu_bubble_adapter.destroy()
        self.gpu_bubble_adapter = None
    
    self.bubble_manager.clear_all()


# ============================================================================
# PERFORMANCE COMPARISON HELPER
# ============================================================================

def benchmark_bubble_systems(self, iterations: int = 1000):
    """
    Compare CPU vs GPU bubble physics performance.
    
    Args:
        iterations: Number of update cycles
    """
    import time
    
    dt = 0.016  # 60fps frame time
    
    # Benchmark CPU
    print(f"[Benchmark] Testing CPU bubble physics...")
    start = time.perf_counter()
    for _ in range(iterations):
        self.bubble_manager.update(dt, self.tendroids, self.wave_controller)
    cpu_time = time.perf_counter() - start
    
    # Benchmark GPU
    if self.gpu_bubble_adapter:
        print(f"[Benchmark] Testing GPU bubble physics...")
        wave_state = self.wave_controller.get_wave_state() if self.wave_controller else None
        start = time.perf_counter()
        for _ in range(iterations):
            self.gpu_bubble_adapter.update_gpu(dt, self.bubble_config, wave_state)
        gpu_time = time.perf_counter() - start
        
        print(f"\n=== Bubble Physics Benchmark ===")
        print(f"Iterations: {iterations}")
        print(f"Tendroids: {len(self.tendroids)}")
        print(f"CPU time: {cpu_time:.3f}s ({cpu_time/iterations*1000:.2f}ms/update)")
        print(f"GPU time: {gpu_time:.3f}s ({gpu_time/iterations*1000:.2f}ms/update)")
        print(f"Speedup: {cpu_time/gpu_time:.1f}x")
    else:
        print("[Benchmark] GPU bubble system not available")


# ============================================================================
# USAGE IN SCRIPT EDITOR
# ============================================================================

"""
# Test GPU bubble physics
scene_mgr = get_tendroid_manager()  # Your existing manager

# Run benchmark
scene_mgr.benchmark_bubble_systems(iterations=1000)

# Expected output:
# CPU time: 400ms (0.40ms/update) for 15 tendroids
# GPU time: 50ms (0.05ms/update) for 15 tendroids
# Speedup: 8.0x
"""
