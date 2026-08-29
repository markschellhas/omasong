import QtQuick
import qs.Commons
import qs.Ui
import "js/Keyboard.js" as Keys

Item {
  id: root

  property color foreground
  property color dim
  property int octave: 4
  property int instrument: 0
  property string layoutName: "qwerty"
  property bool laptopKeys: false
  property var activeNotes: []

  signal noteOn(int midi)
  signal noteOff(int midi)
  signal instrumentChangedByUser(int value)
  signal laptopToggled

  readonly property var keys: Keys.pianoKeysC3C5()
  readonly property var whiteKeys: keys.filter(function(k) { return k.type === "white" })
  readonly property var blackKeys: keys.filter(function(k) { return k.type === "black" })
  readonly property string instrumentLabel: Keys.instrumentName(root.instrument)

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

      Button {
        text: "‹"
        bordered: true
        tooltipText: "Previous sound"
        foreground: root.foreground
        onClicked: root.instrumentChangedByUser(Keys.wrapInstrument(root.instrument - 1))
      }

      Text {
        anchors.verticalCenter: parent.verticalCenter
        width: Style.space(110)
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        text: root.instrumentLabel
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
      }

      Button {
        text: "›"
        bordered: true
        tooltipText: "Next sound"
        foreground: root.foreground
        onClicked: root.instrumentChangedByUser(Keys.wrapInstrument(root.instrument + 1))
      }

      Item { width: Style.spacing.md; height: 1 }

      Button {
        iconText: "\uf11c"
        tooltipText: root.laptopKeys ? "Laptop keys on" : "Laptop keys"
        bordered: true
        selected: root.laptopKeys
        foreground: root.laptopKeys ? root.foreground : root.dim
        onClicked: root.laptopToggled()
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
                visible: root.laptopKeys && root.computerKey(modelData.midi) !== ""
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
          readonly property int octaveOffset: (modelData.octave - 3) * 7
          width: Math.max(18, board.width / 24)
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
            visible: root.laptopKeys && root.computerKey(modelData.midi) !== ""
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
