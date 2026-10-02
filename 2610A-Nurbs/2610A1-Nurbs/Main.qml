import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick3D
import Nurbs 1.0

ApplicationWindow {
    id: window
    width: 1100
    height: 800
    visible: true
    title: "10 × 10 NURBS — Qt / QML / Vulkan"
    color: "#101827"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        View3D {
            id: view
            Layout.fillWidth: true
            Layout.fillHeight: true
            camera: camera
            environment: SceneEnvironment {
                backgroundMode: SceneEnvironment.Color
                clearColor: "#101827"
            }

            PerspectiveCamera {
                id: camera
                position: Qt.vector3d(0, 0, distance.value)
                clipNear: 1
                clipFar: 2000
            }

            Node {
                eulerRotation: Qt.vector3d(tilt.value, spin.value, 0)

                Model {
                    visible: gridVisible.checked
                    geometry: SurfaceGeometry { id: surface }
                    materials: DefaultMaterial {
                        diffuseColor: "#39bbef"
                        lighting: DefaultMaterial.NoLighting
                        cullMode: Material.NoCulling
                    }
                }

                Model {
                    visible: pointsVisible.checked
                    geometry: SurfaceGeometry { markers: true }
                    materials: DefaultMaterial {
                        diffuseColor: "#ff654f"
                        lighting: DefaultMaterial.NoLighting
                        cullMode: Material.NoCulling
                    }
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            color: "#1c293c"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14

                Label { text: "NURBS surface"; color: "white"; font.pixelSize: 22 }
                Label { text: "100 input points · cubic\nWeights = 1"; color: "#b8c9db" }
                Label { text: "Rotation"; color: "white" }
                Slider {
                    id: spin
                    Layout.fillWidth: true
                    from: -180
                    to: 180
                    value: 25
                }
                Label { text: "Tilt"; color: "white" }
                Slider {
                    id: tilt
                    Layout.fillWidth: true
                    from: -90
                    to: 90
                    value: 55
                }
                Label { text: "Camera distance"; color: "white" }
                Slider {
                    id: distance
                    Layout.fillWidth: true
                    from: 220
                    to: 900
                    value: 450
                }
                CheckBox { id: gridVisible; text: "Surface grid"; checked: true }
                CheckBox { id: pointsVisible; text: "Input points"; checked: true }
                Button {
                    text: "Reset view"
                    onClicked: {
                        spin.value = 25
                        tilt.value = 55
                        distance.value = 450
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: "Max interpolation error:\n" + surface.interpolationError.toExponential(3)
                    color: "#b8c9db"
                    wrapMode: Text.Wrap
                }
                Item { Layout.fillHeight: true }
            }
        }
    }
}
