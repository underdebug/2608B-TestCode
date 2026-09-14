
cmake_minimum_required(VERSION 3.18)

set(CMAKE_CUDA_COMPILER /usr/local/cuda/bin/nvcc CACHE FILEPATH "CUDA compiler")

project(test LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 14)

set(CMAKE_BUILD_TYPE Debug)

set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -G -g -O0")

set(CMAKE_CUDA_ARCHITECTURES 75 80 86 87 89 90 100 110 120)

set(ENV{NV_DRIVER_CAPABILITIES} "all")

# OpenMesh (built in-place under 3rdParty, relative to this file's directory)
set(OPENMESH_ROOT ${CMAKE_SOURCE_DIR}/../../../3rdParty/OpenMesh)
set(OPENMESH_BUILD_DIR ${OPENMESH_ROOT}/build/Build)

include_directories(
    ${OPENGL_INCLUDE_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${GLUT_INCLUDE_DIRS}
    ${OPENMESH_ROOT}/src
)

link_directories(
    ${OPENMESH_BUILD_DIR}/lib
)

# so the built executable can find libOpenMeshCored.so / libOpenMeshToolsd.so at runtime
set(CMAKE_BUILD_RPATH ${OPENMESH_BUILD_DIR}/lib)

add_definitions(
    -DGL_GLEXT_PROTOTYPES
)

add_executable(${PROJECT_NAME}
    main.cu
    delaunator.cpp
)

find_package(CUDAToolkit REQUIRED)
find_package(OpenGL REQUIRED)
find_package(GLUT REQUIRED)
find_package(GLEW REQUIRED)
find_package(glfw3 REQUIRED)

target_link_libraries(${PROJECT_NAME} PRIVATE
    #${OPENGL_LIBRARIES}
    #${GLUT_LIBRARIES}
    X11
    GL
    GLU
    cuda
    cudart
    glfw
    GLEW::GLEW
    OpenMeshCored
    OpenMeshToolsd
)

set_target_properties(${PROJECT_NAME} PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
)

