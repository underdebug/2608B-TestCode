#include <cuda_runtime.h>
#include <iostream>
#include <cmath>
#include <vector>
#include <algorithm>
#include <utility>
#include <map>

#include <OpenMesh/Core/Mesh/TriMesh_ArrayKernelT.hh>
#include <OpenMesh/Tools/Subdivider/Uniform/LoopT.hh>

#include "delaunator.hpp"

typedef OpenMesh::TriMesh_ArrayKernelT<> MyMesh;

// Build an OpenMesh mesh from a Delaunator triangulation.
static MyMesh delaunayToOpenMesh(const delaunator::Delaunator& d)
{
    MyMesh mesh;

    std::vector<MyMesh::VertexHandle> vhandles;
    vhandles.reserve(d.coords.size() / 2);
    for (std::size_t i = 0; i < d.coords.size(); i += 2)
        vhandles.push_back(mesh.add_vertex(MyMesh::Point(d.coords[i], d.coords[i + 1], 0.0)));

    for (std::size_t i = 0; i < d.triangles.size(); i += 3)
    {
        mesh.add_face(vhandles[d.triangles[i]],
                      vhandles[d.triangles[i + 1]],
                      vhandles[d.triangles[i + 2]]);
    }

    return mesh;
}

// Get every vertex position as a flat x,y,x,y,... list.
static std::vector<double> openMeshToCoords(const MyMesh& mesh)
{
    std::vector<double> coords;
    coords.reserve(mesh.n_vertices() * 2);

    for (MyMesh::VertexIter vIt = mesh.vertices_begin(); vIt != mesh.vertices_end(); ++vIt)
    {
        const MyMesh::Point& p = mesh.point(*vIt);
        coords.push_back(p[0]);
        coords.push_back(p[1]);
    }

    return coords;
}

// Get every face as 3 vertex indices in a row.
static std::vector<int> openMeshFacesToIndices(const MyMesh& mesh)
{
    std::vector<int> indices;
    indices.reserve(mesh.n_faces() * 3);

    for (MyMesh::FaceIter fIt = mesh.faces_begin(); fIt != mesh.faces_end(); ++fIt)
    {
        for (MyMesh::FaceVertexIter fvIt = mesh.cfv_iter(*fIt); fvIt.is_valid(); ++fvIt)
        {
            indices.push_back(fvIt->idx());
        }
    }

    return indices;
}

// For every halfedge, look up its opposite halfedge index (-1 if none).
static std::vector<int> openMeshEdgesToIndices(const MyMesh& mesh)
{
    std::vector<int> indices(mesh.n_faces() * 3, -1);

    for (MyMesh::EdgeIter eIt = mesh.edges_begin(); eIt != mesh.edges_end(); ++eIt)
    {
        MyMesh::HalfedgeHandle heh = mesh.halfedge_handle(*eIt, 0);

        if (heh.is_valid() && heh.idx() < indices.size())
        {
            MyMesh::HalfedgeHandle oheh = mesh.opposite_halfedge_handle(heh);

            if (oheh.is_valid() && oheh.idx() < indices.size())
                indices[heh.idx()] = oheh.idx();
        }
    }

    return indices;
}

// Walk the mesh boundary using halfedges: a boundary halfedge has no face on
// its side, and following next_halfedge_handle() from one traces the whole
// loop, since OpenMesh keeps boundary halfedges chained together.
static std::vector<std::vector<int>> findBoundaryLoops(const MyMesh& mesh)
{
    std::vector<std::vector<int>> loops;
    std::vector<bool> visited(mesh.n_halfedges(), false);

    for (MyMesh::HalfedgeIter heIt = mesh.halfedges_begin(); heIt != mesh.halfedges_end(); ++heIt)
    {
        MyMesh::HalfedgeHandle start = *heIt;

        if (!mesh.is_boundary(start) || visited[start.idx()])
            continue;

        std::vector<int> loop;
        MyMesh::HalfedgeHandle heh = start;
        do
        {
            visited[heh.idx()] = true;
            loop.push_back(mesh.from_vertex_handle(heh).idx());
            heh = mesh.next_halfedge_handle(heh);
        } while (heh != start);

        loops.push_back(std::move(loop));
    }

    return loops;
}

static void printBoundaryLoops(const MyMesh& mesh, const char* title)
{
    std::vector<std::vector<int>> loops = findBoundaryLoops(mesh);

    std::cout << "== " << title << " ==" << std::endl;
    std::cout << "boundary loops: " << loops.size() << std::endl;
    for (std::size_t i = 0; i < loops.size(); ++i)
    {
        std::cout << "  loop " << i << " (" << loops[i].size() << " verts): ";
        for (int idx : loops[i])
            std::cout << idx << " ";
        std::cout << std::endl;
    }
}

// Turn a list of points into a flat x,y,x,y,... list.
static std::vector<double> pointsToCoords(const std::vector<MyMesh::Point>& points)
{
    std::vector<double> coords;
    coords.reserve(points.size() * 2);

    for (const MyMesh::Point& p : points)
    {
        coords.push_back(p[0]);
        coords.push_back(p[1]);
    }

    return coords;
}

// Get every edge as a (from_vertex, to_vertex) pair.
static std::vector<std::pair<int, int>> openMeshEdgesToIndices_Points(const MyMesh& mesh)
{
    std::vector<std::pair<int, int>> indices;
    indices.reserve(mesh.n_edges());

    for (MyMesh::EdgeIter eIt = mesh.edges_begin(); eIt != mesh.edges_end(); ++eIt)
    {
        MyMesh::HalfedgeHandle heh = mesh.halfedge_handle(*eIt, 0);
        int start = mesh.from_vertex_handle(heh).idx();
        int end = mesh.to_vertex_handle(heh).idx();
        indices.push_back(std::make_pair(start, end));
    }

    return indices;
}

// Find the boundary a different way: an edge used by only one triangle is a
// boundary edge. Count edges by triangle, keep the ones used once, then walk
// them end to end. Doesn't touch OpenMesh's own is_boundary()/halfedge walk.
static std::vector<MyMesh::Point> computeBoundaryPointsByEdgeCount(const MyMesh& mesh, const std::vector<int>& faceIndices)
{
    std::vector<MyMesh::Point> boundaryPoints2;

    std::map<std::pair<int, int>, int> edgeCount;
    for (std::size_t i = 0; i < faceIndices.size(); i += 3)
    {
        int a = faceIndices[i];
        int b = faceIndices[i + 1];
        int c = faceIndices[i + 2];
        int tri[3] = {a, b, c};
        for (int k = 0; k < 3; ++k)
        {
            int u = tri[k];
            int v = tri[(k + 1) % 3];
            if (u > v) std::swap(u, v);
            edgeCount[{u, v}]++;
        }
    }

    std::map<int, std::vector<int>> adj;
    for (const auto& entry : edgeCount)
    {
        if (entry.second == 1)
        {
            int u = entry.first.first;
            int v = entry.first.second;
            adj[u].push_back(v);
            adj[v].push_back(u);
        }
    }

    // Each boundary vertex touches exactly 2 boundary edges, so just keep
    // stepping to "the other" neighbor until we're back at the start.
    if (!adj.empty())
    {
        std::vector<int> loop;
        int start = adj.begin()->first;
        int prev = -1;
        int cur = start;
        do
        {
            loop.push_back(cur);

            int next = -1;
            for (int nb : adj[cur])
            {
                if (nb != prev)
                {
                    next = nb;
                    break;
                }
            }

            prev = cur;
            cur = next;
        } while (cur != -1 && cur != start);

        for (int idx : loop)
            boundaryPoints2.push_back(mesh.point(MyMesh::VertexHandle(idx)));
    }

    return boundaryPoints2;
}

static void printTopology(const MyMesh& mesh, const char* title)
{
    std::cout << "== " << title << " ==" << std::endl;
    std::cout << "points: " << mesh.n_vertices()
               << ", edges: " << mesh.n_edges()
               << ", faces: " << mesh.n_faces() << std::endl;
}

static void printDelaunator(const delaunator::Delaunator& d, const char* title)
{
    std::cout << "== " << title << " ==" << std::endl;
    std::cout << "points: " << d.coords.size() / 2
               << ", triangles: " << d.triangles.size() / 3
               << ", halfedges: " << d.halfedges.size() << std::endl;
}

// ---------------------------------------------------------------------------
// More OpenMesh feature samples: valence, normals, circulators, edge length.
// ---------------------------------------------------------------------------

// Valence = how many edges touch a vertex. OpenMesh has a built-in helper
// for this (mesh.valence(vh)) instead of counting a circulator by hand.
static void printVertexValences(const MyMesh& mesh, const char* title)
{
    std::cout << "== " << title << " ==" << std::endl;
    for (MyMesh::VertexIter vIt = mesh.vertices_begin(); vIt != mesh.vertices_end(); ++vIt)
    {
        std::cout << "  vertex " << vIt->idx()
                   << " valence: " << mesh.valence(*vIt)
                   << (mesh.is_boundary(*vIt) ? " (boundary)" : "") << std::endl;
    }
}

// Vertex normals: OpenMesh can compute these for us. We just need to "ask
// for" the normal property first (request_vertex_normals), then call
// update_normals() to fill them in from the current point positions.
static void printVertexNormals(MyMesh& mesh, const char* title)
{
    mesh.request_face_normals();
    mesh.request_vertex_normals();
    mesh.update_normals();

    std::cout << "== " << title << " ==" << std::endl;
    for (MyMesh::VertexIter vIt = mesh.vertices_begin(); vIt != mesh.vertices_end(); ++vIt)
    {
        const MyMesh::Normal& n = mesh.normal(*vIt);
        std::cout << "  vertex " << vIt->idx()
                   << " normal: (" << n[0] << ", " << n[1] << ", " << n[2] << ")" << std::endl;
    }

    mesh.release_vertex_normals();
    mesh.release_face_normals();
}

// VertexFaceIter (vf_iter): walk every face that touches one vertex.
// VertexVertexIter (vv_iter): walk every neighboring vertex.
// These are the same idea as FaceVertexIter used above, just centered on a
// vertex instead of a face.
static void printVertexNeighbors(const MyMesh& mesh, MyMesh::VertexHandle vh)
{
    std::cout << "== neighbors of vertex " << vh.idx() << " ==" << std::endl;

    std::cout << "  neighbor vertices: ";
    for (MyMesh::VertexVertexIter vvIt = mesh.cvv_iter(vh); vvIt.is_valid(); ++vvIt)
        std::cout << vvIt->idx() << " ";
    std::cout << std::endl;

    std::cout << "  touching faces: ";
    for (MyMesh::VertexFaceIter vfIt = mesh.cvf_iter(vh); vfIt.is_valid(); ++vfIt)
        std::cout << vfIt->idx() << " ";
    std::cout << std::endl;
}

// Edge length: OpenMesh gives us the two endpoint vertex handles for a
// halfedge, and we just measure the distance between their points.
static void printEdgeLengths(const MyMesh& mesh, const char* title)
{
    std::cout << "== " << title << " ==" << std::endl;
    for (MyMesh::EdgeIter eIt = mesh.edges_begin(); eIt != mesh.edges_end(); ++eIt)
    {
        double len = mesh.calc_edge_length(*eIt);
        std::cout << "  edge " << eIt->idx() << " length: " << len << std::endl;
    }
}

// Euler's formula for a disk-like mesh: V - E + F should equal 1 (or 2 for a
// closed surface with no boundary). A quick sanity check on the topology.
static void printEulerCheck(const MyMesh& mesh, const char* title)
{
    long v = (long)mesh.n_vertices();
    long e = (long)mesh.n_edges();
    long f = (long)mesh.n_faces();
    std::cout << "== " << title << " ==" << std::endl;
    std::cout << "  V - E + F = " << v << " - " << e << " + " << f << " = " << (v - e + f) << std::endl;
}

int main()
{
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt


    // 1) A few 2D points, triangulated by delaunator.
    std::vector<double> coords = {
        0, 0,   4, 0,   4, 4,   0, 4,
        2, 2,   1, 3,   3, 1
    };

    delaunator::Delaunator delaunay1(coords);
    printDelaunator(delaunay1, "Delaunator (initial)");

    // 2) Load that triangulation into OpenMesh.
    MyMesh mesh = delaunayToOpenMesh(delaunay1);
    printTopology(mesh, "OpenMesh (from Delaunator)");

    std::vector<double> originalCoords = openMeshToCoords(mesh);
    std::vector<int> originalFaceIndices = openMeshFacesToIndices(mesh);
    std::vector<int> originalEdgeIndices = openMeshEdgesToIndices(mesh);
    std::vector<int> edgeIndices = openMeshEdgesToIndices(mesh);
    std::vector<std::pair<int, int>> edgePoints = openMeshEdgesToIndices_Points(mesh);

    // Boundary, found the OpenMesh way (halfedge walk).
    std::vector<MyMesh::VertexHandle> boundaryVertices;
    std::vector<MyMesh::Point> boundaryPoints;
    for (const std::vector<int>& loop : findBoundaryLoops(mesh))
    {
        for (int idx : loop)
        {
            MyMesh::VertexHandle vh(idx);
            boundaryVertices.push_back(vh);
            boundaryPoints.push_back(mesh.point(vh));
        }
    }
    printBoundaryLoops(mesh, "OpenMesh boundary loops (from Delaunator)");

    // Boundary, found again but by hand (edge-count algorithm) - same
    // answer, just to show the topology info can be recovered either way.
    std::vector<MyMesh::Point> boundaryPoints2 = computeBoundaryPointsByEdgeCount(mesh, originalFaceIndices);

    // Visit every triangle by crossing shared edges (flood fill), starting
    // from triangle 0. This is basically what a mesh circulator does under
    // the hood, just written out explicitly.
    std::vector<int> triangles;
    std::vector<bool> visitedFaces(mesh.n_faces(), false);
    triangles.push_back(0);
    visitedFaces[0] = true;
    int popIndex = 0;
    while (popIndex < (int)triangles.size())
    {
        MyMesh::FaceHandle fh(triangles[popIndex]);
        for (MyMesh::FaceHalfedgeIter fhIt = mesh.fh_iter(fh); fhIt.is_valid(); ++fhIt)
        {
            MyMesh::HalfedgeHandle oheh = mesh.opposite_halfedge_handle(*fhIt);
            if (mesh.is_boundary(oheh))
                continue;

            MyMesh::FaceHandle nfh = mesh.face_handle(oheh);
            if (nfh.is_valid() && !visitedFaces[nfh.idx()])
            {
                visitedFaces[nfh.idx()] = true;
                triangles.push_back(nfh.idx());
            }
        }

        popIndex++;
    }

    // More OpenMesh features on the same mesh: valence, normals, a vertex's
    // neighbors, edge lengths, and a topology sanity check.
    printVertexValences(mesh, "Vertex valences (from Delaunator)");
    printVertexNormals(mesh, "Vertex normals (from Delaunator)");
    printVertexNeighbors(mesh, MyMesh::VertexHandle(0));
    printEdgeLengths(mesh, "Edge lengths (from Delaunator)");
    printEulerCheck(mesh, "Euler check (from Delaunator)");

    // 3) Subdivide with one level of Loop subdivision.
    //
    // OpenMesh's LoopT doesn't know about sharp corners: it moves every
    // boundary vertex with the same soft averaging rule, so square corners
    // round off. New edge-midpoint vertices are fine (they just sit at the
    // average of their two endpoints), only the original corners drift. Fix:
    // remember where the boundary vertices started and snap them back after
    // each subdivision pass (LoopT keeps old vertex handles valid; new
    // vertices are appended after them, so the old handles still line up).
    //
    // Snap after every level, not just at the end - otherwise a second level
    // would use an already-drifted corner as one of its neighbors, baking
    // the error in before we get a chance to fix it.
    const int levels = 2;
    OpenMesh::Subdivider::Uniform::LoopT<MyMesh> loop;
    loop.attach(mesh);
    for (int level = 0; level < levels; ++level)
    {
        loop(1);
        for (std::size_t i = 0; i < boundaryVertices.size(); ++i)
            mesh.set_point(boundaryVertices[i], boundaryPoints[i]);
    }
    loop.detach();

    printTopology(mesh, "OpenMesh (after Loop subdivision)");
    printBoundaryLoops(mesh, "OpenMesh boundary loops (after Loop subdivision)");
    printEulerCheck(mesh, "Euler check (after Loop subdivision)");

    std::vector<double> originalCoords2 = openMeshToCoords(mesh);
    std::vector<int> originalFaceIndices2 = openMeshFacesToIndices(mesh);
    std::vector<int> originalEdgeIndices2 = openMeshEdgesToIndices(mesh);

    // 4) Feed the refined points back into delaunator for a fresh triangulation.
    std::vector<double> refinedCoords = openMeshToCoords(mesh);
    delaunator::Delaunator delaunay2(refinedCoords);
    printDelaunator(delaunay2, "Delaunator (rebuilt from subdivided mesh)");

    return 0;
}
