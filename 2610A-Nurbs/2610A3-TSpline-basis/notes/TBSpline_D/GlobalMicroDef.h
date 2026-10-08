#pragma once

#define FloatTypeZeroValue			1e-10			// 浮点0值定义（小于该值，则认为等于0）
#define MAX_CHAR_ARRAY_LENGTH		256				// 字符串最大长度

#ifndef MAKEWORD
#define MAKEWORD(a, b)      ((WORD)(((BYTE)(a)) | ((WORD)((BYTE)(b))) << 8))
#endif
#ifndef MAKELONG
#define MAKELONG(a, b)      ((LONG)(((WORD)(a)) | ((DWORD)((WORD)(b))) << 16))
#endif
#ifndef UPDATELOWORD
#define UPDATELOWORD(a, l)  a = ((LONG)(((WORD)(l)) | ((a) & 0xFFFF0000)))
#endif
#ifndef UPDATEHIWORD
#define UPDATEHIWORD(a, h)  a = ((((DWORD)((WORD)(h))) << 16) | ((a) & 0xFFFF))
#endif
#ifndef LOWORD
#define LOWORD(l)           ((WORD)(l))
#endif
#ifndef HIWORD
#define HIWORD(l)           ((WORD)(((DWORD)(l) >> 16) & 0xFFFF))
#endif
#ifndef LOBYTE
#define LOBYTE(w)           ((BYTE)(w))
#endif
#ifndef HIBYTE
#define HIBYTE(w)           ((BYTE)(((WORD)(w) >> 8) & 0xFF))
#endif

#ifndef MAX_INTERGER
#define MAX_INTERGER 0xEFFFFFFF
#endif
#ifndef MAX_UINTERGER
#define MAX_UINTERGER 0xFFFFFFFF
#endif

// 地球赤道长度(m)
#ifndef EQUATOR_LENGTH
#define EQUATOR_LENGTH 40076000
#endif

#ifndef PI
#define PI 3.14159265358979323846f
#endif

#ifndef HALFPI
#define HALFPI 1.57079632679489661923f
#endif

#ifndef ZERO_TOLERANCE
#define ZERO_TOLERANCE 1e-06f
#endif

#ifndef min
#define min(a,b) ((a)<(b))?(a):(b)
#endif
#ifndef max
#define max(a,b) ((a)>(b))?(a):(b)
#endif
#ifndef ABS
#define ABS(a) (((a)<0)?(-(a)):(a))
#endif
