cmake_minimum_required(VERSION 3.20)
project(qixotic_tendroids_cpp VERSION 0.2.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# PHASE 2: Pure Computation - No USD dependencies
# Focus on fast vertex math, Python handles USD updates
# ============================================================================

# Find Python (Kit SDK uses Python 3.10)
find_package(Python3 3.10 COMPONENTS Interpreter Development REQUIRED)
message(STATUS "Python3 found: ${Python3_EXECUTABLE}")
message(STATUS "Python3 include: ${Python3_INCLUDE_DIRS}")

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "pybind11 found: ${pybind11_VERSION}")

# Include directories
include_directories(
    ${Python3_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link directories
link_directories(
    ${Python3_LIBRARY_DIRS}
)

# Phase 2: Pure computation source files
set(SOURCES
    src/python_bindings.cpp
    src/fast_mesh_updater.cpp
)

# Create Python module
pybind11_add_module(fast_mesh_updater ${SOURCES})

# Link libraries (Python only, no USD)
target_link_libraries(fast_mesh_updater PRIVATE
    ${Python3_LIBRARIES}
)

# Windows-specific settings
if(WIN32)
    target_compile_definitions(fast_mesh_updater PRIVATE
        NOMINMAX
        WIN32_LEAN_AND_MEAN
        _CRT_SECURE_NO_WARNINGS
    )
endif()

# Optimization flags for maximum performance
if(MSVC)
    target_compile_options(fast_mesh_updater PRIVATE
        /O2          # Maximum optimization
        /Ob2         # Inline expansion
        /Oi          # Intrinsic functions
        /Ot          # Favor fast code
        /GL          # Whole program optimization
        /fp:fast     # Fast floating point
        /arch:AVX2   # Use AVX2 instructions if available
    )
    target_link_options(fast_mesh_updater PRIVATE
        /LTCG        # Link-time code generation
    )
endif()

# Set output properties
set_target_properties(fast_mesh_updater PROPERTIES
    OUTPUT_NAME "fast_mesh_updater"
    PREFIX ""
    SUFFIX ".pyd"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)

# Installation (copies to parent directory for easy import)
install(TARGETS fast_mesh_updater
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/../..
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/../..
)

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Output will be: fast_mesh_updater.pyd")
message(STATUS "Pure computation mode - Python handles USD")
