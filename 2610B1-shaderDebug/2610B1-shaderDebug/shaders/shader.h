#pragma once
#include <glm/glm.hpp>

#define MAIN shader_main

// GLSL declarations used by shaders included as C++.
using vec3 = glm::vec3;

using mat4 = glm::mat4;

#define layout(...)
#define uniform struct
#define out

class vec2
{
public:
    float x = 0.0f;
    float y = 0.0f;

    // Read the current components instead of storing a second, stale vector.
    class SwizzleYX
    {
    public:
        explicit SwizzleYX(const vec2& owner) : owner_(&owner) {}
        operator glm::vec2() const { return glm::vec2(owner_->y, owner_->x); }
        glm::vec2 operator()() const { return static_cast<glm::vec2>(*this); }

    private:
        const vec2* owner_;
    };

    const SwizzleYX yx{*this};

    vec2() = default;
    explicit vec2(float value) : x(value), y(value) {}
    vec2(float x, float y) : x(x), y(y) {}
    vec2(const glm::vec2& value) : x(value.x), y(value.y) {}
    vec2(const SwizzleYX& value) : vec2(static_cast<glm::vec2>(value)) {}
    vec2(const vec2& value) : x(value.x), y(value.y) {}

    vec2& operator=(const vec2& value)
    {
        x = value.x;
        y = value.y;
        return *this;
    }

    vec2& operator=(const glm::vec2& value)
    {
        x = value.x;
        y = value.y;
        return *this;
    }

    vec2& operator=(const SwizzleYX& value)
    {
        return *this = static_cast<glm::vec2>(value);
    }

    operator glm::vec2() const { return glm::vec2(x, y); }

    float& operator[](glm::length_t index) { return index == 0 ? x : y; }
    const float& operator[](glm::length_t index) const { return index == 0 ? x : y; }
};

class vec4
{
public:
    glm::vec3 xyz{0.0f};
    float w = 0.0f;

    vec4() = default;
    explicit vec4(float value) : xyz(value), w(value) {}
    vec4(float x, float y, float z, float w) : xyz(x, y, z), w(w) {}
    vec4(const glm::vec3& xyz, float w) : xyz(xyz), w(w) {}
    vec4(const glm::vec4& value) : xyz(value), w(value.w) {}

    operator glm::vec4() const { return glm::vec4(xyz, w); }

    float& operator[](glm::length_t index)
    {
        return index == 3 ? w : xyz[index];
    }

    const float& operator[](glm::length_t index) const
    {
        return index == 3 ? w : xyz[index];
    }

    friend vec4 operator*(const glm::mat4& matrix, const vec4& value)
    {
        return vec4(matrix * static_cast<glm::vec4>(value));
    }
};

inline int gl_VertexIndex = 0;
inline vec4 gl_Position{0.0f};
