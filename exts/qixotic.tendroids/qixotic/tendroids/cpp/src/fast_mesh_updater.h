#ifndef FAST_MESH_UPDATER_H
#define FAST_MESH_UPDATER_H

#include <string>
#include <vector>
#include <memory>
#include <cstdint>


namespace qixotic::tendroids {

/**
 * FastMeshUpdater - High-performance mesh vertex updates
 * 
 * Phase 1: Simple test functions to verify toolchain ✅
 * Phase 2: USD/Fabric integration with numpy arrays (CURRENT)
 * Phase 3: Batch updates for multiple meshes
 */
class FastMeshUpdater {
public:
    FastMeshUpdater();
    ~FastMeshUpdater();
    
    // Phase 1: Simple test functions ✅
    [[nodiscard]] std::string get_version() const;
    [[nodiscard]] std::string hello_world() const;
    static int add_numbers(int a, int b);
    static std::vector<float> echo_array(const std::vector<float> &input);
    
    // Phase 2: USD/Fabric integration
    
    /**
     * Attach to USD stage by stage ID
     * @param stage_id Stage pointer as uintptr_t from omni.usd.get_context().get_stage_id()
     * @return true if attachment successful
     */
    bool attach_stage(uintptr_t stage_id);
    
    /**
     * Register a mesh for fast updates
     * @param mesh_path USD prim path (e.g., "/World/BatchTest/Tube_00")
     * @return true if mesh registered successfully
     */
    bool register_mesh(const std::string& mesh_path);
    
    /**
     * Update single mesh vertices from raw float pointer
     * @param mesh_path USD prim path
     * @param vertices_ptr Pointer to float array [x,y,z,x,y,z,...]
     * @param vertex_count Number of vertices (array size = vertex_count * 3)
     * @return true if update successful
     */
    bool update_mesh_vertices(
        const std::string& mesh_path,
        const float* vertices_ptr,
        size_t vertex_count
    );
    
    /**
     * Batch update all registered meshes from contiguous memory
     * @param vertices_ptr Pointer to float array for ALL meshes
     * @param total_vertices Total vertices across all meshes
     * @param vertices_per_mesh Vertices in each individual mesh
     * @return Number of meshes updated
     */
    size_t batch_update_vertices(
        const float* vertices_ptr,
        size_t total_vertices,
        size_t vertices_per_mesh
    );
    
    /**
     * Clear all registered meshes
     */
    void clear_meshes();
    
    /**
     * Get number of registered meshes
     */
    [[nodiscard]] size_t get_mesh_count() const;
    
    /**
     * Check if stage is attached
     */
    [[nodiscard]] bool is_stage_attached() const;
    
private:
    std::string version_;
    
    // Forward declare implementation details to avoid exposing USD headers
    class Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace qixotic::tendroids


#endif // FAST_MESH_UPDATER_H
