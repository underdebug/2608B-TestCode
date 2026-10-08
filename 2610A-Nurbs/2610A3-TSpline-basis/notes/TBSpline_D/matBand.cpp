
#include "StdAfx.h"
#include "matBand.h"
#include <stdio.h>
#include <malloc.h>
#include <math.h>

#define _min(a, b)	(a < b ? a : b)
#define _max(a, b)	(a > b ? a : b)

void matBandSetValue(double* A, int m, double v, int i, int j)
{
	if(abs(j-i) <= m)
		A[i*(2*m+1) + j-i+m] = v;
}

void matBandAddValue(double* A, int m, double v, int i, int j)
{
	if(abs(j-i) <= m)
		A[i*(2*m+1) + j-i+m] += v;
}

double matBandGetValue(double* A, int m, int i, int j)
{
	if(abs(j-i) <= m)
		return A[i*(2*m+1) + j-i+m];
	return 0.0;
}

void matBand(double* A, double* b1, double* b2, int n, int m)
{
	int i,ii,jj,c,c1,m1,ii1,jj1;
	double k;
	c  = 0; 
	m1 = m+1;
	c1 = (c+m) % m1;
	
	double* M = (double*) calloc (n*m1, sizeof(double));	
	for(i=0; i<n; i++){
		if(i == 0){
			ii1 = _min(2*m+1, n);
			jj1 = _min(m1, n);
			for(ii=0; ii<ii1; ii++)
				for(jj=0; jj<jj1; jj++)
					M[ii*m1 + jj] = matBandGetValue(A, m, ii, jj);
		}else{
			c  = (c+1) % m1;
			c1 = (c+m) % m1;
			jj = i + m;
			if(jj < n){			
				ii1 = _min(n, i+2*m1);
				for(ii=_max(0, i-1-m); ii<ii1; ii++)
					M[ii*m1 + c1] = matBandGetValue(A, m, ii, jj);
			}
		}
		
		ii1 = _min(i+m1, n);
		for(ii=0; ii<ii1; ii++){
			if(ii == i) continue;
			k = M[ii*m1 + c] / M[i*m1 + c];
			
			jj1 = _min(i+m1, n);
			for(jj=0; jj<m1; jj++)
				M[ii*m1 + jj] -= k * M[i*m1 + jj];
			b1[ii] -= k * b1[i];
			b2[ii] -= k * b2[i];
		}
		
		matBandSetValue(A, m, M[i*m1+c], i, i);
	}
	free(M);
	
	for(i=0; i<n; i++){
		b1[i] /= matBandGetValue(A, m, i, i);
		b2[i] /= matBandGetValue(A, m, i, i);
	}
}