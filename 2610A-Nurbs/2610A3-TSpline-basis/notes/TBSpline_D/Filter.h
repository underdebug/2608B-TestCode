
#ifndef FILTER_H
#define FILTER_H

#include <vector>
#include "Vector.h"

class CFilter  
{
public:
	CFilter(){};
	~CFilter(){};
public:
	static void discardRepeatPos(std::vector<Vector>& vecPos, double mindis);
	static void insertCornerPos(std::vector<Vector>& vecPos, double mindis);
	static void splitPolyline(std::vector<Vector>& vecPos, double mindis);
	static void discardRepeatPosL(std::vector<Vector>& vecPos, double mindis);
	static void insertCornerPosL(std::vector<Vector>& vecPos, double mindis);
	static void splitPolylineL(std::vector<Vector>& vecPos, double mindis);
};

#endif //FILTER_H
