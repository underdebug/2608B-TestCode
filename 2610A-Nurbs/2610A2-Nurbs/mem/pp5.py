

layout(binding = 0, std140) uniform Surface
{
    vec4 control[100]; // xyz in world coordinates, w is the rational weight
    vec4 inputPoint[100];
} surface;
