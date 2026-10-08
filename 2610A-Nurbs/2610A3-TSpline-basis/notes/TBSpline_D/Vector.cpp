
#include "stdafx.h"
#include "Vector.h"
#include <math.h>
#include "GlobalMicroDef.h"

void Vector::minimize(const Vector& pt0, const Vector& pt1)
{
	x = min(pt0.x, pt1.x);
	y = min(pt0.y, pt1.y);
	z = min(pt0.z, pt1.z);
}

void Vector::maximize(const Vector& pt0, const Vector& pt1)
{
	x = max(pt0.x, pt1.x);
	y = max(pt0.y, pt1.y);
	z = max(pt0.z, pt1.z);
}

void Vector::minimize(const Vector& pt)
{
	x = min(x, pt.x);
	y = min(y, pt.y);
	z = min(z, pt.z);
}

void Vector::maximize(const Vector& pt)
{
	x = max(x, pt.x);
	y = max(y, pt.y);
	z = max(z, pt.z);
}

void Vector::minimize(double xt, double yt, double zt)
{
	x = min(x, xt);
	y = min(y, yt);
	z = min(z, zt);
}


void Vector::maximize(double xt, double yt, double zt)
{
	x = max(x, xt);
	y = max(y, yt);
	z = max(z, zt);
}


void Vector::move(double dx, double dy, double dz)
{
	x += dx;
	y += dy;
	z += dz;
}

bool Vector::operator ==(const Vector& pt) const
{	return (x == pt.x) && (y == pt.y) && (z == pt.z);	}

bool Vector::operator !=(const Vector& pt) const
{	return (x != pt.x) || (y != pt.y) || (z != pt.z);	}

bool Vector::operator >(const Vector& pt) const
{	return (x > pt.x) && (y > pt.y) && (z > pt.z);	}

bool Vector::operator <(const Vector& pt) const
{	return (x < pt.x) && (y < pt.y) && (z < pt.z);	}

bool Vector::operator >=(const Vector& pt) const
{	return (x >= pt.x) && (y >= pt.y) && (z >= pt.z);	}

bool Vector::operator <=(const Vector& pt) const
{	return (x <= pt.x) && (y <= pt.y) && (z <= pt.z);	}

Vector Vector::operator +(const Vector& pt) const
{	return Vector(x + pt.x, y + pt.y,	z + pt.z);	}

Vector Vector::operator -(const Vector& pt) const
{	return Vector(x - pt.x, y - pt.y,	z - pt.z);	}

Vector& Vector::operator +=(const Vector& pt)
{
	x += pt.x;
	y += pt.y;
	z += pt.z;
	return *this;
}

Vector& Vector::operator -=(const Vector& pt)
{
	x -= pt.x;
	y -= pt.y;
	z -= pt.z;
	return *this;
}

Vector& Vector::operator *=(double t)
{
	x *= t;
	y *= t;
	z *= t;
	return *this;
}

Vector& Vector::operator /=(double t)
{
	x /= t;
	y /= t;
	z /= t;
	return *this;
}


double Vector::getLength() const
{
	return sqrt(x*x + y*y + z*z);
}


double Vector::angle(const Vector& v) const
{
	return acos(dot(v) / (getLength() * v.getLength()));
}


double Vector::dot(const Vector& v) const
{
	return x * v.x + y * v.y + z * v.z;
}


Vector Vector::cross(const Vector& v) const
{
	Vector c;
	c.x = y * v.z - z * v.y;
	c.y = z * v.x - x * v.z;
	c.z = x * v.y - y * v.x;
	return c;
}


double Vector::distanceSquare(const Vector& pt) const
{
	return (pt.x - x)*(pt.x - x) + (pt.y - y)*(pt.y - y) + (pt.z - z)*(pt.z - z);
}

Vector Vector::normalize()
{
	double fLength = sqrtf(x*x + y*y + z*z);
	if(fLength > FloatTypeZeroValue){
		x /= fLength;
		y /= fLength;
		z /= fLength;
	}else{
		x = y = z = 0.0f;
	}	
	return *this;
}

void Vector::moveXY(double dx, double dy)
{
	x += dx;
	y += dy;
}

double Vector::getLengthXY() const
{
	return sqrt(x*x + y*y);
}

double Vector::getAngleXY() const
{
	return atan2(y, x);
}

double Vector::getAngleXY(const Vector& v) const
{
	double alpha = v.getAngleXY() - getAngleXY();
	if(alpha <= -PI)
		alpha += PI*2.0f;
	else if(alpha > PI)
		alpha -= PI*2.0f;
	return alpha;
}

void Vector::rotateXY(double angle)
{
	double xx = cos(angle)*x + sin(angle)*y;	
	double yy = -sin(angle)*x + cos(angle)*y;
	x = xx; y = yy;
}

double Vector::dotXY(const Vector& v) const
{
	return x * v.x + y * v.y;
}

bool Vector::isSquareXY(const Vector& v, double alpha) const
{
	double angle = fabs(getAngleXY(v));
	if(fabs(angle - PI/2) <= alpha)
		return true;
	return false;
}

bool Vector::isParallelXY(const Vector& v, double alpha) const
{
	double angle = fabs(getAngleXY(v));
	if(angle <= alpha)
		return true;
	return false;
}

double Vector::distanceSquareXY(double xx, double yy) const
{
	return (xx - x)*(xx - x) + (yy - y)*(yy - y);
}


