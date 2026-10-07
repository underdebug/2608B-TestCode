cmake_minimum_required(VERSION 3.18)

set(CMAKE_CUDA_COMPILER /usr/local/cuda/bin/nvcc CACHE FILEPATH "CUDA compiler")
project(test LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_BUILD_TYPE Debug)

set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -G -g -O0")
set(CMAKE_CUDA_ARCHITECTURES 75 80 86 87 89 90 100 110 120)

set(THIRD_PARTY_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../3rdParty")

find_package(CUDAToolkit REQUIRED)
find_package(OpenGL REQUIRED)
find_package(GLUT REQUIRED)
find_package(GLEW REQUIRED)
find_package(glfw3 REQUIRED)
find_package(glm CONFIG REQUIRED)

# Added for the Qt / QML interface.
find_package(Qt6 6.4 REQUIRED COMPONENTS Quick QuickControls2 Quick3D)
set(CMAKE_AUTOMOC ON)

include_directories(
    ${OPENGL_INCLUDE_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${GLUT_INCLUDE_DIRS}
    "${THIRD_PARTY_ROOT}/OpenMesh/src"
    "${THIRD_PARTY_ROOT}/Open3D/cpp"
    "${THIRD_PARTY_ROOT}/eigen"
    "${THIRD_PARTY_ROOT}/glm"
)

link_directories(
    "${THIRD_PARTY_ROOT}/OpenMesh/build/Build/lib"
    "${THIRD_PARTY_ROOT}/Open3D/build/lib/Release"
)

add_executable(${PROJECT_NAME}
    main.cpp
)

# Keep the GLSL source intact; adapt only its C++ build copy.
set(NURBS_SHADER "${CMAKE_CURRENT_SOURCE_DIR}/shaders/nurbs.vert")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${NURBS_SHADER}")
file(READ "${NURBS_SHADER}" NURBS_CPP)
string(REGEX REPLACE "#version[^\n]*" "" NURBS_CPP "${NURBS_CPP}")
string(REGEX REPLACE "float\\[\\]\\(([^;]*)\\);" "{\\1};" NURBS_CPP "${NURBS_CPP}")
string(REPLACE ".yx" ".yx()" NURBS_CPP "${NURBS_CPP}")
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/generated/nurbs_cpp.hpp"
    "// Generated from nurbs.vert; edit the original shader instead.\n${NURBS_CPP}")
target_include_directories(${PROJECT_NAME} PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/generated")

target_link_libraries(${PROJECT_NAME} PRIVATE
    X11
    GL
    GLU
    cuda
    cudart
    glfw
    GLEW::GLEW
    OpenMeshCored
    OpenMeshToolsd
    Open3D
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Quick3D
    glm::glm
)

set_target_properties(${PROJECT_NAME} PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
)
