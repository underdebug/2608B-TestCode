#include "SurfaceGeometry.hpp"
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickWindow>
#include <QSGRendererInterface>
#include <QtQml>

int main(int argc, char *argv[])
{
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt

    // Default to Vulkan. An explicit environment override can select OpenGL.
    if (qEnvironmentVariableIsEmpty("QSG_RHI_BACKEND"))
        QQuickWindow::setGraphicsApi(QSGRendererInterface::Vulkan);

    QGuiApplication app(argc, argv);
    qmlRegisterType<SurfaceGeometry>("Nurbs", 1, 0, "SurfaceGeometry");

    QQmlApplicationEngine engine;
    engine.load(QUrl(QStringLiteral("qrc:/Main.qml")));
    if (engine.rootObjects().isEmpty())
        return 1;

    return app.exec();
}
