#include "SurfaceGeometry.hpp"
#include "surface.hpp"
#include <QVector3D>

SurfaceGeometry::SurfaceGeometry(QQuick3DObject *parent) : QQuick3DGeometry(parent)
{
    rebuild();
}

bool SurfaceGeometry::markers() const
{
    return m_markers;
}

void SurfaceGeometry::setMarkers(bool value)
{
    if (m_markers == value)
        return;

    m_markers = value;
    rebuild();
    emit markersChanged();
}

double SurfaceGeometry::interpolationError() const
{
    return m_error;
}

void SurfaceGeometry::rebuild()
{
    const auto data = nurbs::data();
    const auto control = nurbs::interpolate(data);
    const auto vertices = nurbs::mesh(data, control);
    m_error = nurbs::error(data, control);

    QByteArray bytes;
    for (const auto &vertex : vertices)
    {
        const bool isMarker = vertex.r > 0.5f;
        if (isMarker != m_markers)
            continue;

        // Qt world uses Y as height; original input uses Z as height.
        const float position[] = {vertex.x * 100, vertex.z * 100, vertex.y * 100};
        bytes.append(reinterpret_cast<const char *>(position), sizeof(position));
    }

    clear();
    setStride(3 * sizeof(float));
    setPrimitiveType(QQuick3DGeometry::PrimitiveType::Lines);
    addAttribute(QQuick3DGeometry::Attribute::PositionSemantic, 0,
                 QQuick3DGeometry::Attribute::F32Type);
    setVertexData(bytes);
    setBounds(QVector3D(-103, -60, -103), QVector3D(103, 60, 103));
    update();
}
