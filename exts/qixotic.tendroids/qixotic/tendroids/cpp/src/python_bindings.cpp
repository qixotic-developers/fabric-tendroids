#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "fast_mesh_updater.h"

namespace py = pybind11;

PYBIND11_MODULE(fast_mesh_updater, m) {
    m.doc() = "FastMeshUpdater C++ Extension for Tendroids\n\n"
              "Phase 1: Basic pybind11 integration test\n"
              "Provides simple functions to verify C++ toolchain";
    
    // Bind the FastMeshUpdater class
    py::class_<qixotic::tendroids::FastMeshUpdater>(m, "FastMeshUpdater")
        .def(py::init<>(), 
             "Create a new FastMeshUpdater instance")
        
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
             "Return a greeting message");
    
    // Module-level function for quick testing
    m.def("hello_world", []() {
        return "Hello from C++ FastMeshUpdater module!";
    }, "Simple module-level hello world function");
    
    // Module version
    m.attr("__version__") = "0.1.0-alpha-phase1";
}
