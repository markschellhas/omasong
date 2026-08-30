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

  readonly property var voicing: root.chord && root.chord.rootPc !== undefined
    ? Guitar.voicingFor(root.chord.rootPc, root.chord.quality)
    : null
  readonly property var lines: Guitar.tabLines(root.voicing)
  readonly property string chordLabel: root.voicing
    ? Model.chordName(root.voicing.rootPc, root.voicing.quality)
    : ""
  readonly property string tabText: Guitar.tabBlock(root.voicing)

  Accessible.role: Accessible.StaticText
  Accessible.name: root.chordLabel
    ? root.chordLabel + " guitar tab\n" + root.tabText
    : "Guitar tab, no chord"

  Column {
    anchors.fill: parent
    anchors.leftMargin: Style.space(8)
    anchors.rightMargin: Style.space(4)
    anchors.topMargin: Style.space(2)
    anchors.bottomMargin: Style.space(2)
    spacing: Style.space(4)

    Text {
      width: parent.width
      height: Style.space(20)
      text: root.chordLabel || "—"
      color: root.chordLabel ? root.foreground : root.dim
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.body
      font.bold: !!root.chordLabel
      horizontalAlignment: Text.AlignHCenter
      verticalAlignment: Text.AlignVCenter
      elide: Text.ElideRight
    }

    Column {
      width: parent.width
      height: parent.height - Style.space(24)
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
  }
}
