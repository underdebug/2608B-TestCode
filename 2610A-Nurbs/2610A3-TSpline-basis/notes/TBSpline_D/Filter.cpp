
#include "stdafx.h"
#include "Filter.h"
#include <math.h>
#include "GlobalMicroDef.h"

void CFilter::discardRepeatPos(std::vector<Vector>& vecPos, double mindis)
{
	if(vecPos.size() < 3) return;
	double mindis2 = mindis * mindis;
	for(int i=1; i<vecPos.size();){
		if((vecPos[i-1].x - vecPos[i].x) * (vecPos[i-1].x - vecPos[i].x) + (vecPos[i-1].y - vecPos[i].y) * (vecPos[i-1].y - vecPos[i].y) < mindis2){
			if(i != vecPos.size()-1){
				vecPos.erase(vecPos.begin() + i);
			}else{
				if(vecPos.size() > 2)
					vecPos.erase(vecPos.begin() + i-1);
				break;
			}
		}else{
			i++;
		}
	}
}

static double getAngle(Vector* p1, Vector* p, Vector* p2)
{
	if(!p1 || !p2) return 0.0;
	double alpha1 = atan2(p1->y - p->y, p1->x - p->x);	
	double alpha2 = atan2(p2->y - p->y, p2->x - p->x);
	double alpha  = fabs(alpha1 - alpha2);
	return (alpha > PI) ? (2.0*PI - alpha) : alpha;
}
static double estimateRadius(double alpha, double mindis)
{
	double radius = mindis * sin(alpha) / (1-sin(alpha));
	return sqrt(mindis * (mindis + 2.0 * radius));
}
void CFilter::insertCornerPos(std::vector<Vector>& vecPos, double mindis)
{
	if(vecPos.size()<2) return;
	Vector p;
	double radius1 = estimateRadius(0.0, mindis), radius2, angle, t1, t2;
	for(int i=1; i<vecPos.size(); i++){
		angle = getAngle(&vecPos[i-1], &vecPos[i], i+1 < vecPos.size() ? &vecPos[i+1] : NULL);
		radius2 = estimateRadius(angle/2.0, mindis);

		double di = sqrt((vecPos[i-1].x - vecPos[i].x) * (vecPos[i-1].x - vecPos[i].x) + (vecPos[i-1].y - vecPos[i].y) * (vecPos[i-1].y - vecPos[i].y));
		t1 = radius1 / di;
		t2 = radius2 / di;

		int n = 0;
		if(t1 < 0.6){
			p.x = (1-t1) * vecPos[i-1].x + t1 * vecPos[i].x;
			p.y = (1-t1) * vecPos[i-1].y + t1 * vecPos[i].y;
			p.z = (1-t1) * vecPos[i-1].z + t1 * vecPos[i].z;
			
			vecPos.insert(vecPos.begin() + i, p);
			n++; i++;
		}
		
		if(t2 < 0.6){
			t2 = 1.0 - t2;
			p.x = (1-t2) * vecPos[i-1-n].x + t2 * vecPos[i].x;
			p.y = (1-t2) * vecPos[i-1-n].y + t2 * vecPos[i].y;
			p.z = (1-t2) * vecPos[i-1-n].z + t2 * vecPos[i].z;
			
			if(t2 > t1 || n == 0)
				vecPos.insert(vecPos.begin() + i, p);
			else
				vecPos.insert(vecPos.begin() + i-1, p);
			i++;
		}
		radius1 = radius2;
	}
}

void CFilter::splitPolyline(std::vector<Vector>& vecPos, double mindis)
{
	if(vecPos.size() < 2) return;
	Vector p1,p2,p; double t;
	for(int i=1; i<vecPos.size(); i++){		
		double di2 = (vecPos[i-1].x - vecPos[i].x) * (vecPos[i-1].x - vecPos[i].x) + (vecPos[i-1].y - vecPos[i].y) * (vecPos[i-1].y - vecPos[i].y);
		if(di2 > mindis * mindis){
			int ni = int(sqrt(di2)/mindis) + 1;
			for(int ii=1; ii<ni; ii++){
				t = double(ii) / ni;
				p.x = (1-t) * vecPos[i-ii].x + t * vecPos[i].x;
				p.y = (1-t) * vecPos[i-ii].y + t * vecPos[i].y;
				p.z = (1-t) * vecPos[i-ii].z + t * vecPos[i].z;
				vecPos.insert(vecPos.begin() + i++, p);
			}
		}
	}
}

void CFilter::discardRepeatPosL(std::vector<Vector>& vecPos, double mindis)
{
	discardRepeatPos(vecPos, mindis);
	if(vecPos.size() < 3) return;

	double di2 = (vecPos[0].x - vecPos[vecPos.size()-1].x) * (vecPos[0].x - vecPos[vecPos.size()-1].x)
			   + (vecPos[0].y - vecPos[vecPos.size()-1].y) * (vecPos[0].y - vecPos[vecPos.size()-1].y);
	if(di2 < mindis * mindis)
		vecPos.erase(vecPos.begin() + vecPos.size()-1);
}

void CFilter::insertCornerPosL(std::vector<Vector>& vecPos, double mindis)
{
	if(vecPos.size()<2) return;
	Vector p;
	double angle = getAngle(&vecPos[vecPos.size()-2], &vecPos[vecPos.size()-1], &vecPos[0]);
	double radius1 = estimateRadius(angle/2.0, mindis), radius2, t1, t2;
	for(int i=0; i<vecPos.size(); i++){
		int iPre = (i-1 + vecPos.size()) % vecPos.size();
		angle = getAngle(&vecPos[iPre], &vecPos[i], &vecPos[(i+1) % vecPos.size()]);
		radius2 = estimateRadius(angle/2.0, mindis);
		
		double di = sqrt((vecPos[iPre].x - vecPos[i].x) * (vecPos[iPre].x - vecPos[i].x) + (vecPos[iPre].y - vecPos[i].y) * (vecPos[iPre].y - vecPos[i].y));
		t1 = radius1 / di;
		t2 = radius2 / di;
		
		int n = 0;
		if(t1 < 0.6){
			p.x = (1-t1) * vecPos[iPre].x + t1 * vecPos[i].x;
			p.y = (1-t1) * vecPos[iPre].y + t1 * vecPos[i].y;
			p.z = (1-t1) * vecPos[iPre].z + t1 * vecPos[i].z;
			
			vecPos.insert(vecPos.begin() + i, p);
			n++; i++;
		}
		
		if(t2 < 0.6){
			t2 = 1.0 - t2;
			iPre = (i-1-n + vecPos.size()) % vecPos.size(); 
			p.x = (1-t2) * vecPos[iPre].x + t2 * vecPos[i].x;
			p.y = (1-t2) * vecPos[iPre].y + t2 * vecPos[i].y;
			p.z = (1-t2) * vecPos[iPre].z + t2 * vecPos[i].z;
			
			if(t2 > t1 || n == 0)
				vecPos.insert(vecPos.begin() + i, p);
			else
				vecPos.insert(vecPos.begin() + (i-1+vecPos.size()) % vecPos.size(), p);
			i++;
		}
		radius1 = radius2;
	}
}

void CFilter::splitPolylineL(std::vector<Vector>& vecPos, double mindis)
{
	splitPolyline(vecPos, mindis);
	if(vecPos.size() < 2) return;

	double di2 = (vecPos[0].x - vecPos[vecPos.size()-1].x) * (vecPos[0].x - vecPos[vecPos.size()-1].x)
			   + (vecPos[0].y - vecPos[vecPos.size()-1].y) * (vecPos[0].y - vecPos[vecPos.size()-1].y);
	if(di2 > mindis * mindis){
		Vector p; double t;
		int ni = int(sqrt(di2)/mindis) + 1;
		for(int i=1; i<ni; i++){
			t = double(i) / ni;
			p.x = (1-t) * vecPos[vecPos.size()-i].x + t * vecPos[0].x;
			p.y = (1-t) * vecPos[vecPos.size()-i].y + t * vecPos[0].y;
			p.z = (1-t) * vecPos[vecPos.size()-i].z + t * vecPos[0].z;
			vecPos.push_back(p);
		}
	}
}