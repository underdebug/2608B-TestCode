// pgm.h -- tiny dependency-free PGM (portable graymap) reader/writer.
// Handles both binary ("P5") and ASCII ("P2"), skips '#' comment lines.
#ifndef PGM_H
#define PGM_H
#include <vector>
#include <string>
#include <fstream>
#include <cctype>
#include <cmath>

struct Image {
    int W = 0, H = 0;
    std::vector<double> p;             // pixel values, one double per pixel
    double& at(int x, int y) { return p[y * W + x]; }
};

inline void pgm_skip_ws_and_comments(std::istream& f) {
    int c;
    while ((c = f.peek()) != EOF) {
        if (c == '#') { std::string line; std::getline(f, line); }
        else if (std::isspace(c)) f.get();
        else break;
    }
}

inline bool readPGM(const std::string& path, Image& im) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    std::string magic; f >> magic;
    int maxv;
    pgm_skip_ws_and_comments(f); f >> im.W;
    pgm_skip_ws_and_comments(f); f >> im.H;
    pgm_skip_ws_and_comments(f); f >> maxv;
    f.get();                                   // consume the single whitespace after maxval
    im.p.resize(static_cast<size_t>(im.W) * im.H);
    if (magic == "P5") {
        for (auto& v : im.p) v = static_cast<unsigned char>(f.get());
    } else if (magic == "P2") {
        int t; for (auto& v : im.p) { f >> t; v = t; }
    } else return false;
    return true;
}

inline bool writePGM(const std::string& path, const Image& im) {
    std::ofstream f(path, std::ios::binary);
    if (!f) return false;
    f << "P5\n" << im.W << " " << im.H << "\n255\n";
    for (double v : im.p) {
        int iv = static_cast<int>(std::floor(v + 0.5));
        iv = iv < 0 ? 0 : (iv > 255 ? 255 : iv);
        f.put(static_cast<unsigned char>(iv));
    }
    return true;
}
#endif
