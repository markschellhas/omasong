import QtQuick
import qs.Commons
import qs.Ui
import "js/Guitar.js" as Guitar
import "js/Model.js" as Model

Item {
  id: root

  property color foreground
  property color dim
  property var chord: null
  property bool vertical: false

  readonly property var voicing: root.chord && root.chord.rootPc !== undefined
    ? Guitar.voicingFor(root.chord.rootPc, root.chord.quality)
    : null
  readonly property var lines: Guitar.tabLines(root.voicing, root.vertical ? "vertical" : "horizontal")
  readonly property string chordLabel: root.voicing
    ? Model.chordName(root.voicing.rootPc, root.voicing.quality)
    : ""
  readonly property string tabText: Guitar.tabBlock(root.voicing, root.vertical ? "vertical" : "horizontal")

  Accessible.role: Accessible.StaticText
  Accessible.name: root.chordLabel
    ? root.chordLabel + (root.vertical ? " guitar tab, vertical\n" : " guitar tab\n") + root.tabText
    : "Guitar tab, no chord"

  Column {
    anchors.fill: parent
    anchors.leftMargin: Style.space(8)
    anchors.rightMargin: Style.space(4)
    anchors.topMargin: Style.space(2)
    anchors.bottomMargin: Style.space(2)
    spacing: Style.space(4)

    Item {
      width: parent.width
      height: Style.space(28)

      Text {
        anchors.left: parent.left
        anchors.right: orientationButton.left
        anchors.rightMargin: Style.space(4)
        anchors.verticalCenter: parent.verticalCenter
        height: parent.height
        text: root.chordLabel || "—"
        color: root.chordLabel ? root.foreground : root.dim
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
        font.bold: !!root.chordLabel
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
      }

      Button {
        id: orientationButton
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        text: root.vertical ? "═" : "‖"
        tooltipText: root.vertical ? "Show strings horizontally" : "Show strings vertically"
        selected: root.vertical
        foreground: root.vertical ? root.foreground : root.dim
        Accessible.name: tooltipText
        onClicked: root.vertical = !root.vertical
      }
    }

    Item {
      width: parent.width
      height: parent.height - Style.space(32)

      Column {
        anchors.fill: parent
        visible: !root.vertical
        spacing: 0

        Repeater {
          model: root.lines
          delegate: Item {
            required property var modelData
            width: parent.width
            height: Math.floor(parent.height / 6)

            Text {
              id: stringName
              width: Style.space(14)
              anchors.left: parent.left
              anchors.verticalCenter: parent.verticalCenter
              text: modelData.name
              color: root.dim
              font.family: Style.font.menuFamily
              font.pixelSize: Style.font.caption
              horizontalAlignment: Text.AlignHCenter
            }

            Item {
              anchors.left: stringName.right
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              height: parent.height

              Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                height: 1
                color: root.dim
                opacity: 0.4
              }

              Rectangle {
                anchors.centerIn: parent
                width: fretLabel.implicitWidth + Style.space(6)
                height: fretLabel.implicitHeight
                color: Color.menu.background

                Text {
                  id: fretLabel
                  anchors.centerIn: parent
                  text: modelData.glyph
                  color: modelData.glyph === "-" || modelData.glyph === "x" ? root.dim : root.foreground
                  font.family: Style.font.menuFamily
                  font.pixelSize: Style.font.body
                  font.bold: modelData.glyph !== "-" && modelData.glyph !== "x"
                }
              }
            }
          }
        }
      }

      Row {
        anchors.fill: parent
        visible: root.vertical
        spacing: 0

        Repeater {
          model: root.lines
          delegate: Item {
            required property var modelData
            width: Math.floor(parent.width / 6)
            height: parent.height

            Text {
              id: verticalStringName
              anchors.top: parent.top
              anchors.horizontalCenter: parent.horizontalCenter
              width: parent.width
              height: Style.space(16)
              text: modelData.name
              color: root.dim
              font.family: Style.font.menuFamily
              font.pixelSize: Style.font.caption
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
            }

            Item {
              anchors.top: verticalStringName.bottom
              anchors.bottom: parent.bottom
              anchors.horizontalCenter: parent.horizontalCenter
              width: parent.width

              Rectangle {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: 1
                color: root.dim
                opacity: 0.4
              }

              Rectangle {
                anchors.centerIn: parent
                width: verticalFretLabel.implicitWidth + Style.space(4)
                height: verticalFretLabel.implicitHeight
                color: Color.menu.background

                Text {
                  id: verticalFretLabel
                  anchors.centerIn: parent
                  text: modelData.glyph
                  color: modelData.glyph === "-" || modelData.glyph === "x" ? root.dim : root.foreground
                  font.family: Style.font.menuFamily
                  font.pixelSize: Style.font.body
                  font.bold: modelData.glyph !== "-" && modelData.glyph !== "x"
                }
              }
            }
          }
        }
      }
    }
  }
}
