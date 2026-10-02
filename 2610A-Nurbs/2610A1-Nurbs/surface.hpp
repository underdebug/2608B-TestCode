#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace nurbs
{
struct P
{
    double x = 0, y = 0, z = 0;
    P operator+(P b) const
    {
        return {x + b.x, y + b.y, z + b.z};
    }
    P operator*(double s) const
    {
        return {x * s, y * s, z * s};
    }
};
using Grid = std::array<std::array<P, 10>, 10>;
using Matrix = std::array<std::array<double, 10>, 10>;
inline std::array<double, 14> knots()
{
    std::array<double, 14> k{};
    for (int j = 1; j <= 6; ++j)
        k[j + 3] = double(j + 1) / 9;
    for (int j = 10; j < 14; ++j)
        k[j] = 1;
    return k;
}
inline std::array<double, 10> basis(double t)
{
    auto k = knots();
    std::array<double, 13> b{};
    if (t >= 1)
    {
        std::array<double, 10> r{};
        r[9] = 1;
        return r;
    }
    for (int i = 0; i < 13; ++i)
        b[i] = (t >= k[i] && t < k[i + 1]);
    for (int d = 1; d <= 3; ++d)
        for (int i = 0; i < 13 - d; ++i)
        {
            double a = k[i + d] - k[i], c = k[i + d + 1] - k[i + 1];
            b[i] = (a ? (t - k[i]) * b[i] / a : 0) + (c ? (k[i + d + 1] - t) * b[i + 1] / c : 0);
        }
    std::array<double, 10> r{};
    std::copy_n(b.begin(), 10, r.begin());
    return r;
}
inline std::array<P, 10> solve(Matrix a, std::array<P, 10> b)
{
    for (int i = 0; i < 10; ++i)
    {
        int p = i;
        for (int j = i + 1; j < 10; ++j)
            if (std::abs(a[j][i]) > std::abs(a[p][i]))
                p = j;
        if (std::abs(a[p][i]) < 1e-14)
            throw std::runtime_error("Singular interpolation matrix");
        std::swap(a[i], a[p]);
        std::swap(b[i], b[p]);
        double d = a[i][i];
        for (int j = i; j < 10; ++j)
            a[i][j] /= d;
        b[i] = b[i] * (1 / d);
        for (int r = 0; r < 10; ++r)
            if (r != i)
            {
                double f = a[r][i];
                for (int j = i; j < 10; ++j)
                    a[r][j] -= f * a[i][j];
                b[r] = b[r] + b[i] * (-f);
            }
    }
    return b;
}
inline Grid data()
{
    Grid d;
    for (int i = 0; i < 10; ++i)
        for (int j = 0; j < 10; ++j)
        {
            double x = 2. * i / 9 - 1, y = 2. * j / 9 - 1;
            d[i][j] = {x, y, 0.35 * std::sin(3 * x) * std::cos(3 * y) + 0.15 * x * y};
        }
    return d;
}
inline Grid interpolate(const Grid &d)
{
    Matrix a;
    for (int i = 0; i < 10; ++i)
        a[i] = basis(double(i) / 9);
    Grid t, c;
    for (int j = 0; j < 10; ++j)
    {
        std::array<P, 10> b;
        for (int i = 0; i < 10; ++i)
            b[i] = d[i][j];
        b = solve(a, b);
        for (int i = 0; i < 10; ++i)
            t[i][j] = b[i];
    }
    for (int i = 0; i < 10; ++i)
        c[i] = solve(a, t[i]);
    return c;
}
// All weights are 1: a polynomial B-spline is a special case of NURBS.
inline P evaluate(const Grid &c, double u, double v)
{
    auto a = basis(u), b = basis(v);
    P p;
    for (int i = 0; i < 10; ++i)
        for (int j = 0; j < 10; ++j)
            p = p + c[i][j] * (a[i] * b[j]);
    return p;
}
inline double error(const Grid &d, const Grid &c)
{
    double e = 0;
    for (int i = 0; i < 10; ++i)
        for (int j = 0; j < 10; ++j)
        {
            P p = evaluate(c, double(i) / 9, double(j) / 9) + d[i][j] * (-1);
            e = std::max(e, std::sqrt(p.x * p.x + p.y * p.y + p.z * p.z));
        }
    return e;
}
struct Vertex
{
    float x, y, z, r, g, b;
};
inline std::vector<Vertex> mesh(const Grid &d, const Grid &c)
{
    std::vector<Vertex> v;
    auto line = [&](P a, P b, bool red = false)
    {
        for (P p : {a, b})
            v.push_back({float(p.x), float(p.y), float(p.z), red ? 1.f : 0.15f, red ? 0.2f : 0.75f,
                         red ? 0.15f : 1.f});
    };
    constexpr int N = 100;
    for (int i = 0; i <= N; ++i)
        for (int j = 0; j < N; ++j)
        {
            line(evaluate(c, double(i) / N, double(j) / N),
                 evaluate(c, double(i) / N, double(j + 1) / N));
            line(evaluate(c, double(j) / N, double(i) / N),
                 evaluate(c, double(j + 1) / N, double(i) / N));
        }
    for (auto row : d)
        for (auto p : row)
        {
            double s = .018;
            line(p + P{-s, 0, 0}, p + P{s, 0, 0}, true);
            line(p + P{0, -s, 0}, p + P{0, s, 0}, true);
            line(p + P{0, 0, -s}, p + P{0, 0, s}, true);
        }
    return v;
}
} // namespace nurbs
