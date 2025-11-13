#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "fast_mesh_updater.h"

namespace py = pybind11;

PYBIND11_MODULE(fast_mesh_updater, m) {
    m.doc() = "FastMeshUpdater C++ Extension for Tendroids\n\n"
              "Phase 1: Basic pybind11 integration ✅\n"
              "Phase 2: USD/Fabric with numpy arrays (CURRENT)\n"
              "High-performance mesh vertex updates bypassing Python tuple conversion";
    
    // Bind the FastMeshUpdater class
    py::class_<qixotic::tendroids::FastMeshUpdater>(m, "FastMeshUpdater")
        .def(py::init<>(), 
             "Create a new FastMeshUpdater instance")
        
        // Phase 1: Test functions
        .def("get_version", 
             &qixotic::tendroids::FastMeshUpdater::get_version,
             "Get the version string of the C++ extension")
        
        .def_static("add_numbers", 
             &qixotic::tendroids::FastMeshUpdater::add_numbers,
             "Add two integers and return the result",
             py::arg("a"), 
             py::arg("b"))
        
        .def_static("echo_array", 
             &qixotic::tendroids::FastMeshUpdater::echo_array,
             "Echo back an array with each value doubled (tests data transfer)",
             py::arg("input"))
        
        .def("hello_world",
             &qixotic::tendroids::FastMeshUpdater::hello_world,
             "Return a greeting message")
        
        // Phase 2: USD/Fabric integration
        .def("attach_stage",
             &qixotic::tendroids::FastMeshUpdater::attach_stage,
             "Attach to USD stage by stage ID",
             py::arg("stage_id"))
        
        .def("register_mesh",
             &qixotic::tendroids::FastMeshUpdater::register_mesh,
             "Register a mesh for fast updates",
             py::arg("mesh_path"))
        
        .def("update_mesh_vertices",
             [](qixotic::tendroids::FastMeshUpdater& self,
                const std::string& mesh_path,
                py::array_t<float> vertices) {
                 // Get numpy array info
                 py::buffer_info buf = vertices.request();
                 
                 if (buf.ndim != 2 || buf.shape[1] != 3) {
                     throw std::runtime_error("Vertices must be Nx3 array");
                 }
                 
                 // Direct pointer access - zero copy!
                 float* ptr = static_cast<float*>(buf.ptr);
                 size_t vertex_count = buf.shape[0];
                 
                 return self.update_mesh_vertices(mesh_path, ptr, vertex_count);
             },
             "Update single mesh from numpy array (zero-copy)",
             py::arg("mesh_path"),
             py::arg("vertices"))
        
        .def("batch_update_vertices",
             [](qixotic::tendroids::FastMeshUpdater& self,
                py::array_t<float> vertices,
                size_t vertices_per_mesh) {
                 // Get numpy array info
                 py::buffer_info buf = vertices.request();
                 
                 if (buf.ndim != 2 || buf.shape[1] != 3) {
                     throw std::runtime_error("Vertices must be Nx3 array");
                 }
                 
                 // Direct pointer access - zero copy!
                 float* ptr = static_cast<float*>(buf.ptr);
                 size_t total_vertices = buf.shape[0];
                 
                 return self.batch_update_vertices(ptr, total_vertices, vertices_per_mesh);
             },
             "Batch update all registered meshes from numpy array (zero-copy)",
             py::arg("vertices"),
             py::arg("vertices_per_mesh"))
        
        .def("clear_meshes",
             &qixotic::tendroids::FastMeshUpdater::clear_meshes,
             "Clear all registered meshes")
        
        .def("get_mesh_count",
             &qixotic::tendroids::FastMeshUpdater::get_mesh_count,
             "Get number of registered meshes")
        
        .def("is_stage_attached",
             &qixotic::tendroids::FastMeshUpdater::is_stage_attached,
             "Check if stage is attached");
    
    // Module-level function for quick testing
    m.def("hello_world", []() {
        return "Hello from C++ FastMeshUpdater module!";
    }, "Simple module-level hello world function");
    
    // Module version
    m.attr("__version__") = "0.2.0-alpha-phase2";
}
