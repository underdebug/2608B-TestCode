
#include "stdafx.h"
/*
#include "TBsplineL.h"
#include "BaseDef.h"
#include "matBorderedBand.h"
#include "TBspline.h"
#include "Filter.h"
#include <math.h>

static double fi(int k, double x, double pi, double di);
static double fi(int k, double x, int i, double* p, double* d);
static double beta_k3_j_2(int l, int i, double* p, double* d);
static double beta_k3_j_1(int l, int i, double* p, double* d);
static double beta_k3_j0(int l, int i, double* p, double* d);
static double beta_k3(int l, int i, int j, double* p, double* d);
static double beta_k4(int l, int i, int j, double* p, double* d);
static double sigma_k3(int j, int i, double* p, double* d);
static double sigma(int k, int j, int i, double* p, double* d);
static double sigma(int k, int i, double* p, double* d);

double fi(int k, double x, double pi, double di)
{
	if(pi != 0.0){
		switch(k){
		case 3:
			return (cosh(pi*x)-1) / (pi * sinh(pi*di));
			break;
		case 4:
			return (sinh(pi*x)-pi*x) / (pi * pi * sinh(pi*di));
			break;		
		}
	}
	return x*x / (2*di);
}

double fi(int k, double x, int i, double* p, double* d)
{
	return fi(k, x, p[i], d[i]);
}

double beta_k3_j_2(int l, int i, double* p, double* d)
{
	switch(l){
	case -2:
		return 0.0;
		break;
	case -1:
		return 1.0 / sigma(2, i-1, p, d);
		break;
	case 0:
		return 0.0;
		break;
	}
	return 0.0;
}

double beta_k3_j_1(int l, int i, double* p, double* d)
{
	switch(l){
	case -2:
		return -1.0 / sigma(2, i, p, d);
		break;
	case -1:
		return -1.0 / sigma(2, i-1, p, d);
		break;
	case 0:
		return 1.0;
		break;
	}
	return 0.0;
}

double beta_k3_j0(int l, int i, double* p, double* d)
{
	switch(l){
	case -2:
		return 1.0 / sigma(2, i, p, d);
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

double beta_k3(int l, int i, int j, double* p, double* d)
{
	int seg = j-i;
	switch(seg){
	case -2:
		return beta_k3_j_2(l, i, p, d);
		break;
	case -1:
		return beta_k3_j_1(l, i, p, d);
		break;
	case 0:
		return beta_k3_j0(l, i, p, d);
		break;
	}
	return 0.0;
}

double beta_k4(int l, int i, int j, double* p, double* d)
{
	switch(l){
	case -2:
		return beta_k3(-2, i, j, p, d) / sigma(3, j, p, d) - beta_k3(-2, i, j+1, p, d) / sigma(3, j+1, p, d);
		break;
	case -1:
		return beta_k3(-1, i, j+1, p, d) / sigma(3, j+1, p, d) - beta_k3(-1, i, j, p, d)/ sigma(3, j, p, d);
		break;
	case 0:
		return (sigma(3, j, i, p, d) + beta_k3(-1, i, j, p, d) * fi(4, d[i], i, p, d)) / sigma(3, j, p, d) - (sigma(3, j+1, i, p, d) + beta_k3(-1, i, j+1, p, d) * fi(4, d[i], i, p, d)) / sigma(3, j+1, p, d);
		break;
	case 1:
		return d[i]*beta_k3(0, i, j, p, d) / sigma(3, j, p, d) - d[i]*beta_k3(0, i, j+1, p, d) / sigma(3, j+1, p, d);
		break;	
	}
	return 0.0;
}

double sigma_k3(int j, int i, double* p, double* d)
{
	double dRet = 0.0;
	for(int l=j; l<i; l++)
		dRet += (beta_k3(-2, l, j, p, d) + beta_k3(-1, l, j, p, d)) * fi(4, d[l], l, p, d) + d[l]*beta_k3(0, l, j, p, d);
	return dRet;
}

double sigma(int k, int j, int i, double* p, double* d)
{	
	switch(k){
	case 3:
		return sigma_k3(j, i, p, d);
		break;
	}
	return 0.0;
}

double sigma(int k, int i, double* p, double* d)
{
	if(k >= 3)
		return sigma(k, i, i+k, p, d);
	else if(k >= 2)
		return fi(3, d[i], i, p, d) + fi(3, d[i+1], i+1, p, d);
	return 0.0;	
}

static double distance2(Position p1, Position p2)
{
	return sqrt((p1.x-p2.x)*(p1.x-p2.x) + (p1.y-p2.y)*(p1.y-p2.y));
}

static void calcTD(Position* pt, int sz, int n, double* t, double* d, double L)
{
	int i;
	// 0 1 2 => 3 4 ... n-1 n => n+1 n+2 n+3
	t[0] = 0.0;
	for(i=1; i<n+4; i++)
		t[i] = t[i-1] + distance2(pt[(i-4+sz)%sz], pt[(i-3+sz)%sz]);

	for(i=0; i<n+4; i++)
		t[i] /= L;

	for(i=0; i<n+3; i++)
		d[i] = t[i+1] - t[i];
}

static void calcP(double pp, int n, double* p)
{
	int i;
	for(i=0; i<n+4; i++)
		p[i] = pp;
}

static void calcCoeff(double* t, double* p, double* d, int n, double* CC)
{
	double *cc = CC, c1;
	for(int i=3; i<n; i++){
		for(int j=i-3; j<=i; j++){
			c1    = beta_k4( 1, i, j, p, d);
			cc[0] = beta_k4(-2, i, j, p, d);
			cc[1] = beta_k4(-1, i, j, p, d);
			cc[2] = beta_k4( 0, i, j, p, d) - c1 * t[i] / d[i];
			cc[3] = c1 / d[i];
			cc += 4;
		}
	}
}

static void getLinearPosition(Position* pt, int sz, int i, double t, double& x, double& y)
{
	x = pt[i].x*(1-t) + pt[(i+1) % sz].x*t;
	y = pt[i].y*(1-t) + pt[(i+1) % sz].y*t;
}

static void calcAXY(Position* pt, int sz, int n, double ts, double* t, double* p, double* d, double* CC, double* B, double* AX, double* AY)
{
	double s, b[4], x, y, *cc=CC, fix[2], w;
	int idx[4];

	for(int i=0; i<sz; i++){
		for(double t0=0.0; t0<1.0; t0+=0.1){
			getLinearPosition(pt, sz, i, t0, x, y);

			w = 1.0;
			if (t0 == 0.0) w /= ts;

			s = t[i+3] + t0*d[i+3];
			fix[0] = fi(4, s-t[i+3], i+3, p, d);
			fix[1] = fi(4, t[i+3+1]-s, i+3, p, d);

			b[0] = cc[0] * fix[0] + cc[1] * fix[1] + cc[2] + cc[3] * s;
			b[1] = cc[4] * fix[0] + cc[5] * fix[1] + cc[6] + cc[7] * s;
			b[2] = cc[8] * fix[0] + cc[9] * fix[1] + cc[10]+ cc[11]* s;
			b[3] = cc[12]* fix[0] + cc[13]* fix[1] + cc[14]+ cc[15]* s;	

			idx[0] = (i-3 + sz) % sz;
			idx[1] = (i-2 + sz) % sz;
			idx[2] = (i-1 + sz) % sz;
			idx[3] = (i-0 + sz) % sz;
			
			for(int ii=0; ii<4; ii++){
				for(int jj=0; jj<4; jj++)
					matBorderedBandAddValue(B, n, 3, b[ii] * b[jj] * w, idx[ii], idx[jj]);
				AX[idx[ii]] += b[ii] * x * w;
				AY[idx[ii]] += b[ii] * y * w;
			}
		}
		cc += 16;	
	}

	matBorderedBand(B, AX, AY, n, 3);
}

static double distance2(double a, double b, double c, const Position& p)
{
	double L = a * p.x + b * p.y + c;
	return L*L;
}
static double distance2(const Position& p1, const Position& p2)
{
	return (p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y);
}
static double findMaxH(Position* pt, int ns, int ne, int& nn)
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
static void filter(Position* pt, unsigned char* tag, int ns, int ne, double h, int& num)
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

static void* newbuffer(void* buffer, int szbuf)
{
	if(!buffer)
		return (void*) malloc (szbuf);
	else
		return (void*) realloc (buffer, szbuf);
}

//Position*&	pt			导入点 && 导出点 
//int&			sz			导入点数量 && 导出点数量
//int&			szall		存储点的实际存储空间大小
//double		pp			张力系数
//double		step		插入步长
//double		maxh		最大高度限差
//void*&		buf			临时缓冲区
//int&			szbuf		临时缓冲区大小
bool tbslInterp(Position*& pt, int& sz, int& szall, double pp, double step, double maxh, void*& buf, int& szbuf)
{
	if(sz<3) return false;
	int n = sz+3; //基函数个数(n),矩阵行列数(sz)

	double L = 0.0;
	for(int i=0; i<sz; i++)
		L += distance2(pt[i], pt[(i+1+sz)%sz]);
	step /= L;
	int nseg = int(1.0 / step) + sz;

	int szbuf1 = (n+4 + n+4 + n+4 + n*7 + n + n + n*16) * sizeof(double);
	int szbuf2 = nseg + nseg * sizeof(Position);

	if(szbuf < szbuf1+szbuf2){
		szbuf = 2 * (szbuf1+szbuf2);
		buf   = newbuffer (buf, szbuf);
	}
	
	memset(buf, 0, szbuf1+szbuf2);
	double* buf1 = (double*) buf;
	unsigned char* buf2 = (unsigned char*) buf + szbuf1;
	
	double* t	= buf1;		//n+4
	double* d	= t	 + n+4;	//n+4
	double* p	= d	 + n+4;	//n+4
	double* B	= p  + n+4;	//n*7
	double* AX	= B  + n*7;	//n
	double* AY	= AX + n;	//n
	double* CC  = AY + n;	//n*16

	unsigned char* tag = buf2;
	Position* _pt = (Position*) (tag + nseg);
	
	calcTD(pt, sz, n, t, d, L);
	calcP(pp, n, p);
	calcCoeff(t, p, d, n, CC);
	calcAXY(pt, sz, sz, 0.1, t, p, d, CC, B, AX, AY);

	double s, b[4];
	Position pos;

	int idx=0;
	double *cc = CC, fix[2];;
	for(i=0; i<sz; i++){
		int	nn = int(d[i+3]/step);
		if(nn == 0){
			cc += 16;
			continue;
		}
		double ss = d[i+3] / nn;
		
		for(int j=0; j<nn; j++){
			s = t[i+3] + j*ss;

			fix[0] = fi(4, s-t[i+3], i+3, p, d);
			fix[1] = fi(4, t[i+3+1]-s, i+3, p, d);
			
			b[0] = cc[0] * fix[0] + cc[1] * fix[1] + cc[2] + cc[3] * s;
			b[1] = cc[4] * fix[0] + cc[5] * fix[1] + cc[6] + cc[7] * s;
			b[2] = cc[8] * fix[0] + cc[9] * fix[1] + cc[10]+ cc[11]* s;
			b[3] = cc[12]* fix[0] + cc[13]* fix[1] + cc[14]+ cc[15]* s;	
			
			_pt[idx].x = AX[(i-3+sz)%sz]*b[0] + AX[(i-2+sz)%sz]*b[1] + AX[(i-1+sz)%sz]*b[2] + AX[(i-0+sz)%sz]*b[3];
			_pt[idx].y = AY[(i-3+sz)%sz]*b[0] + AY[(i-2+sz)%sz]*b[1] + AY[(i-1+sz)%sz]*b[2] + AY[(i-0+sz)%sz]*b[3];	
			_pt[idx].z = ((t[i+4] - s) / d[i+3]) * pt[i].z + ((s - t[i+3]) / d[i+3]) * pt[(i+1) % sz].z;

			idx++;
		}
		cc += 16;
	}
	nseg = idx;
	
	int num=nseg;
	filter(_pt, tag, 0, nseg-1, maxh, num);

	if(szall < num){
		szall = 2 * num;
		pt = (Position*) newbuffer (pt, szall* sizeof(Position));
	}
	sz = num;

	Position* ppt = pt;
	for(i=0; i<nseg; i++){
		if(tag[i] != 1)
			memcpy(ppt++, &_pt[i], sizeof(Position));
	}
	return true;
}

CTBsplineL::CTBsplineL()
{
	pt = NULL;
	szall = 0;
	buf = NULL;
	szbuf = NULL;
}

CTBsplineL::~CTBsplineL()
{
	if(pt) free(pt); pt=NULL;
	if(buf) free(buf); buf=NULL;
}

bool CTBsplineL::interp(Array<Position, Position>& vecPos, Array<Position, Position>& vecPosInterp, double pp, double step, double maxh)
{
	if(vecPos.getSize() == 0) return false;
	CFilter::discardRepeatPosL(vecPos, 0.0001);
	CFilter::insertCornerPosL(vecPos, 30.0);
	CFilter::splitPolylineL(vecPos, 300.0);

	int sz = vecPos.getSize();
	if(!pt){
		szall = 2 * sz;
		pt = (Position*) malloc (szall * sizeof(Position));
	}else{
		if(szall < sz){
			szall = 2 * sz;
			pt = (Position*) realloc (pt, szall * sizeof(Position));
		}
	}

	Position* ppt = pt;
	ppt->x = vecPos[0].x;
	ppt->y = vecPos[0].y;
	ppt->z = vecPos[0].z;
	for(int i=1; i<vecPos.getSize(); i++){
		if((ppt->x - vecPos[i].x) * (ppt->x - vecPos[i].x) + (ppt->y - vecPos[i].y) * (ppt->y - vecPos[i].y) > 0.0001){
			ppt++;
			ppt->x = vecPos[i].x;
			ppt->y = vecPos[i].y;
			ppt->z = vecPos[i].z;
		}else{
			sz--;
		}
	}

	if((pt[0].x - pt[sz-1].x) * (pt[0].x - pt[sz-1].x) + (pt[0].y - pt[sz-1].y) * (pt[0].y - pt[sz-1].y) < 0.0001)
		sz--;

	tbslInterp(pt, sz, szall, pp, step, maxh, buf, szbuf);
	for(i=0; i<sz; i++)
		vecPosInterp.add(pt[i]);
	return true;
}

static bool isSqure(Position* pt1, Position* pt, Position* pt2, double th)
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
static bool isParallel(Position* p1, Position* p2, Position* p3, Position* p4, double th)
{
#define PI 3.14159265358979
	double alpha1 = atan2(p2->y - p1->y, p2->x - p1->x);
	double alpha2 = atan2(p3->y - p4->y, p3->x - p4->x);
	double alpha  = fabs(alpha1 - alpha2);				
	if(alpha > PI) alpha = 2.0*PI - alpha;				
	if(alpha < th*PI/180.0) return true;				
	return false;
}
static void append(Array<Position, Position>& vecPos, Array<Position, Position>& vecAdd)
{
	int ns = vecPos.getSize() == 0 ? 0 : 1;
	for(int i=ns; i<vecAdd.getSize(); i++)
		vecPos.add(vecAdd[i]);		
}

bool CTBsplineL::squreInterp(Array<Position, Position>& vecPos, Array<Position, Position>& vecPosInterp, double pp, double step, double maxh, double theta)
{
	if(vecPos.getSize() == 0) return false;
	CFilter::discardRepeatPosL(vecPos, 0.0001);
	
	SortArray<int, int> tagSplit;
	if(vecPos.getSize() > 2){
		for(int i=0; i<vecPos.getSize(); i++){
			if(isSqure(&vecPos[(i-1 + vecPos.getSize()) % vecPos.getSize()], &vecPos[i], &vecPos[(i+1) % vecPos.getSize()], 10.0))
				tagSplit.add(i);			
		}
	}
	if(vecPos.getSize() > 3){
		for(int i=0; i<vecPos.getSize(); i++){
			if(isParallel(&vecPos[(i-1 + vecPos.getSize()) % vecPos.getSize()], &vecPos[i], 
						  &vecPos[(i+1) % vecPos.getSize()], &vecPos[(i+2) % vecPos.getSize()], 10.0)){
				tagSplit.add(i);
				tagSplit.add(i+1);
			}
		}
	}
	tagSplit.sortLess();

	if(tagSplit.getSize() == 0){
		interp(vecPos, vecPosInterp, pp, step, maxh);
	}else{
		CTBspline tbs;
		tagSplit.add(tagSplit[0] + vecPos.getSize());		
		Array<Position, Position> vecPosSplit;
		for(int i=1; i<tagSplit.getSize(); i++){
			vecPosSplit.removeAll();
			for(int ii=tagSplit[i-1]; ii <= tagSplit[i]; ii++)
				vecPosSplit.add(vecPos[ii % vecPos.getSize()]);

			tbs.interp(vecPosSplit, vecPosInterp, pp, step, maxh);
		}
	}
	return true;
}

#define EXPORT_TO_DATAMANAGER
#ifdef  EXPORT_TO_DATAMANAGER

#include "DataManager.h"
#include "PointTable.h"

bool CTBsplineL::interp(Array<Position, Position>& vecPos, Array<Position*, Position*>& vecPosInterp, double pp, double step, double maxh)
{
	Array<Position, Position> vecPosTmp;
	interp(vecPos, vecPosTmp, pp, step, maxh);
	CPointTable& pointTable = CDataManager::Instance().GetPointTable();
	for(int i=0; i<vecPosTmp.getSize(); i++){
		Position* pPos = pointTable.add(vecPosTmp[i]);
		vecPosInterp.add(pPos);
	}
	return true;
}

bool CTBsplineL::squreInterp(Array<Position, Position>& vecPos, Array<Position*, Position*>& vecPosInterp, double pp, double step, double maxh, double theta)
{
	if(vecPos.getSize() == 0) return false;
	Array<Position, Position> vecPosTmp;
	squreInterp(vecPos, vecPosTmp, pp, step, maxh, theta);
	CPointTable& pointTable = CDataManager::Instance().GetPointTable();
	for(int i=0; i<vecPosTmp.getSize(); i++){
		Position* pPos = pointTable.add(vecPosTmp[i]);
		vecPosInterp.add(pPos);
	}
	return true;
}

#endif //EXPORT_TO_DATAMANAGER
*/