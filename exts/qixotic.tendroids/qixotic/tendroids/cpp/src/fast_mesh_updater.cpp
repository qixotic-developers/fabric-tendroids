#include "fast_mesh_updater.h"
#include <cmath>
#include <chrono>
#include <sstream>

namespace qixotic::tendroids {

FastMeshUpdater::FastMeshUpdater() 
    : version_("0.3.0-hybrid-python-usd"),
      stage_(py::none()) {
}

FastMeshUpdater::~FastMeshUpdater() = default;

std::string FastMeshUpdater::get_version() const {
    return version_;
}

std::string FastMeshUpdater::get_mode() const {
    return "Hybrid C++ (numpy processing + Python USD via C-API)";
}

// === USD Integration Methods ===

bool FastMeshUpdater::attach_stage(py::object stage) {
    try {
        if (stage.is_none()) {
            return false;
        }
        
        stage_ = stage;
        stage_attached_ = true;
        return true;
    } catch (...) {
        return false;
    }
}

bool FastMeshUpdater::is_stage_attached() const {
    return stage_attached_ && !stage_.is_none();
}

bool FastMeshUpdater::register_mesh(const std::string& mesh_path) {
    if (!stage_attached_ || stage_.is_none()) {
        return false;
    }
    
    try {
        // Import USD modules
        py::module_ usdGeom = py::module_::import("pxr.UsdGeom");
        py::module_ sdf = py::module_::import("pxr.Sdf");
        
        // Get mesh prim: stage.GetPrimAtPath(Sdf.Path(mesh_path))
        py::object sdf_path = sdf.attr("Path")(mesh_path);
        py::object prim = stage_.attr("GetPrimAtPath")(sdf_path);
        
        if (prim.attr("IsValid")().cast<bool>() == false) {
            return false;
        }
        
        // Get mesh geometry: UsdGeom.Mesh(prim)
        py::object mesh = usdGeom.attr("Mesh")(prim);
        
        // Get points attribute: mesh.GetPointsAttr()
        py::object points_attr = mesh.attr("GetPointsAttr")();
        
        if (points_attr.attr("IsValid")().cast<bool>() == false) {
            return false;
        }
        
        // Cache the attribute for fast lookup
        mesh_points_[mesh_path] = points_attr;
        return true;
        
    } catch (const py::error_already_set& e) {
        return false;
    } catch (...) {
        return false;
    }
}

size_t FastMeshUpdater::get_mesh_count() const {
    return mesh_points_.size();
}

bool FastMeshUpdater::update_mesh_vertices(
    const std::string& mesh_path,
    py::array_t<float> vertices_np
) {
    // Find cached points attribute
    auto it = mesh_points_.find(mesh_path);
    if (it == mesh_points_.end()) {
        return false;
    }
    
    py::object& points_attr = it->second;
    
    try {
        // Get numpy array info
        auto buf = vertices_np.request();
        if (buf.ndim != 2 || buf.shape[1] != 3) {
            return false;  // Expected (N, 3) shape
        }
        
        // Import Vt module
        py::module_ vt = py::module_::import("pxr.Vt");
        
        // Create Vt.Vec3fArray from numpy
        // CRITICAL: This is done in C++ with zero-copy via buffer protocol
        py::object vt_vec3f_array_class = vt.attr("Vec3fArray");
        
        // Use FromNumpy or FromBuffer if available, otherwise convert manually
        py::object vt_vertices;
        
        try {
            // Try direct buffer protocol (fastest)
            vt_vertices = vt_vec3f_array_class.attr("FromBuffer")(vertices_np);
        } catch (...) {
            // Fallback: Convert via Python list (slower but works)
            size_t num_verts = buf.shape[0];
            float* data = static_cast<float*>(buf.ptr);
            
            py::list vert_list;
            for (size_t i = 0; i < num_verts; ++i) {
                py::tuple vert = py::make_tuple(
                    data[i * 3 + 0],
                    data[i * 3 + 1],
                    data[i * 3 + 2]
                );
                vert_list.append(vert);
            }
            vt_vertices = vt_vec3f_array_class(vert_list);
        }
        
        // Call Python USD Set() method
        // points_attr.Set(vt_vertices)
        points_attr.attr("Set")(vt_vertices);
        
        return true;
        
    } catch (const py::error_already_set& e) {
        return false;
    } catch (...) {
        return false;
    }
}

// === Compute Methods (Existing) ===

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


// === Python Bindings ===

PYBIND11_MODULE(fast_mesh_updater, m) {
    m.doc() = "Fast mesh vertex updater with hybrid C++/Python USD";
    
    py::class_<qixotic::tendroids::FastMeshUpdater>(m, "FastMeshUpdater")
        .def(py::init<>())
        .def("get_version", &qixotic::tendroids::FastMeshUpdater::get_version)
        .def("get_mode", &qixotic::tendroids::FastMeshUpdater::get_mode)
        
        // USD integration methods (Hybrid approach)
        .def("attach_stage", &qixotic::tendroids::FastMeshUpdater::attach_stage,
             py::arg("stage"),
             "Attach to USD stage (Python object)")
        .def("is_stage_attached", &qixotic::tendroids::FastMeshUpdater::is_stage_attached,
             "Check if stage is attached")
        .def("register_mesh", &qixotic::tendroids::FastMeshUpdater::register_mesh,
             py::arg("mesh_path"),
             "Register mesh for vertex updates")
        .def("get_mesh_count", &qixotic::tendroids::FastMeshUpdater::get_mesh_count,
             "Get number of registered meshes")
        .def("update_mesh_vertices", &qixotic::tendroids::FastMeshUpdater::update_mesh_vertices,
             py::arg("mesh_path"),
             py::arg("vertices_np"),
             "Update mesh vertices from numpy array (hybrid speedup)")
        
        // Compute methods (existing - kept for compatibility)
        .def("compute_tube_vertices", &qixotic::tendroids::FastMeshUpdater::compute_tube_vertices,
             py::arg("base_vertices"),
             py::arg("output_vertices"),
             py::arg("vertex_count"),
             py::arg("time"),
             py::arg("wave_speed"),
             py::arg("amplitude"),
             py::arg("frequency"))
        .def("batch_compute_vertices", &qixotic::tendroids::FastMeshUpdater::batch_compute_vertices,
             py::arg("base_vertices"),
             py::arg("output_vertices"),
             py::arg("num_tubes"),
             py::arg("verts_per_tube"),
             py::arg("time"),
             py::arg("wave_speed"),
             py::arg("amplitude"),
             py::arg("frequency"))
        .def("get_stats", &qixotic::tendroids::FastMeshUpdater::get_stats)
        .def("reset_stats", &qixotic::tendroids::FastMeshUpdater::reset_stats);
    
    // Expose PerfStats struct
    py::class_<qixotic::tendroids::FastMeshUpdater::PerfStats>(m, "PerfStats")
        .def_readonly("total_calls", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_calls)
        .def_readonly("total_vertices", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_vertices)
        .def_readonly("total_time_ms", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_time_ms)
        .def_readonly("avg_time_ms", &qixotic::tendroids::FastMeshUpdater::PerfStats::avg_time_ms);
}
