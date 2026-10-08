// TBSpline.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include "TBspline.h"
#include "Vector.h"
#include <vector>

int _tmain(int argc, _TCHAR* argv[])
{
/*
	// µÚÒ»Åú²âÊÔ
	std::vector<Vector> vecPos, vecPosInterp;
	vecPos.push_back(Vector(0, 0, 0));
	vecPos.push_back(Vector(0, 200, 0));
	vecPos.push_back(Vector(50, 0, 0));
	vecPos.push_back(Vector(50,  200, 0));
	vecPos.push_back(Vector(500,  0, 0));
	vecPos.push_back(Vector(1000,  0, 0));

	vecPos.push_back(Vector(500,  500, 0));
	vecPos.push_back(Vector(-500,  500, 0));
	vecPos.push_back(Vector(-1000,  0, 0));

	CTBspline tbs;
	//tbs.interp(vecPos, vecPosInterp, 0.01, 5.0, 1.0);
	tbs.interp(vecPos, vecPosInterp, 0.05, 5.0, 1.0);
*/

	int pnSize[105];
	FILE* fp = fopen("D:\\temp\\index.dat", "rb");
	fread(pnSize, 105, sizeof(int), fp);
	fclose(fp);

	double A[2048];
	for(int i = 0; i < 105; i++){
		char strFile[1024] = {0};
		FILE* fp ;

		sprintf(strFile, "D:\\temp\\Ori\\%03d.dat", i+1);
		fp = fopen(strFile, "rb");
		fread(A, pnSize[i] * 2, sizeof(double), fp);
		fclose(fp);

		std::vector<Vector> vecPos, vecPosInterp;
		for(int ii = 0; ii < pnSize[i]; ii++){
			double x = A[2 * ii];
			double y = A[2 * ii + 1];
			vecPos.push_back(Vector(x, y, 0.0));
		}

		//Vector* pt1 = &vecPos[0];
		//Vector* pt2 = &vecPos[vecPos.size() - 1];
		//if(abs(pt1->x - pt2->x) < 1E-6 && abs(pt1->y - pt2->y) < 1E-6){
		//	vecPos.pop_back();
		//}

		CTBspline tbs;
		//tbs.interp(vecPos, vecPosInterp, 0.03, 5.0, 1.0);
		tbs.interp(vecPos, vecPosInterp, 0.03, 5.0, 1.0, i);

		sprintf(strFile, "D:\\temp\\New\\%03d.dat", i+1);
		fp = fopen(strFile, "wb");
		fwrite(&vecPosInterp[0], vecPosInterp.size(), sizeof(Vector), fp);
		fclose(fp);
	}


	return 0;
}

