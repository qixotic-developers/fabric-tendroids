#include "fast_mesh_updater.h"
#include <sstream>


namespace qixotic::tendroids {

FastMeshUpdater::FastMeshUpdater() 
    : version_("0.1.0-alpha-phase1") {
}

FastMeshUpdater::~FastMeshUpdater() = default;

std::string FastMeshUpdater::get_version() const {
    return version_;
}

int FastMeshUpdater::add_numbers(int a, int b) {
    return a + b;
}

std::vector<float> FastMeshUpdater::echo_array(const std::vector<float>& input) {
    // Double each value to verify data transfer works
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
    return oss.str();
}

} // namespace qixotic::tendroids

