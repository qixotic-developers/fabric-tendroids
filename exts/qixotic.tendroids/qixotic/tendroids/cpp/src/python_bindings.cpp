#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "fast_mesh_updater.h"

namespace py = pybind11;

PYBIND11_MODULE(fast_mesh_updater, m) {
    m.doc() = "Fast C++ vertex computation for Tendroids";
    
    // PerfStats struct
    py::class_<qixotic::tendroids::FastMeshUpdater::PerfStats>(m, "PerfStats")
        .def_readonly("total_calls", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_calls)
        .def_readonly("total_vertices", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_vertices)
        .def_readonly("total_time_ms", &qixotic::tendroids::FastMeshUpdater::PerfStats::total_time_ms)
        .def_readonly("avg_time_ms", &qixotic::tendroids::FastMeshUpdater::PerfStats::avg_time_ms);
    
    // Main class
    py::class_<qixotic::tendroids::FastMeshUpdater>(m, "FastMeshUpdater")
        .def(py::init<>())
        .def("get_version", &qixotic::tendroids::FastMeshUpdater::get_version)
        .def("get_mode", &qixotic::tendroids::FastMeshUpdater::get_mode)
        
        // Single tube computation
        .def("compute_tube_vertices",
             [](qixotic::tendroids::FastMeshUpdater& self,
                py::array_t<float> base_verts,
                py::array_t<float> output_verts,
                float time,
                float wave_speed,
                float amplitude,
                float frequency) {
                 
                 auto base_buf = base_verts.request();
                 auto out_buf = output_verts.request();
                 
                 if (base_buf.size != out_buf.size) {
                     throw std::runtime_error("Input and output arrays must be same size");
                 }
                 
                 size_t vertex_count = base_buf.size / 3;
                 
                 return self.compute_tube_vertices(
                     static_cast<float*>(base_buf.ptr),
                     static_cast<float*>(out_buf.ptr),
                     vertex_count,
                     time,
                     wave_speed,
                     amplitude,
                     frequency
                 );
             },
             py::arg("base_vertices"),
             py::arg("output_vertices"),
             py::arg("time"),
             py::arg("wave_speed") = 2.0f,
             py::arg("amplitude") = 0.1f,
             py::arg("frequency") = 1.0f,
             "Compute vertices for single tube")
        
        // Batch computation
        .def("batch_compute_vertices",
             [](qixotic::tendroids::FastMeshUpdater& self,
                py::array_t<float> base_verts,
                py::array_t<float> output_verts,
                size_t num_tubes,
                size_t verts_per_tube,
                float time,
                float wave_speed,
                float amplitude,
                float frequency) {
                 
                 auto base_buf = base_verts.request();
                 auto out_buf = output_verts.request();
                 
                 if (base_buf.size != out_buf.size) {
                     throw std::runtime_error("Input and output arrays must be same size");
                 }
                 
                 return self.batch_compute_vertices(
                     static_cast<float*>(base_buf.ptr),
                     static_cast<float*>(out_buf.ptr),
                     num_tubes,
                     verts_per_tube,
                     time,
                     wave_speed,
                     amplitude,
                     frequency
                 );
             },
             py::arg("base_vertices"),
             py::arg("output_vertices"),
             py::arg("num_tubes"),
             py::arg("verts_per_tube"),
             py::arg("time"),
             py::arg("wave_speed") = 2.0f,
             py::arg("amplitude") = 0.1f,
             py::arg("frequency") = 1.0f,
             "Batch compute vertices for multiple tubes")
        
        // Stats
        .def("get_stats", &qixotic::tendroids::FastMeshUpdater::get_stats)
        .def("reset_stats", &qixotic::tendroids::FastMeshUpdater::reset_stats);
}
