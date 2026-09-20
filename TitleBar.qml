import QtQuick
import qs.Commons

Item {
  id: root

  property color background: Color.menu.background
  property color foreground: Color.menu.text
  property color accent: Color.accent
  property real cornerRadius: 0
  property int ventsRightMargin: Style.space(8)
  property int headerBandHeight: height
  property int contentTopPadding: 0

  readonly property int ventCount: 6
  readonly property int ventSlot: Style.space(2)
  readonly property int ventGap: Style.space(3)
  readonly property int ventClusterWidth: ventCount * ventSlot + (ventCount - 1) * ventGap
  readonly property int ventHeight: Math.max(Style.space(10), Math.round(headerBandHeight * 0.55))

  readonly property color steelHi: Qt.lighter(background, 1.42)
  readonly property color steelMid: Qt.rgba(
    background.r * 0.8 + accent.r * 0.2,
    background.g * 0.8 + accent.g * 0.2,
    background.b * 0.8 + accent.b * 0.2,
    1)
  readonly property color steelLo: Qt.darker(background, 1.22)
  readonly property color steelRim: Qt.darker(background, 1.48)
  readonly property color steelHole: Qt.darker(background, 2.1)
  readonly property color steelSpec: Qt.rgba(
    Math.min(1, background.r * 0.58 + foreground.r * 0.42),
    Math.min(1, background.g * 0.58 + foreground.g * 0.42),
    Math.min(1, background.b * 0.58 + foreground.b * 0.42),
    1)

  Rectangle {
    id: plate
    anchors.fill: parent
    clip: true
    topLeftRadius: root.cornerRadius
    topRightRadius: root.cornerRadius
    bottomLeftRadius: 0
    bottomRightRadius: 0
    color: root.background

    gradient: Gradient {
      GradientStop { position: 0.00; color: root.steelRim }
      GradientStop { position: 0.08; color: root.steelHi }
      GradientStop { position: 0.28; color: root.steelSpec }
      GradientStop { position: 0.52; color: root.steelMid }
      GradientStop { position: 0.82; color: root.steelLo }
      GradientStop { position: 1.00; color: root.steelRim }
    }

    Rectangle {
      anchors.fill: parent
      gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop {
          position: 0.0
          color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.07)
        }
        GradientStop { position: 0.42; color: Qt.rgba(0, 0, 0, 0) }
        GradientStop {
          position: 1.0
          color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.14)
        }
      }
    }

    Rectangle {
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.top: parent.top
      height: 1
      color: Qt.rgba(root.steelHi.r, root.steelHi.g, root.steelHi.b, 0.72)
    }

    Rectangle {
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.bottom: parent.bottom
      height: 1
      color: root.steelRim
    }

    Row {
      spacing: root.ventGap
      anchors.right: parent.right
      anchors.rightMargin: root.ventsRightMargin
      y: root.contentTopPadding + Math.round((root.headerBandHeight - root.ventHeight) / 2)
      height: root.ventHeight

      Repeater {
        model: root.ventCount
        Item {
          width: root.ventSlot
          height: root.ventHeight

          Rectangle {
            anchors.fill: parent
            radius: Math.max(1, Math.round(width / 2))
            color: root.steelHole
          }

          Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 1
            color: Qt.rgba(root.steelHi.r, root.steelHi.g, root.steelHi.b, 0.4)
          }

          Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 1
            color: Qt.rgba(0, 0, 0, 0.32)
          }
        }
      }
    }
  }
}
