#include "fast_mesh_updater.h"
#include <sstream>
#include <stdexcept>
#include <vector>
#include <unordered_map>

// USD/USDRT includes - only in implementation file
#ifdef PHASE2_USD_ENABLED
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/mesh.h>
#include <pxr/base/vt/array.h>
#include <pxr/base/gf/vec3f.h>

// USDRT/Fabric includes for high-performance updates
#include <usdrt/Usd.h>
#include <usdrt/SdfPath.h>
#endif


namespace qixotic::tendroids {

// Private implementation (PIMPL pattern to hide USD headers)
class FastMeshUpdater::Impl {
public:
#ifdef PHASE2_USD_ENABLED
    pxr::UsdStageRefPtr usd_stage;
    usdrt::UsdStage* fabric_stage = nullptr;
    
    struct MeshInfo {
        std::string path;
        usdrt::UsdPrim fabric_prim;
        usdrt::UsdAttribute points_attr;
    };
    
    std::vector<MeshInfo> registered_meshes;
    std::unordered_map<std::string, size_t> path_to_index;
#endif
    
    bool stage_attached = false;
};

FastMeshUpdater::FastMeshUpdater() 
    : version_("0.2.0-alpha-phase2"),
      impl_(std::make_unique<Impl>()) {
}

FastMeshUpdater::~FastMeshUpdater() = default;

std::string FastMeshUpdater::get_version() const {
    return version_;
}

int FastMeshUpdater::add_numbers(int a, int b) {
    return a + b;
}

std::vector<float> FastMeshUpdater::echo_array(const std::vector<float>& input) {
    std::vector<float> result;
    result.reserve(input.size());
    
    for (const auto& value : input) {
        result.push_back(value * 2.0f);
    }
    
    return result;
}

std::string FastMeshUpdater::hello_world() const {
    std::ostringstream oss;
    oss << "Hello from C++ FastMeshUpdater v" << version_;
#ifdef PHASE2_USD_ENABLED
    oss << " (USD enabled)";
#else
    oss << " (USD disabled - Phase 1 only)";
#endif
    return oss.str();
}

// Phase 2: USD/Fabric integration

bool FastMeshUpdater::attach_stage(uintptr_t stage_id) {
#ifdef PHASE2_USD_ENABLED
    try {
        // Attach to Fabric stage
        impl_->fabric_stage = usdrt::UsdStage::Attach(stage_id);
        
        if (!impl_->fabric_stage) {
            return false;
        }
        
        impl_->stage_attached = true;
        return true;
    } catch (const std::exception& e) {
        impl_->stage_attached = false;
        return false;
    }
#else
    // Phase 1: USD not compiled in yet
    return false;
#endif
}

bool FastMeshUpdater::register_mesh(const std::string& mesh_path) {
#ifdef PHASE2_USD_ENABLED
    if (!impl_->stage_attached || !impl_->fabric_stage) {
        return false;
    }
    
    try {
        // Get Fabric prim
        auto fabric_prim = impl_->fabric_stage->GetPrimAtPath(
            usdrt::SdfPath(mesh_path.c_str())
        );
        
        if (!fabric_prim || !fabric_prim.IsValid()) {
            return false;
        }
        
        // Get points attribute
        auto points_attr = fabric_prim.GetAttribute("points");
        if (!points_attr) {
            return false;
        }
        
        // Store mesh info
        Impl::MeshInfo info;
        info.path = mesh_path;
        info.fabric_prim = fabric_prim;
        info.points_attr = points_attr;
        
        impl_->path_to_index[mesh_path] = impl_->registered_meshes.size();
        impl_->registered_meshes.push_back(info);
        
        return true;
    } catch (const std::exception& e) {
        return false;
    }
#else
    return false;
#endif
}

bool FastMeshUpdater::update_mesh_vertices(
    const std::string& mesh_path,
    const float* vertices_ptr,
    size_t vertex_count
) {
#ifdef PHASE2_USD_ENABLED
    if (!impl_->stage_attached) {
        return false;
    }
    
    auto it = impl_->path_to_index.find(mesh_path);
    if (it == impl_->path_to_index.end()) {
        return false;
    }
    
    try {
        auto& mesh_info = impl_->registered_meshes[it->second];
        
        // Convert float array to Fabric-compatible format
        // Direct memory manipulation - bypass Python tuple conversion!
        std::vector<std::tuple<float, float, float>> fabric_vertices;
        fabric_vertices.reserve(vertex_count);
        
        for (size_t i = 0; i < vertex_count; ++i) {
            size_t base = i * 3;
            fabric_vertices.emplace_back(
                vertices_ptr[base + 0],
                vertices_ptr[base + 1],
                vertices_ptr[base + 2]
            );
        }
        
        // Set vertices via Fabric API
        mesh_info.points_attr.Set(fabric_vertices);
        
        return true;
    } catch (const std::exception& e) {
        return false;
    }
#else
    return false;
#endif
}

size_t FastMeshUpdater::batch_update_vertices(
    const float* vertices_ptr,
    size_t total_vertices,
    size_t vertices_per_mesh
) {
#ifdef PHASE2_USD_ENABLED
    if (!impl_->stage_attached || impl_->registered_meshes.empty()) {
        return 0;
    }
    
    size_t meshes_updated = 0;
    
    try {
        for (size_t i = 0; i < impl_->registered_meshes.size(); ++i) {
            auto& mesh_info = impl_->registered_meshes[i];
            
            // Calculate offset for this mesh
            size_t start_idx = i * vertices_per_mesh;
            size_t end_idx = start_idx + vertices_per_mesh;
            
            if (end_idx > total_vertices) {
                break;
            }
            
            // Extract vertices for this mesh
            const float* mesh_vertices = vertices_ptr + (start_idx * 3);
            
            // Convert to Fabric format
            std::vector<std::tuple<float, float, float>> fabric_vertices;
            fabric_vertices.reserve(vertices_per_mesh);
            
            for (size_t v = 0; v < vertices_per_mesh; ++v) {
                size_t base = v * 3;
                fabric_vertices.emplace_back(
                    mesh_vertices[base + 0],
                    mesh_vertices[base + 1],
                    mesh_vertices[base + 2]
                );
            }
            
            // Update mesh
            mesh_info.points_attr.Set(fabric_vertices);
            meshes_updated++;
        }
    } catch (const std::exception& e) {
        // Return number of meshes successfully updated before error
    }
    
    return meshes_updated;
#else
    return 0;
#endif
}

void FastMeshUpdater::clear_meshes() {
#ifdef PHASE2_USD_ENABLED
    impl_->registered_meshes.clear();
    impl_->path_to_index.clear();
#endif
}

size_t FastMeshUpdater::get_mesh_count() const {
#ifdef PHASE2_USD_ENABLED
    return impl_->registered_meshes.size();
#else
    return 0;
#endif
}

bool FastMeshUpdater::is_stage_attached() const {
    return impl_->stage_attached;
}

} // namespace qixotic::tendroids
