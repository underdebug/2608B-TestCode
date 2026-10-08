
#pragma once
#include <math.h>

class Vector
{
public:
	Vector() : x(0), y(0), z(0) {}
	Vector(double t0) : x(t0), y(t0), z(t0) {}
	Vector(double x0, double y0) : x(x0), y(y0), z(0) {}
	Vector(double x0, double y0, double z0) : x(x0), y(y0), z(z0) {}
	Vector(const Vector& pt) : x(pt.x), y(pt.y), z(pt.z) {}
	void minimize(const Vector& pt0, const Vector& pt1);
	void maximize(const Vector& pt0, const Vector& pt1);
	void minimize(const Vector& pt);
	void maximize(const Vector& pt);

	void minimize(double xt, double yt, double zt);
	void maximize(double xt, double yt, double zt);

	void move(double dx, double dy, double dz);

	bool operator ==(const Vector& pt) const;
	bool operator !=(const Vector& pt) const;
	bool operator >(const Vector& pt) const;
	bool operator <(const Vector& pt) const;
	bool operator >=(const Vector& pt) const;
	bool operator <=(const Vector& pt) const;
	Vector operator +(const Vector& pt) const;
	Vector operator -(const Vector& pt) const;
	Vector& operator +=(const Vector& pt);
	Vector& operator -=(const Vector& pt);
	Vector operator *(double t) const { return Vector(x * t, y * t, z * t); }
	Vector operator /(double t) const { return Vector(x / t, y / t, z / t); }
	Vector& operator *=(double t);
	Vector& operator /=(double t);
	friend Vector operator * (double t, const Vector& v) { return Vector(v.x * t, v.y * t, v.z * t); }

	double getLength() const;
	double angle(const Vector& v) const;
	double dot(const Vector& pt) const;
	Vector cross(const Vector& pt) const;
	double distanceSquare(const Vector& pt) const;	
	double distance(const Vector& pt) const { return sqrt(distanceSquare(pt)); }
	Vector normalize();

	void moveXY(double dx, double dy);
	double getLengthXY() const;
	double getAngleXY() const;
	double getAngleXY(const Vector& v) const;
	void rotateXY(double angle);
	double dotXY(const Vector& v) const;
	bool isSquareXY(const Vector& v, double alpha) const;
	bool isParallelXY(const Vector& v, double alpha) const;

	double distanceSquareXY(double xx, double yy) const;	
	double distanceXY(double xx, double yy) const { return sqrt(distanceSquareXY(xx, yy)); }
	double distanceSquareXY(const Vector& pt) const { return distanceSquareXY(pt.x, pt.y); };	
	double distanceXY(const Vector& pt) const { return sqrt(distanceSquareXY(pt)); }

	double x, y, z;
};
