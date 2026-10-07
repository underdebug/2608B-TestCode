
#include <cstdio>
#include <glm/glm.hpp>

#define SHADER_TEST

#include "shaders/shader.h"
#include "shaders/nurbs.vert"
// #include "nurbs_cpp.hpp"

int main(int argc, char *argv[])
{
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt

    // A constant rational surface provides a simple CPU shader example.
    for (int i = 0; i < 100; ++i)
    {
        surface.control[i] = vec4(2.0f, 3.0f, 4.0f, 1.0f);
        surface.inputPoint[i] = surface.control[i];
    }
    view.mvp = mat4(1.0f);
    view.mode = 0;
    gl_VertexIndex = 0;
    shader_test();
    std::printf("Position: %g %g %g %g\n", gl_Position.xyz.x,
                gl_Position.xyz.y, gl_Position.xyz.z, gl_Position.w);
    return 0;
}
