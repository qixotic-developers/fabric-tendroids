cmake_minimum_required(VERSION 3.20)
project(qixotic_tendroids_cpp VERSION 0.3.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# PHASE 2C: Hybrid C++/Python USD Integration
# C++ handles numpy processing, calls Python USD via pybind11
# No direct USD C++ dependencies needed (uses Python pxr module)
# ============================================================================

# Use Kit SDK Python (Python 3.12)
set(Python3_ROOT_DIR "C:/dev/omniverse-old/omnikitsdk-108.1.0/python" CACHE PATH "Kit SDK Python root")

# Find Python from Kit SDK
find_package(Python3 3.12 COMPONENTS Interpreter Development REQUIRED)
message(STATUS "Python3 found: ${Python3_EXECUTABLE}")
message(STATUS "Python3 version: ${Python3_VERSION}")
message(STATUS "Python3 include: ${Python3_INCLUDE_DIRS}")
message(STATUS "Python3 library: ${Python3_LIBRARIES}")

# Find pybind11 from Kit SDK Python
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "pybind11 dir: ${pybind11_DIR}")

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

# Source files
set(SOURCES
    src/fast_mesh_updater.cpp
)

# Create Python module
pybind11_add_module(fast_mesh_updater ${SOURCES})

# Link libraries (Python only, USD accessed via Python)
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
message(STATUS "Hybrid C++/Python USD - Using Kit SDK Python 3.12")
