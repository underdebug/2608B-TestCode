
#ifndef MAT_BAND_H
#define MAT_BAND_H

void	matBandSetValue(double* A, int m, double v, int i, int j);
void	matBandAddValue(double* A, int m, double v, int i, int j);
double	matBandGetValue(double* A, int m, int i, int j);
void	matBand(double* A, double* b1, double* b2, int n, int m);

#endif //MAT_BAND_H