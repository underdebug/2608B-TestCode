#version 450

layout(location = 0) in vec3 color;
layout(location = 0) out vec4 fragColor;

#ifndef _main
#define _main main
#endif
void _main()
{
    fragColor = vec4(color, 1);
}
