#ifndef FAST_MESH_UPDATER_H
#define FAST_MESH_UPDATER_H

#include <string>
#include <vector>
#include <cstdint>


namespace qixotic::tendroids {

/**
 * FastMeshUpdater - High-performance vertex computation
 * 
 * Phase 2: Pure computation mode
 * - C++ handles all vertex math/deformation
 * - Python handles USD updates
 * - Numpy arrays for zero-copy data transfer
 */
class FastMeshUpdater {
public:
    FastMeshUpdater();
    ~FastMeshUpdater();
    
    // Version info
    [[nodiscard]] std::string get_version() const;
    [[nodiscard]] std::string get_mode() const;
    
    /**
     * Batch compute vertices for multiple tubes
     * Computes breathing wave deformation on GPU-style batch
     * 
     * @param base_vertices Input vertices [num_tubes * verts_per_tube * 3]
     * @param output_vertices Output buffer (same size as input)
     * @param num_tubes Number of tubes in batch
     * @param verts_per_tube Vertices per tube
     * @param time Current animation time
     * @param wave_speed Speed of wave propagation
     * @param amplitude Wave amplitude
     * @param frequency Wave frequency
     * @return Number of vertices processed
     */
    size_t batch_compute_vertices(
        const float* base_vertices,
        float* output_vertices,
        size_t num_tubes,
        size_t verts_per_tube,
        float time,
        float wave_speed,
        float amplitude,
        float frequency
    );
    
    /**
     * Single tube vertex computation (for testing)
     */
    size_t compute_tube_vertices(
        const float* base_vertices,
        float* output_vertices,
        size_t vertex_count,
        float time,
        float wave_speed,
        float amplitude,
        float frequency
    );
    
    /**
     * Get performance stats
     */
    struct PerfStats {
        size_t total_calls = 0;
        size_t total_vertices = 0;
        double total_time_ms = 0.0;
        double avg_time_ms = 0.0;
    };
    
    [[nodiscard]] PerfStats get_stats() const;
    void reset_stats();
    
private:
    std::string version_;
    
    // Performance tracking
    size_t total_calls_ = 0;
    size_t total_vertices_ = 0;
    double total_time_ms_ = 0.0;
};

} // namespace qixotic::tendroids


#endif // FAST_MESH_UPDATER_H
