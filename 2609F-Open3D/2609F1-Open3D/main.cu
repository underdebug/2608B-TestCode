// Reconstruct a surface from a point cloud using Open3D Poisson reconstruction.
#include <open3d/geometry/PointCloud.h>
#include <open3d/geometry/TriangleMesh.h>
#include <open3d/io/PointCloudIO.h>
#include <open3d/io/TriangleMeshIO.h>
#include <open3d/visualization/visualizer/Visualizer.h>
#include <open3d/visualization/visualizer/RenderOption.h>

#include <algorithm>
#include <chrono>
#include <thread>
#include <exception>
#include <iostream>
#include <memory>


#include "mem/mem.h"

// 可调参数：文件路径相对于运行目录。
#define INPUT_PLY "./sphere.ply"
#define OUTPUT_PLY "./sphere_mesh.ply"
#define RECONSTRUCTION_DEPTH 6       // 建议 5~7；越低越少细节。
#define NORMAL_ESTIMATION_K 100       // 法线估计邻居数，建议 100~200。
#define NORMAL_ORIENTATION_K 30       // 法线方向一致化邻居数，与上面的参数不同。
#define SMOOTH_ITERATIONS 20          // Taubin 平滑次数，建议 10~30；0 表示关闭。
#define SMOOTH_LAMBDA 0.5             // Taubin 正向平滑系数。
#define SMOOTH_MU (-0.53)             // Taubin 反向系数，减少收缩。
#define SHOW_MESH_EDGES true         // 右侧叠加三角形边线。
#define SHOW_VIEWER true
#define VIEWER_WIDTH 1024
#define VIEWER_HEIGHT 768
#define VIEWER_GAP 20                // 两个窗口之间的距离（像素）。

static_assert(RECONSTRUCTION_DEPTH >= 2, "Reconstruction depth must be >= 2");
static_assert(NORMAL_ESTIMATION_K >= 3, "Normal estimation needs >= 3 neighbors");
static_assert(NORMAL_ORIENTATION_K >= 3, "Normal orientation needs >= 3 neighbors");
static_assert(SMOOTH_ITERATIONS >= 0, "Smoothing iterations must be nonnegative");

int main()
{
    mem();
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt


    // Relative to the working directory; run from the project root.
    constexpr const char* filename = INPUT_PLY;

    constexpr const char* output = OUTPUT_PLY;

    try {
        auto cloud = std::make_shared<open3d::geometry::PointCloud>();
        if (!open3d::io::ReadPointCloud(filename, *cloud) || cloud->IsEmpty()) {
            std::cerr << "Failed to load a nonempty point cloud from "
                      << filename << '\n';
            return 1;
        }
        std::cout << "Loaded " << cloud->points_.size()
                  << " points from " << filename << std::endl;

        if (cloud->points_.size() < 4) {
            std::cerr << "Too few points for surface reconstruction\n";
            return 1;
        }

        // Poisson reconstruction requires consistently oriented normals.
        // sphere.ply already has outward normals; estimate them if absent.
        if (!cloud->HasNormals()) {
            cloud->EstimateNormals(open3d::geometry::KDTreeSearchParamKNN(
                    static_cast<int>(std::min<std::size_t>(
                            NORMAL_ESTIMATION_K, cloud->points_.size() - 1))));
            cloud->OrientNormalsConsistentTangentPlane(
                    std::min<std::size_t>(NORMAL_ORIENTATION_K, cloud->points_.size() - 1));
        }
        cloud->NormalizeNormals();

        auto [mesh, densities] =
                open3d::geometry::TriangleMesh::CreateFromPointCloudPoisson(
                        *cloud, RECONSTRUCTION_DEPTH);
        if (!mesh || mesh->triangles_.empty()) {
            std::cerr << "Surface reconstruction produced no triangles\n";
            return 1;
        }
        if (SMOOTH_ITERATIONS > 0) {
            mesh = mesh->FilterSmoothTaubin(
                    SMOOTH_ITERATIONS, SMOOTH_LAMBDA, SMOOTH_MU);
        }
        mesh->ComputeVertexNormals();

        // ASCII PLY stores both vertex data and triangle indices as text.
        if (!open3d::io::WriteTriangleMesh(output, *mesh, true)) {
            std::cerr << "Failed to save " << output << '\n';
            return 1;
        }
        std::cout << "Saved " << output << ": " << mesh->vertices_.size()
                  << " vertices, " << mesh->triangles_.size()
                  << " triangles" << std::endl;

        if (SHOW_VIEWER) {
            open3d::visualization::Visualizer point_view;
            open3d::visualization::Visualizer mesh_view;
            if (!point_view.CreateVisualizerWindow(
                        "Original PLY point cloud", VIEWER_WIDTH, VIEWER_HEIGHT,
                        20, 50) ||
                !mesh_view.CreateVisualizerWindow(
                        "Reconstructed mesh", VIEWER_WIDTH, VIEWER_HEIGHT,
                        20 + VIEWER_WIDTH + VIEWER_GAP, 50)) {
                point_view.DestroyVisualizerWindow();
                mesh_view.DestroyVisualizerWindow();
                std::cerr << "Failed to open the Open3D viewers\n";
                return 1;
            }
            if (!point_view.AddGeometry(cloud) || !mesh_view.AddGeometry(mesh)) {
                point_view.DestroyVisualizerWindow();
                mesh_view.DestroyVisualizerWindow();
                std::cerr << "Failed to add geometry to the viewers\n";
                return 1;
            }

            // 在右侧三角面上叠加边线，不影响左侧点云。
            mesh_view.GetRenderOption().mesh_show_wireframe_ = SHOW_MESH_EDGES;
            mesh_view.UpdateRender();

            // 同一线程轮询两个窗口；关闭一个后，另一个仍可操作。
            bool points_open = true;
            bool mesh_open = true;
            while (points_open || mesh_open) {
                if (points_open) {
                    points_open = point_view.PollEvents();
                    if (points_open) {
                        point_view.UpdateRender();
                    } else {
                        point_view.DestroyVisualizerWindow();
                    }
                }
                if (mesh_open) {
                    mesh_open = mesh_view.PollEvents();
                    if (mesh_open) {
                        mesh_view.UpdateRender();
                    } else {
                        mesh_view.DestroyVisualizerWindow();
                    }
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        }
    } catch (const std::exception& error) {
        std::cerr << "Open3D error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}

