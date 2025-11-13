#include "fast_mesh_updater.h"
#include <cmath>
#include <chrono>
#include <sstream>

namespace qixotic::tendroids {

FastMeshUpdater::FastMeshUpdater() 
    : version_("0.2.0-computation") {
}

FastMeshUpdater::~FastMeshUpdater() = default;

std::string FastMeshUpdater::get_version() const {
    return version_;
}

std::string FastMeshUpdater::get_mode() const {
    return "Pure Computation (C++ math, Python USD)";
}

size_t FastMeshUpdater::compute_tube_vertices(
    const float* base_vertices,
    float* output_vertices,
    size_t vertex_count,
    float time,
    float wave_speed,
    float amplitude,
    float frequency
) {
    auto start = std::chrono::high_resolution_clock::now();
    
    // Simple breathing wave: radial displacement based on Y position
    for (size_t i = 0; i < vertex_count; ++i) {
        size_t idx = i * 3;
        float x = base_vertices[idx];
        float y = base_vertices[idx + 1];
        float z = base_vertices[idx + 2];
        
        // Wave travels up the tube (based on Y)
        float wave_phase = y * frequency + time * wave_speed;
        float scale = 1.0f + amplitude * std::sin(wave_phase);
        
        // Apply radial scaling (XZ plane)
        output_vertices[idx] = x * scale;
        output_vertices[idx + 1] = y;  // Y unchanged
        output_vertices[idx + 2] = z * scale;
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration<double, std::milli>(end - start).count();
    
    total_calls_++;
    total_vertices_ += vertex_count;
    total_time_ms_ += duration;
    
    return vertex_count;
}

size_t FastMeshUpdater::batch_compute_vertices(
    const float* base_vertices,
    float* output_vertices,
    size_t num_tubes,
    size_t verts_per_tube,
    float time,
    float wave_speed,
    float amplitude,
    float frequency
) {
    auto start = std::chrono::high_resolution_clock::now();
    
    size_t total_verts = num_tubes * verts_per_tube;
    
    // Process all tubes in a tight loop for cache efficiency
    for (size_t tube_idx = 0; tube_idx < num_tubes; ++tube_idx) {
        size_t offset = tube_idx * verts_per_tube * 3;
        
        for (size_t v = 0; v < verts_per_tube; ++v) {
            size_t idx = offset + v * 3;
            
            float x = base_vertices[idx];
            float y = base_vertices[idx + 1];
            float z = base_vertices[idx + 2];
            
            // Wave travels up the tube
            float wave_phase = y * frequency + time * wave_speed;
            float scale = 1.0f + amplitude * std::sin(wave_phase);
            
            // Apply radial scaling
            output_vertices[idx] = x * scale;
            output_vertices[idx + 1] = y;
            output_vertices[idx + 2] = z * scale;
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration<double, std::milli>(end - start).count();
    
    total_calls_++;
    total_vertices_ += total_verts;
    total_time_ms_ += duration;
    
    return total_verts;
}

FastMeshUpdater::PerfStats FastMeshUpdater::get_stats() const {
    PerfStats stats;
    stats.total_calls = total_calls_;
    stats.total_vertices = total_vertices_;
    stats.total_time_ms = total_time_ms_;
    stats.avg_time_ms = total_calls_ > 0 ? total_time_ms_ / total_calls_ : 0.0;
    return stats;
}

void FastMeshUpdater::reset_stats() {
    total_calls_ = 0;
    total_vertices_ = 0;
    total_time_ms_ = 0.0;
}

} // namespace qixotic::tendroids
