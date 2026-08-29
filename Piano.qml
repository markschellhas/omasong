import QtQuick
import qs.Commons
import qs.Ui
import "js/Keyboard.js" as Keys

Item {
  id: root

  property color foreground
  property color dim
  property int octave: 4
  property string layoutName: "qwerty"
  property var activeNotes: []
  property bool sustain: false

  signal noteOn(int midi)
  signal noteOff(int midi)
  signal octaveChangedByUser(int value)

  readonly property var keys: Keys.twoOctaveKeys(octave)
  readonly property var whiteKeys: keys.filter(function(k) { return k.type === "white" })
  readonly property var blackKeys: keys.filter(function(k) { return k.type === "black" })

  function isActive(midi) {
    return root.activeNotes && root.activeNotes.indexOf(midi) !== -1
  }

  function computerKey(midi) {
    return Keys.computerKeyForMidi(midi, root.octave, root.layoutName)
  }

  Column {
    anchors.fill: parent
    spacing: Style.space(6)

    Row {
      width: parent.width
      spacing: Style.spacing.sm

      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: "Keyboard"
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
        font.bold: true
      }

      Button {
        text: "Oct −"
        bordered: true
        foreground: root.foreground
        onClicked: root.octaveChangedByUser(root.octave - 1)
      }

      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: "C" + root.octave
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
      }

      Button {
        text: "Oct +"
        bordered: true
        foreground: root.foreground
        onClicked: root.octaveChangedByUser(root.octave + 1)
      }

      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: root.sustain ? "Sustain" : "Space sustain"
        color: root.sustain ? Color.accent : root.dim
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.caption
      }

      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: "white " + Keys.getLayout(root.layoutName).white.slice(0, 8).join(" ")
        color: root.dim
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.caption
      }
    }

    Item {
      id: board
      width: parent.width
      height: parent.height - Style.space(36)

      Row {
        id: whites
        anchors.fill: parent
        spacing: 1

        Repeater {
          model: root.whiteKeys
          delegate: Rectangle {
            required property var modelData
            width: (board.width - (root.whiteKeys.length - 1)) / root.whiteKeys.length
            height: board.height
            color: root.isActive(modelData.midi) ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.55) : "#f4f1ea"
            border.width: 1
            border.color: Qt.rgba(0, 0, 0, 0.28)
            radius: 2

            Column {
              anchors.horizontalCenter: parent.horizontalCenter
              anchors.bottom: parent.bottom
              anchors.bottomMargin: 6
              spacing: 2

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: modelData.label
                color: "#1f1b16"
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.caption
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: root.computerKey(modelData.midi) !== ""
                text: root.computerKey(modelData.midi).toUpperCase()
                color: "#5c564c"
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.caption
              }
            }

            MouseArea {
              anchors.fill: parent
              onPressed: root.noteOn(modelData.midi)
              onReleased: root.noteOff(modelData.midi)
              onCanceled: root.noteOff(modelData.midi)
            }
          }
        }
      }

      Repeater {
        model: root.blackKeys
        delegate: Rectangle {
          required property var modelData
          required property int index
          readonly property int octaveOffset: modelData.octave > root.octave ? 7 : 0
          width: Math.max(18, board.width / 22)
          height: board.height * 0.62
          x: (Keys.blackKeyLeftPercent(modelData.keyIndex, octaveOffset) / 100) * board.width - width / 2
          y: 0
          z: 2
          color: root.isActive(modelData.midi) ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.85) : "#161513"
          border.width: 1
          border.color: "#2c2a27"
          radius: 2

          Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 6
            visible: root.computerKey(modelData.midi) !== ""
            text: root.computerKey(modelData.midi).toUpperCase()
            color: "#f4f1ea"
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.caption
          }

          MouseArea {
            anchors.fill: parent
            onPressed: root.noteOn(modelData.midi)
            onReleased: root.noteOff(modelData.midi)
            onCanceled: root.noteOff(modelData.midi)
          }
        }
      }
    }
  }
}
