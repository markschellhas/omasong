import QtQuick
import qs.Commons
import qs.Ui

Item {
  id: root

  property color foreground
  property color dim
  property int bpm: 120
  property bool playing: false
  property bool looping: true
  property int currentBar: 1
  property int currentBeat: 1
  property string statusText: ""
  property string songTitle: "Untitled"

  signal playRequested
  signal stopRequested
  signal loopToggled
  signal bpmChangedByUser(int value)
  signal titleEdited(string value)
  signal saveRequested
  signal openRequested

  readonly property int beatPulseMs: Math.max(200, Math.round(60000 / Math.max(40, bpm)))

  function commitTitle() {
    var next = titleInput.text.trim()
    if (next === "")
      next = "Untitled"
    if (next !== root.songTitle)
      root.titleEdited(next)
  }

  Row {
    id: leftCluster
    anchors.left: parent.left
    anchors.verticalCenter: parent.verticalCenter
    spacing: Style.spacing.sm

    Rectangle {
      anchors.verticalCenter: parent.verticalCenter
      width: Style.space(220)
      height: Style.space(28)
      radius: Math.max(2, Style.cornerRadius / 2)
      color: "transparent"
      border.width: 1
      border.color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.2)

      TextInput {
        id: titleInput
        anchors.fill: parent
        anchors.margins: 4
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
        verticalAlignment: Text.AlignVCenter
        selectByMouse: true
        clip: true
        onEditingFinished: root.commitTitle()
      }
    }

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: "Save"
      tooltipText: "Save song to library"
      focusable: true
      foreground: root.foreground
      accent: Color.accent
      onClicked: root.saveRequested()
    }

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: "Open"
      tooltipText: "Open a saved song"
      focusable: true
      foreground: root.foreground
      accent: Color.accent
      onClicked: root.openRequested()
    }
  }

  Row {
    id: rightCluster
    anchors.right: parent.right
    anchors.verticalCenter: parent.verticalCenter
    spacing: Style.spacing.sm

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: root.playing ? "Stop" : "Play"
      iconText: root.playing ? "\uf04d" : "\uf04b"
      tooltipText: root.playing ? "Stop" : "Play the song"
      focusable: true
      foreground: root.foreground
      accent: Color.accent
      onClicked: {
        if (root.playing)
          root.stopRequested()
        else
          root.playRequested()
      }
    }

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: root.looping ? "Loop on" : "Loop"
      selected: root.looping
      bordered: true
      tooltipText: "Repeat the song"
      focusable: true
      foreground: root.foreground
      accent: Color.accent
      onClicked: root.loopToggled()
    }

    Rectangle {
      anchors.verticalCenter: parent.verticalCenter
      width: 1
      height: parent.height * 0.55
      color: root.dim
      opacity: 0.35
    }

    Text {
      anchors.verticalCenter: parent.verticalCenter
      text: "BPM"
      color: root.dim
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.caption
    }

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: "−"
      tooltipText: "Slower"
      focusable: true
      foreground: root.foreground
      onClicked: root.bpmChangedByUser(root.bpm - 1)
    }

    Rectangle {
      anchors.verticalCenter: parent.verticalCenter
      width: Style.space(56)
      height: Style.space(28)
      radius: Math.max(2, Style.cornerRadius / 2)
      color: "transparent"
      border.width: 1
      border.color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.2)

      TextInput {
        id: bpmInput
        anchors.fill: parent
        anchors.margins: 4
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.body
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        inputMethodHints: Qt.ImhDigitsOnly
        validator: IntValidator { bottom: 40; top: 240 }
        onEditingFinished: {
          var n = parseInt(text, 10)
          if (isFinite(n) && n !== root.bpm)
            root.bpmChangedByUser(n)
        }
      }
    }

    Button {
      anchors.verticalCenter: parent.verticalCenter
      text: "+"
      tooltipText: "Faster"
      focusable: true
      foreground: root.foreground
      onClicked: root.bpmChangedByUser(root.bpm + 1)
    }

    Item { width: Style.spacing.md; height: 1 }

    Rectangle {
      id: beatDot
      anchors.verticalCenter: parent.verticalCenter
      width: Style.space(14)
      height: Style.space(14)
      radius: width / 2
      color: root.playing ? Color.accent : root.dim
      opacity: root.playing ? beatPulse.phase : 0.35

      SequentialAnimation {
        id: beatPulse
        property real phase: 1
        running: root.playing
        loops: Animation.Infinite
        NumberAnimation { target: beatPulse; property: "phase"; from: 1; to: 0.35; duration: root.beatPulseMs / 2 }
        NumberAnimation { target: beatPulse; property: "phase"; from: 0.35; to: 1; duration: root.beatPulseMs / 2 }
      }
    }

    Text {
      anchors.verticalCenter: parent.verticalCenter
      text: root.currentBar + " : " + root.currentBeat
      color: root.foreground
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.body
      font.bold: true
    }

    Text {
      anchors.verticalCenter: parent.verticalCenter
      visible: root.statusText !== ""
      text: root.statusText
      color: root.dim
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.caption
      elide: Text.ElideRight
    }
  }

  Binding {
    target: bpmInput
    property: "text"
    value: String(root.bpm)
    when: bpmInput && !bpmInput.activeFocus
  }

  Binding {
    target: titleInput
    property: "text"
    value: root.songTitle
    when: titleInput && !titleInput.activeFocus
  }
}
