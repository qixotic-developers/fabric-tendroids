#ifndef FAST_MESH_UPDATER_H
#define FAST_MESH_UPDATER_H

#include <string>
#include <vector>
#include <cstdint>
#include <unordered_map>

// pybind11 for Python integration
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;


namespace qixotic::tendroids {

/**
 * FastMeshUpdater - High-performance vertex updates using Python USD via C-API
 * 
 * Phase 2C: Hybrid approach
 * - C++ handles numpy array processing (zero-copy)
 * - C++ calls Python USD via pybind11 (faster than pure Python)
 * - Eliminates tuple conversion overhead
 */
class FastMeshUpdater {
public:
    FastMeshUpdater();
    ~FastMeshUpdater();
    
    // Version info
    [[nodiscard]] std::string get_version() const;
    [[nodiscard]] std::string get_mode() const;
    
    // === USD Integration Methods (Hybrid C++/Python) ===
    
    /**
     * Attach to USD stage
     * Stores Python stage reference for later use
     * @param stage Python USD stage object
     * @return True if successful
     */
    bool attach_stage(py::object stage);
    
    /**
     * Check if stage is attached
     */
    [[nodiscard]] bool is_stage_attached() const;
    
    /**
     * Register mesh for vertex updates
     * Caches Python points attribute for fast updates
     * @param mesh_path USD prim path (e.g., "/World/Tendroid_01/mesh")
     * @return True if successful
     */
    bool register_mesh(const std::string& mesh_path);
    
    /**
     * Get number of registered meshes
     */
    [[nodiscard]] size_t get_mesh_count() const;
    
    /**
     * Update mesh vertices from numpy array (CRITICAL METHOD)
     * C++ converts numpy to Vt.Vec3fArray, calls Python USD Set()
     * @param mesh_path USD prim path
     * @param vertices_np Numpy array shape (N, 3) dtype float32
     * @return True if successful
     */
    bool update_mesh_vertices(
        const std::string& mesh_path,
        py::array_t<float> vertices_np
    );
    
    // === Compute Methods (Existing - kept for compatibility) ===
    
    /**
     * Batch compute vertices for multiple tubes
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
     * Single tube vertex computation
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
    
    // === Performance Stats ===
    
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
    
    // USD integration (Python objects via pybind11)
    py::object stage_;  // Python USD stage
    std::unordered_map<std::string, py::object> mesh_points_;  // Python USD attributes
    bool stage_attached_ = false;
    
    // Performance tracking
    size_t total_calls_ = 0;
    size_t total_vertices_ = 0;
    double total_time_ms_ = 0.0;
};

} // namespace qixotic::tendroids


#endif // FAST_MESH_UPDATER_H
