/*
#ifndef TBSPLINE_LOOP_H
#define TBSPLINE_LOOP_H

#include "BaseDef.h"
#include "STLinf.h"
#include <windef.h>
#include "phoenixtempl.h"

bool tbslInterp(Position*& pt, int& sz, int& szall, double pp, double step, double maxh, void*& buf, int& szbuf);

class CTBsplineL
{
public:
	CTBsplineL();
	~CTBsplineL();
	
public:
	bool interp(Array<Position, Position>& vecPos, Array<Position, Position>& vecPosInterp, double pp, double step, double maxh);
	bool interp(Array<Position, Position>& vecPos, Array<Position*, Position*>& vecPosInterp, double pp, double step, double maxh);
	bool squreInterp(Array<Position, Position>& vecPos, Array<Position, Position>& vecPosInterp, double pp, double step, double maxh, double theta);
	bool squreInterp(Array<Position, Position>& vecPos, Array<Position*, Position*>& vecPosInterp, double pp, double step, double maxh, double theta);
	
private:
	Position* pt;
	int   szall;
	void* buf;
	int	  szbuf;
};

#endif //TBSPLINE_LOOP_H
*/
