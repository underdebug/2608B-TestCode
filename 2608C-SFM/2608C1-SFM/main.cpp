// ============================================================================
// Minimal multi-image Structure-from-Motion — NO third-party libraries.
// Pure C++17 standard library only.
//
// Implements from scratch:
//   - PPM (P6/P5) and 24-bit BMP image loading
//   - Gaussian blur, Sobel gradients
//   - Harris corner detection + non-max suppression
//   - ZNCC patch descriptors + ratio-test matching
//   - Jacobi eigensolver, 3x3 SVD
//   - Normalized 8-point essential matrix + RANSAC
//   - Pose recovery (4-way decomposition + cheirality test)
//   - Linear (DLT) triangulation
//   - Colored PLY point-cloud output
//
// Usage:   ./sfm <image_dir>       (default: ./images)
// Images:  ordered, overlapping .ppm / .pgm / .bmp files
//          (convert JPEG/PNG first, e.g.:  ffmpeg -i in.jpg out.ppm)
// Output:  cloud.ply
//
// Build:   g++ -O2 -std=c++17 main.cpp -o sfm
// ============================================================================

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// ============================== Basic types =================================

struct Vec2 { double x = 0, y = 0; };

struct Vec3 {
    double x = 0, y = 0, z = 0;
    Vec3() = default;
    Vec3(double a, double b, double c) : x(a), y(b), z(c) {}
    Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator*(double s)      const { return {x * s, y * s, z * s}; }
    double dot(const Vec3& o)     const { return x * o.x + y * o.y + z * o.z; }
    Vec3 cross(const Vec3& o)     const {
        return {y * o.z - z * o.y, z * o.x - x * o.z, x * o.y - y * o.x};
    }
    double norm() const { return std::sqrt(dot(*this)); }
    Vec3 normalized() const { double n = norm(); return n > 0 ? *this * (1.0 / n) : *this; }
};

struct Mat3 {
    double m[3][3] = {{0}};
    static Mat3 identity() {
        Mat3 I; I.m[0][0] = I.m[1][1] = I.m[2][2] = 1.0; return I;
    }
    Vec3 operator*(const Vec3& v) const {
        return {m[0][0]*v.x + m[0][1]*v.y + m[0][2]*v.z,
                m[1][0]*v.x + m[1][1]*v.y + m[1][2]*v.z,
                m[2][0]*v.x + m[2][1]*v.y + m[2][2]*v.z};
    }
    Mat3 operator*(const Mat3& o) const {
        Mat3 r;
        for (int i = 0; i < 3; ++i)
            for (int j = 0; j < 3; ++j)
                for (int k = 0; k < 3; ++k)
                    r.m[i][j] += m[i][k] * o.m[k][j];
        return r;
    }
    Mat3 transposed() const {
        Mat3 r;
        for (int i = 0; i < 3; ++i)
            for (int j = 0; j < 3; ++j) r.m[i][j] = m[j][i];
        return r;
    }
    double det() const {
        return m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1])
             - m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0])
             + m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0]);
    }
    Vec3 col(int j) const { return {m[0][j], m[1][j], m[2][j]}; }
    void setCol(int j, const Vec3& v) { m[0][j] = v.x; m[1][j] = v.y; m[2][j] = v.z; }
};

// ============================== Image I/O ===================================

struct Image {
    int w = 0, h = 0;
    std::vector<uint8_t> rgb;   // w*h*3
    uint8_t r(int x, int y) const { return rgb[3 * (y * w + x) + 0]; }
    uint8_t g(int x, int y) const { return rgb[3 * (y * w + x) + 1]; }
    uint8_t b(int x, int y) const { return rgb[3 * (y * w + x) + 2]; }
};

// Skips PPM whitespace and '#' comments, then reads one integer.
static int ppmInt(std::istream& in) {
    int c;
    while ((c = in.get()) != EOF) {
        if (c == '#') { while ((c = in.get()) != EOF && c != '\n') {} }
        else if (!std::isspace(c)) break;
    }
    int v = 0;
    while (c != EOF && std::isdigit(c)) { v = v * 10 + (c - '0'); c = in.get(); }
    return v;
}

static bool loadPPM(const fs::path& p, Image& img) {
    std::ifstream in(p, std::ios::binary);
    if (!in) return false;
    char m0 = in.get(), m1 = in.get();
    bool color;
    if (m0 == 'P' && m1 == '6') color = true;        // binary RGB
    else if (m0 == 'P' && m1 == '5') color = false;  // binary gray
    else return false;
    img.w = ppmInt(in);
    img.h = ppmInt(in);
    int maxv = ppmInt(in);
    if (img.w <= 0 || img.h <= 0 || maxv != 255) return false;
    img.rgb.resize(size_t(img.w) * img.h * 3);
    if (color) {
        in.read(reinterpret_cast<char*>(img.rgb.data()), img.rgb.size());
    } else {
        std::vector<uint8_t> gray(size_t(img.w) * img.h);
        in.read(reinterpret_cast<char*>(gray.data()), gray.size());
        for (size_t i = 0; i < gray.size(); ++i)
            img.rgb[3*i] = img.rgb[3*i+1] = img.rgb[3*i+2] = gray[i];
    }
    return bool(in);
}

static bool loadBMP(const fs::path& p, Image& img) {
    std::ifstream in(p, std::ios::binary);
    if (!in) return false;
    uint8_t hdr[54];
    in.read(reinterpret_cast<char*>(hdr), 54);
    if (!in || hdr[0] != 'B' || hdr[1] != 'M') return false;
    auto u32 = [&](int o) { return uint32_t(hdr[o]) | (uint32_t(hdr[o+1]) << 8)
                                 | (uint32_t(hdr[o+2]) << 16) | (uint32_t(hdr[o+3]) << 24); };
    auto u16 = [&](int o) { return uint16_t(hdr[o]) | (uint16_t(hdr[o+1]) << 8); };
    uint32_t dataOff = u32(10);
    int32_t  bw = int32_t(u32(18));
    int32_t  bh = int32_t(u32(22));
    if (u16(28) != 24 || u32(30) != 0) return false;   // 24-bit uncompressed only
    bool topDown = bh < 0;
    int H = std::abs(bh);
    img.w = bw; img.h = H;
    img.rgb.resize(size_t(bw) * H * 3);
    in.seekg(dataOff, std::ios::beg);
    int rowBytes = ((bw * 3 + 3) / 4) * 4;             // rows padded to 4 bytes
    std::vector<uint8_t> row(rowBytes);
    for (int ry = 0; ry < H; ++ry) {
        in.read(reinterpret_cast<char*>(row.data()), rowBytes);
        int y = topDown ? ry : (H - 1 - ry);           // BMP default is bottom-up
        for (int x = 0; x < bw; ++x) {                 // BGR -> RGB
            img.rgb[3 * (y * bw + x) + 0] = row[3 * x + 2];
            img.rgb[3 * (y * bw + x) + 1] = row[3 * x + 1];
            img.rgb[3 * (y * bw + x) + 2] = row[3 * x + 0];
        }
    }
    return bool(in);
}

static bool loadImage(const fs::path& p, Image& img) {
    std::string ext = p.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    if (ext == ".ppm" || ext == ".pgm") return loadPPM(p, img);
    if (ext == ".bmp")                  return loadBMP(p, img);
    return false;
}

// ========================= Grayscale + filtering ============================

using Gray = std::vector<float>;   // w*h, row-major

static Gray toGray(const Image& im) {
    Gray g(size_t(im.w) * im.h);
    for (int y = 0; y < im.h; ++y)
        for (int x = 0; x < im.w; ++x)
            g[y * im.w + x] = 0.299f * im.r(x, y) + 0.587f * im.g(x, y)
                            + 0.114f * im.b(x, y);
    return g;
}

// Separable Gaussian blur with reflected borders.
static Gray gaussianBlur(const Gray& src, int w, int h, double sigma) {
    int rad = std::max(1, int(std::ceil(3 * sigma)));
    std::vector<float> k(2 * rad + 1);
    float sum = 0;
    for (int i = -rad; i <= rad; ++i) {
        k[i + rad] = std::exp(-(i * i) / float(2 * sigma * sigma));
        sum += k[i + rad];
    }
    for (auto& v : k) v /= sum;

    auto refl = [](int i, int n) { return i < 0 ? -i : (i >= n ? 2 * n - 2 - i : i); };
    Gray tmp(src.size()), dst(src.size());
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x) {
            float a = 0;
            for (int i = -rad; i <= rad; ++i) a += k[i + rad] * src[y * w + refl(x + i, w)];
            tmp[y * w + x] = a;
        }
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x) {
            float a = 0;
            for (int i = -rad; i <= rad; ++i) a += k[i + rad] * tmp[refl(y + i, h) * w + x];
            dst[y * w + x] = a;
        }
    return dst;
}

// ====================== Harris corners + descriptors ========================

struct Corner { int x, y; float response; };

static std::vector<Corner> harrisCorners(const Gray& g, int w, int h,
                                         int maxCorners = 1500) {
    // Sobel gradients
    Gray Ix(g.size(), 0), Iy(g.size(), 0);
    for (int y = 1; y < h - 1; ++y)
        for (int x = 1; x < w - 1; ++x) {
            Ix[y*w+x] = (g[(y-1)*w+x+1] + 2*g[y*w+x+1] + g[(y+1)*w+x+1]
                       - g[(y-1)*w+x-1] - 2*g[y*w+x-1] - g[(y+1)*w+x-1]) * 0.125f;
            Iy[y*w+x] = (g[(y+1)*w+x-1] + 2*g[(y+1)*w+x] + g[(y+1)*w+x+1]
                       - g[(y-1)*w+x-1] - 2*g[(y-1)*w+x] - g[(y-1)*w+x+1]) * 0.125f;
        }
    // Structure tensor, smoothed
    Gray Ixx(g.size()), Iyy(g.size()), Ixy(g.size());
    for (size_t i = 0; i < g.size(); ++i) {
        Ixx[i] = Ix[i] * Ix[i];
        Iyy[i] = Iy[i] * Iy[i];
        Ixy[i] = Ix[i] * Iy[i];
    }
    Ixx = gaussianBlur(Ixx, w, h, 1.5);
    Iyy = gaussianBlur(Iyy, w, h, 1.5);
    Ixy = gaussianBlur(Ixy, w, h, 1.5);

    // Harris response  R = det(M) - k * trace(M)^2
    Gray R(g.size(), 0);
    float maxR = 0;
    for (size_t i = 0; i < g.size(); ++i) {
        float det = Ixx[i] * Iyy[i] - Ixy[i] * Ixy[i];
        float tr  = Ixx[i] + Iyy[i];
        R[i] = det - 0.04f * tr * tr;
        maxR = std::max(maxR, R[i]);
    }
    float thresh = 0.005f * maxR;

    // Non-max suppression in a radius, away from borders (descriptor margin)
    const int nms = 4, margin = 12;
    std::vector<Corner> out;
    for (int y = margin; y < h - margin; ++y)
        for (int x = margin; x < w - margin; ++x) {
            float v = R[y * w + x];
            if (v < thresh) continue;
            bool localMax = true;
            for (int dy = -nms; dy <= nms && localMax; ++dy)
                for (int dx = -nms; dx <= nms; ++dx)
                    if (R[(y + dy) * w + x + dx] > v) { localMax = false; break; }
            if (localMax) out.push_back({x, y, v});
        }
    std::sort(out.begin(), out.end(),
              [](const Corner& a, const Corner& b) { return a.response > b.response; });
    if (int(out.size()) > maxCorners) out.resize(maxCorners);
    return out;
}

// Zero-mean, unit-norm 16x16 patch. Matching score = dot product (ZNCC).
struct Descriptor { std::array<float, 256> v; };

static std::vector<Descriptor> describe(const Gray& g, int w,
                                        const std::vector<Corner>& cs) {
    std::vector<Descriptor> ds(cs.size());
    for (size_t i = 0; i < cs.size(); ++i) {
        auto& d = ds[i].v;
        int n = 0;
        float mean = 0;
        for (int dy = -8; dy < 8; ++dy)
            for (int dx = -8; dx < 8; ++dx) {
                float p = g[(cs[i].y + dy) * w + cs[i].x + dx];
                d[n++] = p; mean += p;
            }
        mean /= 256.0f;
        float norm = 0;
        for (auto& p : d) { p -= mean; norm += p * p; }
        norm = std::sqrt(std::max(norm, 1e-12f));
        for (auto& p : d) p /= norm;
    }
    return ds;
}

// Brute-force matching, Lowe-style ratio test on ZNCC-derived distance,
// plus mutual (cross-check) consistency.
static void matchFeatures(const std::vector<Descriptor>& d1,
                          const std::vector<Descriptor>& d2,
                          std::vector<std::pair<int, int>>& matches) {
    auto bestTwo = [](const Descriptor& q, const std::vector<Descriptor>& db,
                      int& b1, float& s1, float& s2) {
        b1 = -1; s1 = -2; s2 = -2;
        for (int j = 0; j < int(db.size()); ++j) {
            float s = 0;
            for (int k = 0; k < 256; ++k) s += q.v[k] * db[j].v[k];
            if (s > s1)      { s2 = s1; s1 = s; b1 = j; }
            else if (s > s2) { s2 = s; }
        }
    };
    matches.clear();
    std::vector<int> back(d2.size(), -1);
    for (int j = 0; j < int(d2.size()); ++j) {
        int b; float s1, s2;
        bestTwo(d2[j], d1, b, s1, s2);
        back[j] = b;
    }
    for (int i = 0; i < int(d1.size()); ++i) {
        int b; float s1, s2;
        bestTwo(d1[i], d2, b, s1, s2);
        if (b < 0 || s1 < 0.6f) continue;                    // absolute quality
        float dist1 = std::sqrt(std::max(0.f, 2 - 2 * s1));  // ZNCC -> distance
        float dist2 = std::sqrt(std::max(0.f, 2 - 2 * s2));
        if (dist1 > 0.85f * dist2) continue;                 // ratio test
        if (back[b] != i) continue;                          // cross-check
        matches.push_back({i, b});
    }
}

// ============================ Linear algebra ================================

// Cyclic Jacobi eigensolver for a symmetric n x n matrix (row-major).
// On return: eig = eigenvalues (descending), V columns = eigenvectors.
static void jacobiEigenSym(std::vector<double> A, int n,
                           std::vector<double>& eig, std::vector<double>& V) {
    V.assign(size_t(n) * n, 0.0);
    for (int i = 0; i < n; ++i) V[i * n + i] = 1.0;
    for (int sweep = 0; sweep < 100; ++sweep) {
        double off = 0;
        for (int p = 0; p < n; ++p)
            for (int q = p + 1; q < n; ++q) off += A[p * n + q] * A[p * n + q];
        if (off < 1e-24) break;
        for (int p = 0; p < n; ++p)
            for (int q = p + 1; q < n; ++q) {
                double apq = A[p * n + q];
                if (std::abs(apq) < 1e-30) continue;
                double theta = (A[q * n + q] - A[p * n + p]) / (2 * apq);
                double t = (theta >= 0 ? 1.0 : -1.0)
                         / (std::abs(theta) + std::sqrt(theta * theta + 1));
                double c = 1.0 / std::sqrt(t * t + 1), s = t * c;
                for (int k = 0; k < n; ++k) {   // A <- J^T A J
                    double akp = A[k * n + p], akq = A[k * n + q];
                    A[k * n + p] = c * akp - s * akq;
                    A[k * n + q] = s * akp + c * akq;
                }
                for (int k = 0; k < n; ++k) {
                    double apk = A[p * n + k], aqk = A[q * n + k];
                    A[p * n + k] = c * apk - s * aqk;
                    A[q * n + k] = s * apk + c * aqk;
                }
                for (int k = 0; k < n; ++k) {   // accumulate V <- V J
                    double vkp = V[k * n + p], vkq = V[k * n + q];
                    V[k * n + p] = c * vkp - s * vkq;
                    V[k * n + q] = s * vkp + c * vkq;
                }
            }
    }
    // sort eigenpairs descending
    std::vector<int> idx(n);
    for (int i = 0; i < n; ++i) idx[i] = i;
    std::sort(idx.begin(), idx.end(),
              [&](int a, int b) { return A[a * n + a] > A[b * n + b]; });
    eig.resize(n);
    std::vector<double> Vs(size_t(n) * n);
    for (int j = 0; j < n; ++j) {
        eig[j] = A[idx[j] * n + idx[j]];
        for (int i = 0; i < n; ++i) Vs[i * n + j] = V[i * n + idx[j]];
    }
    V = std::move(Vs);
}

// SVD of a 3x3 matrix:  M = U * diag(S) * V^T, with det(U) > 0, det(V) > 0.
static void svd3(const Mat3& M, Mat3& U, Vec3& S, Mat3& V) {
    // Eigen-decompose M^T M for V and singular values
    Mat3 MtM = M.transposed() * M;
    std::vector<double> A(9), eig, Vv;
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) A[i * 3 + j] = MtM.m[i][j];
    jacobiEigenSym(A, 3, eig, Vv);
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) V.m[i][j] = Vv[i * 3 + j];
    S = {std::sqrt(std::max(eig[0], 0.0)),
         std::sqrt(std::max(eig[1], 0.0)),
         std::sqrt(std::max(eig[2], 0.0))};
    // U columns: u_i = M v_i / s_i (third column from cross product for stability)
    Vec3 u0 = (M * V.col(0)) * (S.x > 1e-12 ? 1.0 / S.x : 0.0);
    Vec3 u1 = (M * V.col(1)) * (S.y > 1e-12 ? 1.0 / S.y : 0.0);
    u0 = u0.normalized();
    u1 = (u1 - u0 * u0.dot(u1)).normalized();   // re-orthogonalize
    Vec3 u2 = u0.cross(u1);
    U.setCol(0, u0); U.setCol(1, u1); U.setCol(2, u2);
    // Make both proper (det > 0); flipping the 3rd column is safe since s3 ~ 0
    if (V.det() < 0) V.setCol(2, V.col(2) * -1.0);
    if (U.det() < 0) U.setCol(2, U.col(2) * -1.0);
}

// ==================== Essential matrix (8-point + RANSAC) ===================

// Hartley normalization: translate to centroid, scale mean distance to sqrt(2).
static Mat3 normalizePts(const std::vector<Vec2>& pts, std::vector<Vec2>& out) {
    double cx = 0, cy = 0;
    for (auto& p : pts) { cx += p.x; cy += p.y; }
    cx /= pts.size(); cy /= pts.size();
    double md = 0;
    for (auto& p : pts) md += std::hypot(p.x - cx, p.y - cy);
    md /= pts.size();
    double s = (md > 1e-12) ? std::sqrt(2.0) / md : 1.0;
    out.resize(pts.size());
    for (size_t i = 0; i < pts.size(); ++i)
        out[i] = {s * (pts[i].x - cx), s * (pts[i].y - cy)};
    Mat3 T = Mat3::identity();
    T.m[0][0] = s; T.m[0][2] = -s * cx;
    T.m[1][1] = s; T.m[1][2] = -s * cy;
    return T;
}

// 8-point algorithm on normalized camera coordinates; indices select the subset.
static Mat3 eightPoint(const std::vector<Vec2>& p1, const std::vector<Vec2>& p2,
                       const std::vector<int>& idx) {
    std::vector<Vec2> s1(idx.size()), s2(idx.size());
    for (size_t k = 0; k < idx.size(); ++k) { s1[k] = p1[idx[k]]; s2[k] = p2[idx[k]]; }
    std::vector<Vec2> n1, n2;
    Mat3 T1 = normalizePts(s1, n1);
    Mat3 T2 = normalizePts(s2, n2);

    // Build A^T A directly (9x9) from constraint rows x2^T E x1 = 0
    std::vector<double> AtA(81, 0.0);
    for (size_t k = 0; k < n1.size(); ++k) {
        double r[9] = {n2[k].x * n1[k].x, n2[k].x * n1[k].y, n2[k].x,
                       n2[k].y * n1[k].x, n2[k].y * n1[k].y, n2[k].y,
                       n1[k].x,           n1[k].y,           1.0};
        for (int i = 0; i < 9; ++i)
            for (int j = 0; j < 9; ++j) AtA[i * 9 + j] += r[i] * r[j];
    }
    std::vector<double> eig, V;
    jacobiEigenSym(AtA, 9, eig, V);
    Mat3 F;   // eigenvector of the smallest eigenvalue = column 8
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) F.m[i][j] = V[(i * 3 + j) * 9 + 8];

    F = T2.transposed() * F * T1;   // undo normalization

    // Enforce essential-matrix constraint: singular values (s, s, 0)
    Mat3 U, Vt3; Vec3 S;
    svd3(F, U, S, Vt3);
    double s = 0.5 * (S.x + S.y);
    Mat3 D; D.m[0][0] = s; D.m[1][1] = s; D.m[2][2] = 0;
    return U * D * Vt3.transposed();
}

static double sampsonError(const Mat3& E, const Vec2& a, const Vec2& b) {
    Vec3 x1{a.x, a.y, 1}, x2{b.x, b.y, 1};
    Vec3 Ex1  = E * x1;
    Vec3 Etx2 = E.transposed() * x2;
    double num = x2.dot(Ex1);
    double den = Ex1.x * Ex1.x + Ex1.y * Ex1.y + Etx2.x * Etx2.x + Etx2.y * Etx2.y;
    return num * num / std::max(den, 1e-18);
}

// RANSAC over 8-point samples. p1/p2 are in normalized camera coordinates.
static Mat3 findEssentialRANSAC(const std::vector<Vec2>& p1,
                                const std::vector<Vec2>& p2,
                                double inlierThresh, std::vector<char>& inlierMask,
                                std::mt19937& rng) {
    const int N = int(p1.size());
    const double t2 = inlierThresh * inlierThresh;
    std::uniform_int_distribution<int> uni(0, N - 1);
    Mat3 bestE;
    int bestCount = -1;
    for (int it = 0; it < 800; ++it) {
        std::vector<int> idx;
        while (int(idx.size()) < 8) {
            int c = uni(rng);
            if (std::find(idx.begin(), idx.end(), c) == idx.end()) idx.push_back(c);
        }
        Mat3 E = eightPoint(p1, p2, idx);
        int count = 0;
        for (int i = 0; i < N; ++i)
            if (sampsonError(E, p1[i], p2[i]) < t2) ++count;
        if (count > bestCount) { bestCount = count; bestE = E; }
    }
    // Refit on all inliers of the best model
    inlierMask.assign(N, 0);
    std::vector<int> inl;
    for (int i = 0; i < N; ++i)
        if (sampsonError(bestE, p1[i], p2[i]) < t2) { inlierMask[i] = 1; inl.push_back(i); }
    if (inl.size() >= 8) {
        Mat3 E = eightPoint(p1, p2, inl);
        inlierMask.assign(N, 0);
        for (int i = 0; i < N; ++i)
            if (sampsonError(E, p1[i], p2[i]) < t2) inlierMask[i] = 1;
        return E;
    }
    return bestE;
}

// ==================== Triangulation + pose recovery =========================

// Linear (DLT) triangulation from two 3x4 projections P = [R|t]
// (normalized coordinates, K = I). Solves via 4x4 eigen problem.
static Vec3 triangulate(const Mat3& R1, const Vec3& t1,
                        const Mat3& R2, const Vec3& t2,
                        const Vec2& x1, const Vec2& x2, bool& ok) {
    double P1[3][4], P2[3][4];
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) { P1[i][j] = R1.m[i][j]; P2[i][j] = R2.m[i][j]; }
        P1[i][3] = (i == 0 ? t1.x : i == 1 ? t1.y : t1.z);
        P2[i][3] = (i == 0 ? t2.x : i == 1 ? t2.y : t2.z);
    }
    double A[4][4];
    for (int j = 0; j < 4; ++j) {
        A[0][j] = x1.x * P1[2][j] - P1[0][j];
        A[1][j] = x1.y * P1[2][j] - P1[1][j];
        A[2][j] = x2.x * P2[2][j] - P2[0][j];
        A[3][j] = x2.y * P2[2][j] - P2[1][j];
    }
    std::vector<double> AtA(16, 0.0);
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j)
            for (int k = 0; k < 4; ++k) AtA[i * 4 + j] += A[k][i] * A[k][j];
    std::vector<double> eig, V;
    jacobiEigenSym(AtA, 4, eig, V);
    double X = V[0 * 4 + 3], Y = V[1 * 4 + 3], Z = V[2 * 4 + 3], W = V[3 * 4 + 3];
    ok = std::abs(W) > 1e-12;
    return ok ? Vec3{X / W, Y / W, Z / W} : Vec3{};
}

// Decompose E into the 4 candidate (R, t) and pick the one with the most
// points in front of both cameras (cheirality test).
static bool recoverPose(const Mat3& E,
                        const std::vector<Vec2>& p1, const std::vector<Vec2>& p2,
                        const std::vector<char>& mask, Mat3& R, Vec3& t) {
    Mat3 U, V; Vec3 S;
    svd3(E, U, S, V);
    Mat3 W;                     // 90-degree rotation about z
    W.m[0][1] = -1; W.m[1][0] = 1; W.m[2][2] = 1;
    Mat3 Rs[2] = {U * W * V.transposed(), U * W.transposed() * V.transposed()};
    for (auto& Rc : Rs)
        if (Rc.det() < 0)       // ensure proper rotations
            for (int i = 0; i < 3; ++i)
                for (int j = 0; j < 3; ++j) Rc.m[i][j] = -Rc.m[i][j];
    Vec3 ts[2] = {U.col(2), U.col(2) * -1.0};

    Mat3 I = Mat3::identity();
    Vec3 zero{0, 0, 0};
    int bestGood = -1;
    std::vector<double> G[4];
    for (int ri = 0; ri < 2; ++ri)
        for (int ti = 0; ti < 2; ++ti) {
            int good = 0, tested = 0;
            for (size_t k = 0; k < p1.size() && tested < 200; ++k) {
                if (!mask[k]) continue;
                ++tested;
                bool ok;
                Vec3 X = triangulate(I, zero, Rs[ri], ts[ti], p1[k], p2[k], ok);
                if (!ok) continue;
                double z1 = X.z;
                double z2 = (Rs[ri] * X + ts[ti]).z;
                if (z1 > 0 && z2 > 0) ++good;
                G[ri * 2 + ti].push_back(z1);
                G[ri * 2 + ti].push_back(z2);
            }
            if (good > bestGood) { bestGood = good; R = Rs[ri]; t = ts[ti]; }
        }
    return bestGood > 10;
}

// ================================= Main =====================================

int main(int argc, char** argv) {
    unsigned char a = 1; 
    char b = 2;
    short c = 3;
    int d = 4;
    long e = 5;
    float ff = 0.5;
    double gg = 1.5;

    //fs::path dir = (argc > 1) ? argv[1] : "images";
    fs::path dir = "//home//roots//develop2//sfm//cpp_no_dependencies//images";

    // ---------- 1. Load images ----------
    std::vector<fs::path> paths;
    for (const auto& e : fs::directory_iterator(dir)) {
        std::string ext = e.path().extension().string();
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        if (ext == ".ppm" || ext == ".pgm" || ext == ".bmp")
            paths.push_back(e.path());
    }
    std::sort(paths.begin(), paths.end());
    if (paths.size() < 2) {
        std::cerr << "Need >= 2 .ppm/.pgm/.bmp images in " << dir << "\n"
                  << "(convert e.g.:  ffmpeg -i photo.jpg photo.ppm)\n";
        return 1;
    }

    std::vector<Image> imgs(paths.size());
    for (size_t i = 0; i < paths.size(); ++i) {
        if (!loadImage(paths[i], imgs[i])) {
            std::cerr << "Failed to load " << paths[i] << "\n";
            return 1;
        }
    }
    const int w = imgs[0].w, h = imgs[0].h;
    std::cout << "Loaded " << imgs.size() << " images (" << w << "x" << h << ")\n";

    // Approximate intrinsics: focal ~ image width, principal point = center.
    const double f = double(w), cx = w / 2.0, cy = h / 2.0;

    // ---------- 2. Features per image ----------
    std::vector<std::vector<Corner>>     corners(imgs.size());
    std::vector<std::vector<Descriptor>> descs(imgs.size());
    for (size_t i = 0; i < imgs.size(); ++i) {
        Gray g = gaussianBlur(toGray(imgs[i]), w, h, 1.0);
        corners[i] = harrisCorners(g, w, h);
        descs[i]   = describe(g, w, corners[i]);
        std::cout << paths[i].filename().string() << ": "
                  << corners[i].size() << " corners\n";
    }

    // ---------- 3. Incremental chaining ----------
    // Global pose of camera i:  x_cam = R_i * x_world + t_i.  Camera 0 = identity.
    Mat3 R_prev = Mat3::identity();
    Vec3 t_prev{0, 0, 0};
    std::vector<Vec3>                    cloud;
    std::vector<std::array<uint8_t, 3>>  colors;
    std::mt19937 rng(42);

    for (size_t i = 0; i + 1 < imgs.size(); ++i) {
        std::vector<std::pair<int, int>> matches;
        matchFeatures(descs[i], descs[i + 1], matches);
        if (matches.size() < 20) {
            std::cout << "[pair " << i << "] only " << matches.size()
                      << " matches, skipping\n";
            continue;
        }

        // Pixel -> normalized camera coordinates (K^-1 applied)
        std::vector<Vec2> p1(matches.size()), p2(matches.size());
        for (size_t k = 0; k < matches.size(); ++k) {
            const Corner& c1 = corners[i][matches[k].first];
            const Corner& c2 = corners[i + 1][matches[k].second];
            p1[k] = {(c1.x - cx) / f, (c1.y - cy) / f};
            p2[k] = {(c2.x - cx) / f, (c2.y - cy) / f};
        }

        // Essential matrix + relative pose
        std::vector<char> mask;
        Mat3 E = findEssentialRANSAC(p1, p2, 1.5 / f, mask, rng);
        Mat3 R_rel; Vec3 t_rel;
        if (!recoverPose(E, p1, p2, mask, R_rel, t_rel)) {
            int inl = int(std::count(mask.begin(), mask.end(), 1));
            std::cout << "[pair " << i << "] pose recovery failed ("
                      << matches.size() << " matches, " << inl
                      << " inliers), skipping\n";
            continue;
        }

        // Compose into global poses.  |t_rel| = 1: scale is arbitrary per pair.
        Mat3 R_cur = R_rel * R_prev;
        Vec3 t_cur = R_rel * t_prev + t_rel;

        // Triangulate inliers in the global frame
        int kept = 0;
        for (size_t k = 0; k < matches.size(); ++k) {
            if (!mask[k]) continue;
            bool ok;
            Vec3 X = triangulate(R_prev, t_prev, R_cur, t_cur, p1[k], p2[k], ok);
            if (!ok) continue;
            double z1 = (R_prev * X + t_prev).z;
            double z2 = (R_cur  * X + t_cur ).z;
            if (z1 <= 0 || z2 <= 0 || X.norm() > 100.0) continue;

            const Corner& c1 = corners[i][matches[k].first];
            cloud.push_back(X);
            colors.push_back({imgs[i].r(c1.x, c1.y),
                              imgs[i].g(c1.x, c1.y),
                              imgs[i].b(c1.x, c1.y)});
            ++kept;
        }
        int inliers = int(std::count(mask.begin(), mask.end(), 1));
        std::cout << "[" << paths[i].filename().string() << " -> "
                  << paths[i + 1].filename().string() << "] "
                  << matches.size() << " matches, " << inliers
                  << " inliers, " << kept << " points\n";

        R_prev = R_cur;
        t_prev = t_cur;
    }

    if (cloud.empty()) {
        std::cerr << "No points reconstructed - check overlap, order, texture.\n";
        return 1;
    }

    // ---------- 4. Write colored PLY ----------
    std::ofstream ply("cloud.ply");
    ply << "ply\nformat ascii 1.0\n"
        << "element vertex " << cloud.size() << "\n"
        << "property float x\nproperty float y\nproperty float z\n"
        << "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        << "end_header\n";
    for (size_t k = 0; k < cloud.size(); ++k)
        ply << cloud[k].x << " " << cloud[k].y << " " << cloud[k].z << " "
            << int(colors[k][0]) << " " << int(colors[k][1]) << " "
            << int(colors[k][2]) << "\n";

    std::cout << "\nWrote cloud.ply with " << cloud.size() << " points\n";
    return 0;
}
