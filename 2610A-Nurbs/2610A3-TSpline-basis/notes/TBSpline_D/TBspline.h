
#ifndef TBSPLINE_H
#define TBSPLINE_H

#include <vector>
#include "Vector.h"

bool tbsInterp(Vector*& pt, int& sz, int& szall, double pp, double step, double maxh, void*& buf, int& szbuf);

class CTBspline
{
public:
	CTBspline();
	~CTBspline();

public:
	bool interp(std::vector<Vector>& vecPos, std::vector<Vector>& vecPosInterp, double pp, double step, double maxh, int ii);
	bool interp(std::vector<Vector>& vecPos, std::vector<Vector*>& vecPosInterp, double pp, double step, double maxh);
	bool squreInterp(std::vector<Vector>& vecPos, std::vector<Vector>& vecPosInterp, double pp, double step, double maxh, double theta);
	bool squreInterp(std::vector<Vector>& vecPos, std::vector<Vector*>& vecPosInterp, double pp, double step, double maxh, double theta);

private:
	Vector* pt;
	int   szall;
	void* buf;
	int	  szbuf;
};

#endif //TBSPLINE_H
