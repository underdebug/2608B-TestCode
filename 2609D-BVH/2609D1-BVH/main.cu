// bvh_cuda.cu
#include <cuda_runtime.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <vector>

// ============================================================
// Basic vector
// ============================================================

struct Vec3
{
    float x, y, z;

    __host__ __device__
    Vec3() : x(0), y(0), z(0) {}

    __host__ __device__
    Vec3(float X, float Y, float Z) : x(X), y(Y), z(Z) {}

    __host__ __device__
    Vec3 operator+(const Vec3& b) const
    {
        return Vec3(x + b.x, y + b.y, z + b.z);
    }

    __host__ __device__
    Vec3 operator-(const Vec3& b) const
    {
        return Vec3(x - b.x, y - b.y, z - b.z);
    }

    __host__ __device__
    Vec3 operator*(float s) const
    {
        return Vec3(x * s, y * s, z * s);
    }
};

__host__ __device__
float dot(const Vec3& a, const Vec3& b)
{
    return a.x * b.x +
           a.y * b.y +
           a.z * b.z;
}

__host__ __device__
Vec3 cross(const Vec3& a, const Vec3& b)
{
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    );
}


// ============================================================
// Triangle
// ============================================================

struct Triangle
{
    Vec3 v0;
    Vec3 v1;
    Vec3 v2;
};


// ============================================================
// Ray
// ============================================================

struct Ray
{
    Vec3 origin;
    Vec3 dir;
};


// ============================================================
// AABB
// ============================================================

struct AABB
{
    Vec3 bmin;
    Vec3 bmax;
};


// ============================================================
// BVH Node
//
// Leaf:
//      triangle >= 0
//
// Internal:
//      triangle = -1
//      left/right point to child nodes
// ============================================================

struct BVHNode
{
    AABB box;

    int left;
    int right;

    int triangle;
};


// ============================================================
// Helpers
// ============================================================

Vec3 minVec(const Vec3& a, const Vec3& b)
{
    return Vec3(
        std::min(a.x, b.x),
        std::min(a.y, b.y),
        std::min(a.z, b.z)
    );
}

Vec3 maxVec(const Vec3& a, const Vec3& b)
{
    return Vec3(
        std::max(a.x, b.x),
        std::max(a.y, b.y),
        std::max(a.z, b.z)
    );
}


AABB triangleBox(const Triangle& t)
{
    AABB box;

    box.bmin = minVec(t.v0, minVec(t.v1, t.v2));
    box.bmax = maxVec(t.v0, maxVec(t.v1, t.v2));

    return box;
}


AABB mergeBox(const AABB& a, const AABB& b)
{
    AABB result;

    result.bmin = minVec(a.bmin, b.bmin);
    result.bmax = maxVec(a.bmax, b.bmax);

    return result;
}


Vec3 triangleCenter(const Triangle& t)
{
    return (t.v0 + t.v1 + t.v2) * (1.0f / 3.0f);
}


// ============================================================
// CPU BVH construction
// ============================================================

int buildBVH(
    std::vector<BVHNode>& nodes,
    const std::vector<Triangle>& triangles,
    std::vector<int>& indices,
    int begin,
    int end)
{
    int nodeIndex = static_cast<int>(nodes.size());

    nodes.push_back(BVHNode());

    // --------------------------------------------------------
    // Calculate bounding box
    // --------------------------------------------------------

    AABB box = triangleBox(triangles[indices[begin]]);

    for (int i = begin + 1; i < end; ++i)
    {
        box = mergeBox(
            box,
            triangleBox(triangles[indices[i]])
        );
    }

    int count = end - begin;

    // --------------------------------------------------------
    // Leaf
    // --------------------------------------------------------

    if (count == 1)
    {
        nodes[nodeIndex].box      = box;
        nodes[nodeIndex].left     = -1;
        nodes[nodeIndex].right    = -1;
        nodes[nodeIndex].triangle = indices[begin];

        return nodeIndex;
    }

    // --------------------------------------------------------
    // Find longest axis
    // --------------------------------------------------------

    Vec3 extent = box.bmax - box.bmin;

    int axis = 0;

    if (extent.y > extent.x)
        axis = 1;

    if ((axis == 0 ? extent.x : extent.y) < extent.z)
        axis = 2;


    // --------------------------------------------------------
    // Sort triangles according to centroid
    // --------------------------------------------------------

    std::sort(
        indices.begin() + begin,
        indices.begin() + end,
        [&](int a, int b)
        {
            Vec3 ca = triangleCenter(triangles[a]);
            Vec3 cb = triangleCenter(triangles[b]);

            if (axis == 0)
                return ca.x < cb.x;

            if (axis == 1)
                return ca.y < cb.y;

            return ca.z < cb.z;
        }
    );


    int mid = (begin + end) / 2;


    // --------------------------------------------------------
    // Recursively build children
    // --------------------------------------------------------

    int left = buildBVH(
        nodes,
        triangles,
        indices,
        begin,
        mid
    );

    int right = buildBVH(
        nodes,
        triangles,
        indices,
        mid,
        end
    );


    nodes[nodeIndex].box      = box;
    nodes[nodeIndex].left     = left;
    nodes[nodeIndex].right    = right;
    nodes[nodeIndex].triangle = -1;

    return nodeIndex;
}


// ============================================================
// GPU AABB intersection
// ============================================================

__device__
bool intersectAABB(
    const Ray& ray,
    const AABB& box)
{
    float tmin = 0.0f;
    float tmax = 1e30f;

    float origin[3] =
    {
        ray.origin.x,
        ray.origin.y,
        ray.origin.z
    };

    float dir[3] =
    {
        ray.dir.x,
        ray.dir.y,
        ray.dir.z
    };

    float bmin[3] =
    {
        box.bmin.x,
        box.bmin.y,
        box.bmin.z
    };

    float bmax[3] =
    {
        box.bmax.x,
        box.bmax.y,
        box.bmax.z
    };


    for (int i = 0; i < 3; ++i)
    {
        float invD = 1.0f / dir[i];

        float t0 = (bmin[i] - origin[i]) * invD;
        float t1 = (bmax[i] - origin[i]) * invD;

        if (invD < 0.0f)
        {
            float temp = t0;
            t0 = t1;
            t1 = temp;
        }

        tmin = fmaxf(tmin, t0);
        tmax = fminf(tmax, t1);

        if (tmax < tmin)
            return false;
    }

    return true;
}


// ============================================================
// GPU Ray-Triangle intersection
//
// Moller-Trumbore
// ============================================================

__device__
bool intersectTriangle(
    const Ray& ray,
    const Triangle& tri,
    float& t)
{
    const float EPS = 1e-7f;

    Vec3 edge1 = tri.v1 - tri.v0;
    Vec3 edge2 = tri.v2 - tri.v0;

    Vec3 h = cross(ray.dir, edge2);

    float a = dot(edge1, h);

    if (fabsf(a) < EPS)
        return false;

    float f = 1.0f / a;

    Vec3 s = ray.origin - tri.v0;

    float u = f * dot(s, h);

    if (u < 0.0f || u > 1.0f)
        return false;

    Vec3 q = cross(s, edge1);

    float v = f * dot(ray.dir, q);

    if (v < 0.0f || u + v > 1.0f)
        return false;

    t = f * dot(edge2, q);

    return t > EPS;
}


// ============================================================
// GPU BVH traversal
// ============================================================

__device__
int traverseBVH(
    const Ray& ray,
    const BVHNode* nodes,
    const Triangle* triangles,
    float& closestT)
{
    // Explicit stack instead of recursion
    int stack[64];

    int stackPtr = 0;

    stack[stackPtr++] = 0;       // root

    int hitTriangle = -1;

    closestT = 1e30f;


    while (stackPtr > 0)
    {
        int nodeIndex = stack[--stackPtr];

        const BVHNode& node = nodes[nodeIndex];


        // ----------------------------------------------
        // First test bounding box
        // ----------------------------------------------

        if (!intersectAABB(ray, node.box))
            continue;


        // ----------------------------------------------
        // Leaf node
        // ----------------------------------------------

        if (node.triangle >= 0)
        {
            float t;

            if (intersectTriangle(
                    ray,
                    triangles[node.triangle],
                    t))
            {
                if (t < closestT)
                {
                    closestT = t;
                    hitTriangle = node.triangle;
                }
            }
        }

        // ----------------------------------------------
        // Internal node
        // ----------------------------------------------

        else
        {
            if (node.left >= 0)
                stack[stackPtr++] = node.left;

            if (node.right >= 0)
                stack[stackPtr++] = node.right;
        }
    }

    return hitTriangle;
}


// ============================================================
// CUDA kernel
//
// One thread = one ray
// ============================================================

__global__
void traceKernel(
    const Ray* rays,
    int rayCount,
    const BVHNode* nodes,
    const Triangle* triangles,
    int* hits,
    float* distances)
{
    int id =
        blockIdx.x * blockDim.x +
        threadIdx.x;

    if (id >= rayCount)
        return;


    float t;

    int triangle =
        traverseBVH(
            rays[id],
            nodes,
            triangles,
            t
        );


    hits[id] = triangle;
    distances[id] = t;
}


// ============================================================
// Main
// ============================================================


#include "mem/mem.h"

int main()
{
    mem();
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt


    // --------------------------------------------------------
    // Create two triangles
    // --------------------------------------------------------

    std::vector<Triangle> triangles =
    {
        {
            Vec3(-1.0f, -1.0f, 5.0f),
            Vec3( 1.0f, -1.0f, 5.0f),
            Vec3( 0.0f,  1.0f, 5.0f)
        },

        {
            Vec3(2.0f, -1.0f, 8.0f),
            Vec3(4.0f, -1.0f, 8.0f),
            Vec3(3.0f,  1.0f, 8.0f)
        }
    };


    // --------------------------------------------------------
    // Build BVH on CPU
    // --------------------------------------------------------

    std::vector<int> indices(triangles.size());

    for (int i = 0; i < (int)triangles.size(); ++i)
        indices[i] = i;


    std::vector<BVHNode> nodes;

    buildBVH(
        nodes,
        triangles,
        indices,
        0,
        static_cast<int>(triangles.size())
    );


    std::cout
        << "BVH nodes = "
        << nodes.size()
        << "\n";


    // --------------------------------------------------------
    // Rays
    // --------------------------------------------------------

    std::vector<Ray> rays =
    {
        {
            Vec3(0, 0, 0),
            Vec3(0, 0, 1)
        },

        {
            Vec3(3, 0, 0),
            Vec3(0, 0, 1)
        },

        {
            Vec3(10, 0, 0),
            Vec3(0, 0, 1)
        }
    };


    int rayCount = static_cast<int>(rays.size());


    // --------------------------------------------------------
    // GPU memory
    // --------------------------------------------------------

    Triangle* d_triangles;
    BVHNode*  d_nodes;
    Ray*      d_rays;

    int*   d_hits;
    float* d_distances;


    cudaMalloc(
        &d_triangles,
        triangles.size() * sizeof(Triangle)
    );

    cudaMalloc(
        &d_nodes,
        nodes.size() * sizeof(BVHNode)
    );

    cudaMalloc(
        &d_rays,
        rayCount * sizeof(Ray)
    );

    cudaMalloc(
        &d_hits,
        rayCount * sizeof(int)
    );

    cudaMalloc(
        &d_distances,
        rayCount * sizeof(float)
    );


    // --------------------------------------------------------
    // CPU -> GPU
    // --------------------------------------------------------

    cudaMemcpy(
        d_triangles,
        triangles.data(),
        triangles.size() * sizeof(Triangle),
        cudaMemcpyHostToDevice
    );

    cudaMemcpy(
        d_nodes,
        nodes.data(),
        nodes.size() * sizeof(BVHNode),
        cudaMemcpyHostToDevice
    );

    cudaMemcpy(
        d_rays,
        rays.data(),
        rayCount * sizeof(Ray),
        cudaMemcpyHostToDevice
    );


    // --------------------------------------------------------
    // Launch kernel
    // --------------------------------------------------------

    int blockSize = 256;

    int gridSize =
        (rayCount + blockSize - 1) /
        blockSize;


    traceKernel<<<gridSize, blockSize>>>(
        d_rays,
        rayCount,
        d_nodes,
        d_triangles,
        d_hits,
        d_distances
    );


    cudaDeviceSynchronize();


    // --------------------------------------------------------
    // GPU -> CPU
    // --------------------------------------------------------

    std::vector<int> hits(rayCount);
    std::vector<float> distances(rayCount);


    cudaMemcpy(
        hits.data(),
        d_hits,
        rayCount * sizeof(int),
        cudaMemcpyDeviceToHost
    );

    cudaMemcpy(
        distances.data(),
        d_distances,
        rayCount * sizeof(float),
        cudaMemcpyDeviceToHost
    );


    // --------------------------------------------------------
    // Print result
    // --------------------------------------------------------

    for (int i = 0; i < rayCount; ++i)
    {
        std::cout << "Ray " << i << ": ";

        if (hits[i] >= 0)
        {
            std::cout
                << "hit triangle "
                << hits[i]
                << ", t = "
                << distances[i]
                << "\n";
        }
        else
        {
            std::cout << "miss\n";
        }
    }


    // --------------------------------------------------------
    // Cleanup
    // --------------------------------------------------------

    cudaFree(d_triangles);
    cudaFree(d_nodes);
    cudaFree(d_rays);
    cudaFree(d_hits);
    cudaFree(d_distances);


    return 0;
}