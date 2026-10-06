#pragma once
#include <QQuick3DGeometry>

class SurfaceGeometry : public QQuick3DGeometry
{
    Q_OBJECT
    Q_PROPERTY(bool markers READ markers WRITE setMarkers NOTIFY markersChanged)
    Q_PROPERTY(bool controlPoints READ controlPoints WRITE setControlPoints NOTIFY controlPointsChanged)
    Q_PROPERTY(double interpolationError READ interpolationError CONSTANT)

  public:
    explicit SurfaceGeometry(QQuick3DObject *parent = nullptr);
    bool markers() const;
    void setMarkers(bool value);
    bool controlPoints() const;
    void setControlPoints(bool value);
    double interpolationError() const;

  signals:
    void markersChanged();
    void controlPointsChanged();

  private:
    void rebuild();
    bool m_markers = false;
    bool m_controlPoints = false;
    double m_error = 0;
};
