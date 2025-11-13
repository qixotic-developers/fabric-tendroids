cmake_minimum_required(VERSION 3.20)
project(qixotic_tendroids_cpp VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Force MSVC on Windows (not MinGW)
if(WIN32)
    if(NOT MSVC)
        message(WARNING "Detected non-MSVC compiler. For best compatibility with Python extensions on Windows, use MSVC.")
        message(WARNING "In CLion: Settings -> Toolchains -> Move 'Visual Studio' to top")
    endif()
endif()

# Find Python (Kit SDK uses Python 3.10)
find_package(Python3 3.10 COMPONENTS Interpreter Development REQUIRED)
message(STATUS "Python3 found: ${Python3_EXECUTABLE}")
message(STATUS "Python3 include: ${Python3_INCLUDE_DIRS}")
message(STATUS "Python3 libraries: ${Python3_LIBRARIES}")

# Try multiple methods to find pybind11
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not found via CONFIG, trying pybind11 module...")
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(pybind11_DIR)
        message(STATUS "Found pybind11 cmake dir: ${pybind11_DIR}")
        set(CMAKE_PREFIX_PATH "${pybind11_DIR}" ${CMAKE_PREFIX_PATH})
        find_package(pybind11 CONFIG REQUIRED)
    endif()
endif()

if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not found via cmake, using manual include...")
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import pybind11; print(pybind11.get_include())"
        OUTPUT_VARIABLE pybind11_INCLUDE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(pybind11_INCLUDE_DIR)
        message(STATUS "Found pybind11 include: ${pybind11_INCLUDE_DIR}")
        include_directories(${pybind11_INCLUDE_DIR})
        set(pybind11_FOUND TRUE)
    else()
        message(FATAL_ERROR "pybind11 not found! Install with: pip install pybind11")
    endif()
endif()

if(pybind11_FOUND)
    message(STATUS "✓ pybind11 found: ${pybind11_VERSION}")
else()
    message(FATAL_ERROR "✗ pybind11 not found - install with: pip install pybind11")
endif()

# Omniverse Kit SDK paths (for Phase 2+)
set(KIT_SDK_PATH "C:/Users/$ENV{USERNAME}/AppData/Local/ov/pkg/composer-2024.1.0" 
    CACHE PATH "Kit SDK installation path")

if(NOT EXISTS ${KIT_SDK_PATH})
    message(WARNING "Kit SDK not found at ${KIT_SDK_PATH}")
    message(WARNING "This is OK for Phase 1 (no USD dependencies yet)")
    message(WARNING "Set KIT_SDK_PATH for Phase 2+: cmake .. -DKIT_SDK_PATH=\"C:/path/to/kit\"")
endif()

set(USD_INCLUDE_DIR "${KIT_SDK_PATH}/include" CACHE PATH "USD include directory")
set(USD_LIB_DIR "${KIT_SDK_PATH}/lib" CACHE PATH "USD library directory")

message(STATUS "Kit SDK Path: ${KIT_SDK_PATH}")
message(STATUS "USD Include: ${USD_INCLUDE_DIR}")
message(STATUS "USD Lib: ${USD_LIB_DIR}")

# Include directories
include_directories(
    ${Python3_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link directories
link_directories(
    ${Python3_LIBRARY_DIRS}
)

# Phase 1: Simple source files
set(SOURCES
    src/python_bindings.cpp
    src/fast_mesh_updater.cpp
)

# Create Python module
if(pybind11_VERSION)
    pybind11_add_module(fast_mesh_updater ${SOURCES})
else()
    add_library(fast_mesh_updater MODULE ${SOURCES})
    target_include_directories(fast_mesh_updater PRIVATE ${pybind11_INCLUDE_DIR})
    target_link_libraries(fast_mesh_updater PRIVATE ${Python3_LIBRARIES})
    
    set_target_properties(fast_mesh_updater PROPERTIES
        PREFIX ""
        SUFFIX ".pyd"
    )
endif()

# Additional link libraries
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
    
    # Make sure we're using /MD (release) or /MDd (debug) runtime
    if(MSVC)
        target_compile_options(fast_mesh_updater PRIVATE
            $<$<CONFIG:Debug>:/MDd>
            $<$<CONFIG:Release>:/MD>
        )
    endif()
endif()

# Set output properties
set_target_properties(fast_mesh_updater PROPERTIES
    OUTPUT_NAME "fast_mesh_updater"
    PREFIX ""
    SUFFIX ".pyd"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)

# Installation
install(TARGETS fast_mesh_updater
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/../..
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/../..
)

message(STATUS "========================================")
message(STATUS "Configuration Summary:")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "  Python: ${Python3_VERSION}")
message(STATUS "  pybind11: ${pybind11_VERSION}")
message(STATUS "  Output: fast_mesh_updater.pyd")
message(STATUS "========================================")

if(NOT MSVC AND WIN32)
    message(WARNING "")
    message(WARNING "⚠️  NOT using MSVC compiler!")
    message(WARNING "For Python extensions on Windows, MSVC is recommended.")
    message(WARNING "MinGW-compiled modules may have DLL dependency issues.")
    message(WARNING "")
    message(WARNING "To fix: In CLion Settings -> Toolchains")
    message(WARNING "  Move 'Visual Studio' toolchain to the top")
    message(WARNING "")
endif()
