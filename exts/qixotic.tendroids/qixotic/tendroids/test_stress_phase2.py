"""
Phase 2 Stress Test - Performance Ceiling Analysis
==================================================

Automated test to find performance limits of current transform-based architecture.

Test Plan:
1. Spawn Tendroids in increments: 15, 20, 25, 30
2. Monitor FPS for 30 seconds at each count with profiling
3. Log performance metrics and degradation curve
4. Identify bottlenecks and breaking points

Usage:
    Run from Omniverse Script Editor or via UI button
"""

import asyncio
import carb
import json
from pathlib import Path
from datetime import datetime


async def run_stress_test(
    test_counts=None,
    duration_seconds=30,
    output_file=None
):
    """
    Run progressive stress test with profiling.
    
    Args:
        test_counts: List of Tendroid counts to test (default: [15, 20, 25, 30])
        duration_seconds: How long to run each test
        output_file: Optional path to save JSON results
    
    Returns:
        Dict with all test results
    """
    from qixotic.tendroids.scene.manager import TendroidSceneManager
    
    if test_counts is None:
        test_counts = [15, 20, 25, 30]
    
    carb.log_info("\n" + "=" * 70)
    carb.log_info("STRESS TEST - Progressive Load Testing with Profiling")
    carb.log_info("=" * 70)
    carb.log_info(f"Test Configuration:")
    carb.log_info(f"  Counts: {test_counts}")
    carb.log_info(f"  Duration: {duration_seconds}s per test")
    carb.log_info(f"  Total Time: ~{len(test_counts) * (duration_seconds + 5) / 60:.1f} minutes")
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'test_runs': []
    }
    
    scene_manager = TendroidSceneManager()
    
    for count in test_counts:
        carb.log_info("\n" + "=" * 70)
        carb.log_info(f"Test: {count} Tendroids")
        carb.log_info("=" * 70)
        
        # Create Tendroids
        spawn_size = int(300 + (count - 15) * 15)
        success = scene_manager.create_tendroids(
            count=count,
            spawn_area=(spawn_size, spawn_size),
            radius_range=(8, 12),
            num_segments=16
        )
        
        if not success:
            carb.log_error(f"Failed to create {count} Tendroids")
            continue
        
        actual_count = scene_manager.get_tendroid_count()
        carb.log_info(f"Created {actual_count} Tendroids")
        
        # Start animation WITH profiling enabled
        scene_manager.start_animation(enable_profiling=True)
        
        carb.log_info(f"Running for {duration_seconds} seconds...")
        
        # Wait for test duration
        await asyncio.sleep(duration_seconds)
        
        # Stop animation and get profile data
        scene_manager.stop_animation()
        profile_data = scene_manager.get_profile_data()
        
        # Record results
        if profile_data:
            test_result = {
                'tendroid_count': count,
                'actual_count': actual_count,
                'duration': duration_seconds,
                'avg_fps': profile_data['avg_fps'],
                'min_fps': profile_data['min_fps'],
                'max_fps': profile_data['max_fps'],
                'samples': len(profile_data['samples']),
                'total_frames': profile_data['total_frames']
            }
            all_results['test_runs'].append(test_result)
            
            carb.log_info(
                f"Result: {profile_data['avg_fps']:.2f} fps avg "
                f"(min: {profile_data['min_fps']:.2f}, max: {profile_data['max_fps']:.2f})"
            )
        
        # Clear for next test
        scene_manager.clear_tendroids()
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    # Analyze results
    _analyze_results(all_results)
    
    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        carb.log_info(f"\nResults saved to: {output_path}")
    
    return all_results


def _analyze_results(results):
    """Print analysis of test results."""
    if not results['test_runs']:
        return
    
    carb.log_info("\n" + "=" * 70)
    carb.log_info("STRESS TEST SUMMARY")
    carb.log_info("=" * 70)
    
    carb.log_info(
        f"\n{'Count':<8} {'Avg FPS':<12} {'Frame Time':<12} "
        f"{'Min FPS':<10} {'Max FPS':<10}"
    )
    carb.log_info("-" * 70)
    
    for run in results['test_runs']:
        count = run['tendroid_count']
        fps = run['avg_fps']
        frame_time = (1000.0 / fps) if fps > 0 else 0
        min_fps = run.get('min_fps', 0)
        max_fps = run.get('max_fps', 0)
        
        carb.log_info(
            f"{count:<8} {fps:<12.2f} {frame_time:<12.2f} "
            f"{min_fps:<10.2f} {max_fps:<10.2f}"
        )
    
    # Calculate degradation
    if len(results['test_runs']) >= 2:
        baseline = results['test_runs'][0]
        worst = results['test_runs'][-1]
        degradation = (
            (baseline['avg_fps'] - worst['avg_fps']) / baseline['avg_fps'] * 100
        )
        
        carb.log_info(f"\nPerformance Degradation: {degradation:.1f}%")
        carb.log_info(
            f"  Baseline: {baseline['avg_fps']:.2f} fps @ "
            f"{baseline['tendroid_count']} Tendroids"
        )
        carb.log_info(
            f"  Worst: {worst['avg_fps']:.2f} fps @ "
            f"{worst['tendroid_count']} Tendroids"
        )
    
    # Headroom calculation
    worst_run = min(results['test_runs'], key=lambda x: x['avg_fps'])
    worst_fps = worst_run['avg_fps']
    current_frame_time = (1000.0 / worst_fps) if worst_fps > 0 else 0
    target_frame_time = 25.0  # 40 fps
    headroom = target_frame_time - current_frame_time
    
    carb.log_info(f"\nFrame Budget Analysis:")
    carb.log_info(f"  Current: {current_frame_time:.2f} ms")
    carb.log_info(f"  Target: {target_frame_time:.2f} ms (40 fps)")
    carb.log_info(
        f"  Headroom: {headroom:.2f} ms "
        f"({headroom/target_frame_time*100:.1f}%)"
    )
    
    if headroom < 0:
        carb.log_info(f"\n  ⚠️  OVER BUDGET - Optimization required before features")
    elif headroom < 2:
        carb.log_info(f"\n  ⚠️  CRITICAL - Complete FastMeshUpdater before features")
    elif headroom < 5:
        carb.log_info(f"\n  ⚠️  LIMITED - Add features cautiously")
    else:
        carb.log_info(f"\n  ✓  GOOD - Headroom available for features")
    
    carb.log_info("=" * 70)


async def run_default_stress_test():
    """Run with default settings (UI button compatible)."""
    output_dir = Path(__file__).parent / "profiling_results"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"stress_test_{timestamp}.json"
    
    await run_stress_test(
        test_counts=[15, 20, 25, 30],
        duration_seconds=30,
        output_file=str(output_file)
    )


if __name__ == "__main__":
    # For Script Editor execution
    asyncio.ensure_future(run_default_stress_test())
