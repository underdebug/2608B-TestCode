
#include "stdafx.h"
#include "TBspline.h"
#include "matBand.h"
#include "Filter.h"
#include <math.h>
#include "GlobalMicroDef.h"

static double fi(int k, double x, double pi, double di);
static double fi(int k, double x, int i, double* p, double* d);
static double sigma_k3(int j, int i, int n, double* p, double* d);
static double sigma(int k, int j, int i, int n, double* p, double* d);
static double sigma(int k, int i, int n, double* p, double* d);
static double beta_k3_j_2(int l, int i, int n, double* p, double* d);
static double beta_k3_j_1(int l, int i, int n, double* p, double* d);
static double beta_k3_j0(int l, int i, int n, double* p, double* d);
static double beta_k3(int l, int i, int j, int n, double*p, double* d);
static double beta_k4_l_2(int i, int j, int n, double* p, double* d);
static double beta_k4_l_1(int i, int j, int n, double* p, double* d);
static double beta_k4_l0(int i, int j, int n, double* p, double* d);
static double beta_k4_l1(int i, int j, int n, double* p, double* d);
static double beta_k4(int l, int i, int j, int n, double* p, double* d);

double fi(int k, double x, double pi, double di)
{
	if(di < FloatTypeZeroValue) 
		return 0.0;
	double val = 0.0;
	if(pi != 0.0){
		switch(k){
		case 3:
			val = (cosh(pi*x)-1) / (pi * sinh(pi*di));
			return val;
			break;
		case 4:
			val = (sinh(pi*x)-pi*x) / (pi * pi * sinh(pi*di));
			return val;
			break;		
		}
	}
	val = x*x / (2*di);
	return val;
}

double fi(int k, double x, int i, double* p, double* d)
{
	double val = fi(k, x, p[i], d[i]);
	return val;
}

double sigma_k3(int j, int i, int n, double* p, double* d)
{
	double val = 0.0;
	for(int l=j; l<i; l++)
		val += (beta_k3(-2, l, j, n, p, d) + beta_k3(-1, l, j, n, p, d)) * fi(4, d[l], l, p, d) + d[l]*beta_k3(0, l, j, n, p, d);
	return val;
}

double sigma(int k, int j, int i, int n, double* p, double* d)
{	
	double val = 0.0;
	switch(k){
	case 3:
		val = sigma_k3(j, i, n, p, d);
		return val;
		break;
	}
	return val;
}

double sigma(int k, int i, int n, double* p, double* d)
{
	double val = 0.0;
	if(k >= 3){
		val = sigma(k, i, i+k, n, p, d);
		return val;
	}else if(k >= 2){
		val = fi(3, d[i], i, p, d) + fi(3, d[i+1], i+1, p, d);
		return val;
	}
	return val;	
}

double beta_k3_j_2(int l, int i, int n, double* p, double* d)
{
	double val = 0.0;
	switch(l){
	case -2:
		return 0.0;
		break;
	case -1:
		if(i-1>1 && i-1<n){
			val = 1.0 / sigma(2, i-1, n, p, d);
			return val;
		}
		break;
	case 0:
		return 0.0;
		break;
	}
	return 0.0;
}

double beta_k3_j_1(int l, int i, int n, double* p, double* d)
{
	double val = 0.0;
	switch(l){
	case -2:
		if(i>1 && i<n){
			val = -1.0 / sigma(2, i, n, p, d);
			return val;
		}
		break;
	case -1:
		if(i-1>1 && i-1<n){
			val = -1.0 / sigma(2, i-1, n, p, d);
			return val;
		}
		break;
	case 0:
		return 1.0;
		break;
	}
	return 0.0;
}

double beta_k3_j0(int l, int i, int n, double* p, double* d)
{
	double val = 0.0;
	switch(l){
	case -2:
		if(i>1 && i<n){
			val = 1.0 / sigma(2, i, n, p, d);
			return val;
		}
		break;
	case -1:
		return 0.0;
		break;
	case 0:
		return 0.0;
		break;
	}
	return 0.0;
}

double beta_k3(int l, int i, int j, int n, double*p, double* d)
{
	double val = 0.0;
	int seg = j-i;
	switch(seg){
	case -2:
		val = beta_k3_j_2(l, i, n, p, d);
		return val;
		break;
	case -1:
		val = beta_k3_j_1(l, i, n, p, d);
		return val;
		break;
	case 0:
		val = beta_k3_j0(l, i, n, p, d);
		return val;
		break;
	}
	return 0.0;
}

double beta_k4_l_2(int i, int j, int n, double* p, double* d)
{
	double val = 0.0;
	if(j>0) 
		val += beta_k3(-2, i, j, n, p, d) / sigma(3, j, n, p, d);
	if(j+1<n)
		val -= beta_k3(-2, i, j+1, n, p, d)/ sigma(3, j+1, n, p, d);
	return val;
}

double beta_k4_l_1(int i, int j, int n, double* p, double* d)
{
	double val = 0.0;
	if(j+1<n)
		val += beta_k3(-1, i, j+1, n, p, d) / sigma(3, j+1, n, p, d);
	if(j>0)
		val -= beta_k3(-1, i, j, n, p, d) / sigma(3, j, n, p, d);
	return val;
}

double beta_k4_l0(int i, int j, int n, double* p, double* d)
{
	double val = 0.0;
	if(j>0 && j<n) 
		val += (sigma(3, j, i, n, p, d) + beta_k3(-1, i, j, n, p, d) * fi(4, d[i], i, p, d)) / sigma(3, j, n, p, d);
	else
		val += 1.0;

	if(j+1<n)
		val -= (sigma(3, j+1, i, n, p, d) + beta_k3(-1, i, j+1, n, p, d) * fi(4, d[i], i, p, d)) / sigma(3, j+1, n, p, d);
	return val;
}

double beta_k4_l1(int i, int j, int n, double* p, double* d)
{
	double val = 0.0;
	if(j>0) 
		val += d[i]*beta_k3(0, i, j, n, p, d) / sigma(3, j, n, p, d);
	if(j+1<n)
		val -= d[i]*beta_k3(0, i, j+1, n, p, d) / sigma(3, j+1, n, p, d);
	return val;
}

double beta_k4(int l, int i, int j, int n, double* p, double* d)
{
	double val = 0.0;
	switch(l){
	case -2:
		val = beta_k4_l_2(i, j, n, p, d);
		return val;
		break;
	case -1:
		val = beta_k4_l_1(i, j, n, p, d);
		return val;
		break;
	case 0:
		val = beta_k4_l0(i, j, n, p, d);
		return val;
		break;
	case 1:
		val = beta_k4_l1(i, j, n, p, d);
		return val;
		break;	
	}
	return 0.0;
}

static void tbsIn(double* t, int i0, double t0, double* p, double* d, double* CC, double* b)
{
	double* cc = CC + i0*16, fix[2];
	fix[0] = fi(4, t0-t[i0+3], i0+3, p, d);
	fix[1] = fi(4, t[i0+4]-t0, i0+3, p, d);
	b[0] = cc[0] * fix[0] + cc[1] * fix[1] + cc[2] + cc[3] * t0;
	b[1] = cc[4] * fix[0] + cc[5] * fix[1] + cc[6] + cc[7] * t0;
	b[2] = cc[8] * fix[0] + cc[9] * fix[1] + cc[10]+ cc[11]* t0;
	b[3] = cc[12]* fix[0] + cc[13]* fix[1] + cc[14]+ cc[15]* t0;	
}

static double distance(Vector* p1, Vector* p2)
{
	double val = sqrt((p1->x-p2->x)*(p1->x-p2->x) + (p1->y-p2->y)*(p1->y-p2->y));
	return val;
}

static double getLength(Vector* pt, int sz)
{
	double L = 0.0;
	for(int i=1; i<sz; i++)
		L += distance(&pt[i-1], &pt[i]);
	return L;
}

static void calcTD(Vector* pt, int n, double* t, double* d, double L)
{
	// 0 1 2 => 3 4 ... n-1 n => n+1 n+2 n+3
	t[1] = t[2] = t[3] = t[0] = 0.0;
	for(int i=4; i<=n; i++)
		t[i] = t[i-1] + distance(&pt[i-4], &pt[i-3]);
	t[n+1] = t[n+2] = t[n+3] = t[n];
                               
	for(int i=0; i<n+3; i++)
		d[i] = t[i+1] - t[i];
}

static void calcP(double pp, int n, double* p)
{
	for(int i=0; i<n; i++)
		p[i] = pp;
}

static void calcCoeff(double* t, double* p, double* d, int n, double* CC)
{
	double *cc = CC, c1;
	for(int i=3; i<n; i++){
		for(int j=i-3; j<=i; j++){
			c1    = beta_k4( 1, i, j, n, p, d);
			cc[0] = beta_k4(-2, i, j, n, p, d);
			cc[1] = beta_k4(-1, i, j, n, p, d);
			cc[2] = beta_k4( 0, i, j, n, p, d) - c1 * t[i] / d[i];
			cc[3] = c1 / d[i];
			cc += 4;
		}
	}
}

static void getLinearPosition(Vector* pt, int i, double t, double& x, double& y)
{
	x = pt[i].x*(1-t) + pt[i+1].x*t;
	y = pt[i].y*(1-t) + pt[i+1].y*t;
}

static void calcAXY(Vector* pt, int sz, int n, double ts, double* t, double* p, double* d, double* CC, double* B, double* AX, double* AY)
{
	double s=0.0, b[4], x, y, w;
	int i;
	for(i=0; i<sz-1; i++){
		for(double t0=0.0; t0<1.0; t0+=ts){
			getLinearPosition(pt, i, t0, x, y);
			
			w = 1.0;
			if(i == 0 && t0 == 0.0)
				w = 20.0/ts;
 			if(i != 0 && t0 == 0.0)
 				w = 0.2;

			s = t[i+3] + t0*d[i+3];
			if(s > t[i+4]) s = t[i+3];

			tbsIn(t, i, s, p, d, CC, b);

			for(int ii=i; ii<i+4; ii++){
				for(int jj=i; jj<i+4; jj++)
					matBandAddValue(B, 3, b[ii-i] * b[jj-i] * w, ii, jj);
				AX[ii] += b[ii-i] * x * w;
				AY[ii] += b[ii-i] * y * w;
			}
		}
	}
	i = sz-2;
	s = t[i+4];

	tbsIn(t, i, s, p, d, CC, b);

	w = 20.0/ts;
	for(int ii=i; ii<i+4; ii++){
		for(int jj=i; jj<i+4; jj++)
			matBandAddValue(B, 3, b[ii-i] * b[jj-i] * w, ii, jj);
		AX[ii] += b[ii-i] * pt[sz-1].x * w;
		AY[ii] += b[ii-i] * pt[sz-1].y * w;
	}

	matBand(B, AX, AY, n, 3);
}

static double distance2(double a, double b, double c, const Vector& p)
{
	double L = a * p.x + b * p.y + c;
	return L*L;
}
static double distance2(const Vector& p1, const Vector& p2)
{
	return (p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y);
}
static double findMaxH(Vector* pt, int ns, int ne, int& nn)
{
	double a, b, c;
	a = pt[ne].y - pt[ns].y;
	b = pt[ns].x - pt[ne].x;
	c = (pt[ne].x - pt[ns].x) * pt[ns].y - (pt[ne].y - pt[ns].y) * pt[ns].x;

	double maxH = 0.0, H;
	if(a == 0.0 && b == 0.0 && c == 0.0){
		for(int i=ns+1; i<ne; i++){
			H = distance2(pt[ns], pt[i]);
			if(H > maxH){
				maxH = H;
				nn = i;
			}
		}
	}else{	
		for(int i=ns+1; i<ne; i++){
			H = distance2(a, b, c, pt[i]);
			if(H > maxH){
				maxH = H;
				nn = i;
			}
		}
	}
	return maxH;
}
static void filter(Vector* pt, unsigned char* tag, int ns, int ne, double h, int& num)
{
	if(ne - ns < 2) return;
	int nn;
	double maxH = findMaxH(pt, ns, ne, nn);
	if(maxH < h){
		for(int i=ns+1; i<ne; i++){
			tag[i] = 1;
			num--;
		}
	}else{
		filter(pt, tag, ns, nn, h, num);
		filter(pt, tag, nn, ne, h, num);
	}
}

static int calcTbsAllPt(double* AX, double* AY, double* CC, int sz, double step, double* t, double* d, double* p, Vector* pt, int& num)
{
	double s, b[4];
	Vector pos;
	
	num = 0;
	for(int i=0; i<sz-1; i++){
		int	nn = max(int(d[i+3]/step), 1);		
		double ss = d[i+3] / nn;
		if(i == sz-2) nn++;
		
		for(int j=0; j<nn; j++){
			s = t[i+3] + j*ss;
			if(s > t[i+4]) s = t[i+4];
			
			tbsIn(t, i, s, p, d, CC, b);

			pt[num].x = AX[i+0]*b[0] + AX[i+1]*b[1] + AX[i+2]*b[2] + AX[i+3]*b[3];
			pt[num].y = AY[i+0]*b[0] + AY[i+1]*b[1] + AY[i+2]*b[2] + AY[i+3]*b[3];	
			pt[num].z = ((t[i+4] - s) / d[i+3]) * pt[i].z + ((s - t[i+3]) / d[i+3]) * pt[i+1].z;
			
			num++;
		}
	}
	return num;
}	

static void* newbuffer(void* buffer, int szbuf)
{
	if(!buffer)
		return (void*) malloc (szbuf);
	else
		return (void*) realloc (buffer, szbuf);
}

static void putPtBack(Vector*& pt, int& sz, int& szall, Vector* _pt, unsigned char* tag, int num, int numAll)
{
	if(szall < num){
		szall = 2 * num;
		pt = (Vector*) newbuffer (pt, szall* sizeof(Vector));
	}
	sz = num;
	
	Vector* ppt = pt;
	for(int i=0; i<numAll; i++){
		if(tag[i] != 1)
			memcpy(ppt++, &_pt[i], sizeof(Vector));
	}
}


//void*&	buf				样条基函数需要的缓冲
//int&		szbuf			样条基函数需要的总计缓冲大小
//int		n				基函数行列数
//int		nseg			需要插入的段数
//double*&	t				样条需要的参数
//double*&	d				...
//double*&	p				...
//double*&	B				...
//double*&	AX				...
//double*&	AY				...
//double*&	CC				样条系数存储
//unsigned	char*& tag		导出点的标记
//Vector*& pt				所有的导出点
static void initMem(void*& buf, int& szbuf, int n, int nseg, 
					double*& t, double*& d, double*& p, double*& B, double*& AX, double*& AY, double*& CC, 
					unsigned char*& tag, Vector*& pt)
{
	int szbuf1 = (n+4 + n+4 + n+4 + n*7 + n + n + n*16) * sizeof(double);
	int szbuf2 = nseg + nseg * sizeof(Vector);
	
	if(szbuf < szbuf1+szbuf2){
		szbuf = 2 * (szbuf1+szbuf2);
		buf   = newbuffer (buf, szbuf);
	}
	
	memset(buf, 0, szbuf1+szbuf2);
	double* buf1 = (double*) buf;
	unsigned char* buf2 = (unsigned char*) buf + szbuf1;
	
	t	= buf1;		//n+4
	d	= t	 + n+4;	//n+4
	p	= d	 + n+4;	//n+4
	B	= p  + n+4;	//n*7
	AX	= B  + n*7;	//n
	AY	= AX + n;	//n
	CC  = AY + n;	//n*16
	
	tag = buf2;
	pt = (Vector*) (tag + nseg);
}

//Vector*&	pt			导入点 && 导出点 
//int&			sz			导入点数量 && 导出点数量
//int&			szall		存储点的实际存储空间大小
//double		pp			张力系数
//double		step		插入步长
//double		maxh		最大高度限差
//void*&		buf			临时缓冲区
//int&			szbuf		临时缓冲区大小
bool tbsInterp(Vector*& pt, int& sz, int& szall, double pp, double step, double maxh, void*& buf, int& szbuf, int ii)
{
	if(sz<3) return false;
	int n = sz+2; //基函数个数(n),矩阵行列数(n)

	double L = getLength(pt, sz);
	int nseg = int(L/step) + sz;

	double *t, *d, *p, *B, *AX, *AY, *CC;	
	unsigned char* tag;
	Vector* ptAll;
	initMem(buf, szbuf, n, nseg,  t, d, p, B, AX, AY, CC,  tag, ptAll);

	calcTD(pt, n, t, d, L);
	calcP(pp, n, p);


	calcCoeff(t, p, d, n, CC);

	calcAXY(pt, sz, n, 1.0/10, t, p, d, CC, B, AX, AY);


	char strFile[1024] = {0};
	FILE* fp ;

	sprintf(strFile, "D:\\temp\\Ctrl\\%03d.dat", ii+1);
	fp = fopen(strFile, "wb");
	fwrite(AX, sz, sizeof(double), fp);
	fwrite(AY, sz, sizeof(double), fp);
	fclose(fp);


	int numAll;
	calcTbsAllPt(AX, AY, CC, sz, step, t, d, p, ptAll, numAll);

	memcpy(&ptAll[0], &pt[0], sizeof(Vector));
	memcpy(&ptAll[numAll-1], &pt[sz-1], sizeof(Vector));

	int num = numAll;
	filter(ptAll, tag, 0, numAll-1, maxh, num);

	putPtBack(pt, sz, szall, ptAll, tag, num, numAll);

	return true;
}

CTBspline::CTBspline()
{
	pt = NULL;
	szall = 0;
	buf = NULL;
	szbuf = NULL;
}

CTBspline::~CTBspline()
{
	if(pt) free(pt); pt=NULL;
	if(buf) free(buf); buf=NULL;
}

bool CTBspline::interp(std::vector<Vector>& vecPos, std::vector<Vector>& vecPosInterp, double pp, double step, double maxh, int ii)
{
	if(vecPos.size() == 0) return false;
	CFilter::discardRepeatPos(vecPos, 0.0001);
	CFilter::insertCornerPos(vecPos, 30.0);
	CFilter::splitPolyline(vecPos, 300.0);

	int sz = vecPos.size();
	if(sz <= 0) return false;
	if(!pt){
		szall = 2 * sz;
		pt = (Vector*) malloc (szall * sizeof(Vector));
	}else{
		if(szall < sz){
			szall = 2 * sz;
			pt = (Vector*) realloc (pt, szall * sizeof(Vector));
		}
	}
	
	Vector* ppt = pt;
	for(int i=0; i<vecPos.size(); i++){
		ppt->x = vecPos[i].x;
		ppt->y = vecPos[i].y;
		ppt->z = vecPos[i].z;
		ppt++;
	}
	
	tbsInterp(pt, sz, szall, pp, step, maxh, buf, szbuf, ii);
	for(int i=0; i<sz; i++)
		vecPosInterp.push_back(pt[i]);
	return true;
}
/*
static bool isSqure(Vector* pt1, Vector* pt, Vector* pt2, double th)
{
	double x1 = pt1->x - pt->x;
	double y1 = pt1->y - pt->y;
	double x2 = pt2->x - pt->x;
	double y2 = pt2->y - pt->y;
	
	double d1 = sqrt(x1*x1 + y1*y1);
	double d2 = sqrt(x2*x2 + y2*y2);
	
	if(fabs(x1*x2 + y1*y2) < d1 * d2 * fabs(cos((90+th) * 3.1415926 / 180.0)))
		return true;
	return false;
}
static bool isParallel(Vector* p1, Vector* p2, Vector* p3, Vector* p4, double th)
{
#define PI 3.14159265358979
	double alpha1 = atan2(p2->y - p1->y, p2->x - p1->x);
	double alpha2 = atan2(p3->y - p4->y, p3->x - p4->x);
	double alpha  = fabs(alpha1 - alpha2);				
	if(alpha > PI) alpha = 2.0*PI - alpha;				
	if(alpha < th*PI/180.0) return true;				
	return false;
}
static void append(std::vector<Vector>& vecPos, std::vector<Vector>& vecAdd)
{
	int ns = vecPos.size() == 0 ? 0 : 1;
	for(int i=ns; i<vecAdd.size(); i++)
		vecPos.push_back(vecAdd[i]);	
}
bool CTBspline::squreInterp(std::vector<Vector>& vecPos, std::vector<Vector>& vecPosInterp, double pp, double step, double maxh, double theta)
{
	if(vecPos.size() == 0) return false;
	CFilter::discardRepeatPos(vecPos, 0.0001);

	SortArray<int, int> tagSplit;
	for(int i=1; i<vecPos.size()-1; i++){
		if(isSqure(&vecPos[i-1], &vecPos[i], &vecPos[i+1], 10.0))
			tagSplit.push_back(i);			
	}
	for(int i=1; i<vecPos.size()-2; i++){
		if(isParallel(&vecPos[i-1], &vecPos[i], &vecPos[i+1], &vecPos[i+2], 10.0)){
			tagSplit.push_back(i);
			tagSplit.push_back(i+1);
		}
	}
	tagSplit.push_back(0);
	tagSplit.push_back(vecPos.size()-1);
	tagSplit.sortLess();

	std::vector<Vector> vecPosSplit;
	for(int i=1; i<tagSplit.size(); i++){
		vecPosSplit.removeAll();
		for(int ii=tagSplit[i-1]; ii <= tagSplit[i]; ii++)
			vecPosSplit.push_back(vecPos[ii]);

		interp(vecPosSplit, vecPosInterp, pp, step, maxh);
	}
	return true;
}
*/
