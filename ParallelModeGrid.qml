import QtQuick
import qs.Commons
import qs.Ui
import "js/ParallelMode.js" as ParallelMode
import "js/Model.js" as Model

Item {
  id: root

  property color foreground
  property color dim
  property color faint
  property int rootPc: 0
  property int homeModeIndex: 1
  property bool useSevenths: false
  property bool showAllModes: false
  property var progression: []
  property int hoverMode: -1
  property int hoverDegree: -1
  property int selectedMode: -1
  property int selectedDegree: -1

  readonly property var gridRows: ParallelMode.buildGrid(
    rootPc, homeModeIndex, useSevenths, showAllModes)
  readonly property var duplicateHits: {
    if (hoverMode < 0 || hoverDegree < 0)
      return []
    return ParallelMode.duplicateCells(gridRows, hoverMode, hoverDegree, useSevenths, rootPc)
  }
  readonly property var selectedChord: selectedMode >= 0
    ? ParallelMode.cellChord(rootPc, selectedMode, selectedDegree, useSevenths)
    : null
  readonly property int controlStripHeight: Style.space(52)
  readonly property int progressionHeight: Style.space(28)
  readonly property int gridSide: Math.max(
    Style.space(120),
    Math.min(width, height - controlStripHeight - progressionHeight - Style.space(4)))

  signal chordAuditioned(var chord, var notes, string label)
  signal chordAdded(var chord)
  signal chordDragStarted(string payload)

  function isDuplicateHit(modeIndex, degreeIndex) {
    var i
    for (i = 0; i < duplicateHits.length; i++) {
      if (duplicateHits[i].modeIndex === modeIndex && duplicateHits[i].degreeIndex === degreeIndex)
        return true
    }
    return false
  }

  function isInProgression(modeIndex, degreeIndex) {
    var i
    for (i = 0; i < progression.length; i++) {
      if (progression[i].modeIndex === modeIndex && progression[i].degreeIndex === degreeIndex)
        return true
    }
    return false
  }

  function auditionCell(modeIndex, degreeIndex) {
    var chord = ParallelMode.cellChord(rootPc, modeIndex, degreeIndex, useSevenths)
    var notes = ParallelMode.chordMidiNotes(chord)
    root.chordAuditioned(chord, notes, chord.symbol)
  }

  function addCell(modeIndex, degreeIndex) {
    var next = progression.slice()
    next.push(ParallelMode.progressionEntry(modeIndex, degreeIndex))
    progression = next
    var chord = ParallelMode.cellChord(rootPc, modeIndex, degreeIndex, useSevenths)
    root.chordAdded(chord)
  }

  function shiftProgression(delta) {
    var shifted = ParallelMode.shiftProgressionRows(progression, delta)
    if (shifted)
      progression = shifted
  }

  function clearProgression() {
    progression = []
  }

  function stepRoot(delta) {
    rootPc = Model.wrapPitchClass(rootPc + delta)
  }

  Column {
    anchors.fill: parent
    spacing: Style.space(2)

    Item {
      width: parent.width
      height: root.gridSide
      anchors.horizontalCenter: parent.horizontalCenter

      readonly property int cols: 8
      readonly property int rows: root.gridRows.length + 1
      readonly property real cell: Math.floor(Math.min(width / cols, height / rows))

      Item {
        anchors.centerIn: parent
        width: cols * cell
        height: rows * cell

        Rectangle {
          x: 0
          y: 0
          width: cell
          height: cell
          color: "transparent"
        }

        Repeater {
          model: 7
          delegate: Text {
            required property int index
            x: (index + 1) * cell
            y: 0
            width: cell
            height: cell
            text: String(index + 1)
            color: root.dim
            font.family: Style.font.menuFamily
            font.pixelSize: Math.max(8, cell * 0.28)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
          }
        }

        Repeater {
          model: root.gridRows
          delegate: Item {
            id: rowItem
            required property int index
            required property var modelData
            readonly property var row: modelData
            readonly property int rowY: (index + 1) * cell
            readonly property bool isHome: row.modeIndex === root.homeModeIndex
            readonly property real distance: row.distanceFromHome

            Text {
              x: 0
              y: rowY
              width: cell
              height: cell
              text: row.modeName.slice(0, 3)
              color: rowItem.isHome ? root.foreground : root.dim
              font.family: Style.font.menuFamily
              font.pixelSize: Math.max(7, cell * 0.22)
              font.bold: rowItem.isHome
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
              elide: Text.ElideRight

              MouseArea {
                anchors.fill: parent
                onClicked: root.homeModeIndex = rowItem.row.modeIndex
              }
            }

            Rectangle {
              x: cell
              y: rowY
              width: cell * 7
              height: cell
              radius: rowItem.isHome ? 2 : 0
              color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.04 * rowItem.distance)
              border.width: rowItem.isHome ? 2 : 0
              border.color: root.foreground
              z: -1
            }

            Repeater {
              model: row.cells
              delegate: Rectangle {
                id: cellRect
                required property int index
                required property var modelData
                readonly property var cell: modelData
                readonly property bool dup: root.isDuplicateHit(cell.modeIndex, cell.degreeIndex)
                readonly property bool inProg: root.isInProgression(cell.modeIndex, cell.degreeIndex)
                readonly property bool selected: root.selectedMode === cell.modeIndex
                  && root.selectedDegree === cell.degreeIndex

                x: (index + 1) * cell
                y: rowItem.rowY
                width: cell
                height: cell
                color: {
                  if (selected)
                    return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.28)
                  if (dup)
                    return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.18)
                  if (inProg)
                    return Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.22)
                  if (cell.changedFromAbove)
                    return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.10)
                  return "transparent"
                }
                opacity: cell.changedFromAbove ? 1 : (rowItem.row.modeIndex === root.hoverMode ? 1 : 0.92)
                border.width: cell.unstableTonic ? 1 : (inProg ? 1 : 0)
                border.color: cell.unstableTonic ? root.dim : Color.accent

                Column {
                  anchors.centerIn: parent
                  width: parent.width - 2
                  spacing: 0

                  Text {
                    width: parent.width
                    text: cell.chord.symbol
                    color: root.foreground
                    font.family: Style.font.menuFamily
                    font.pixelSize: Math.max(7, cellRect.width * 0.26)
                    font.bold: cellRect.selected
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                  }

                  Text {
                    width: parent.width
                    visible: cellRect.width > Style.space(26)
                    text: cell.numeral
                    color: root.dim
                    font.family: Style.font.menuFamily
                    font.pixelSize: Math.max(6, cellRect.width * 0.2)
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    maximumLineCount: 1
                  }

                  Text {
                    width: parent.width
                    visible: cellRect.width > Style.space(34)
                    text: {
                      if (cell.unstableTonic)
                        return "°"
                      return cell.diatonic ? "·" : "○"
                    }
                    color: cell.diatonic ? root.dim : root.foreground
                    font.family: Style.font.menuFamily
                    font.pixelSize: Math.max(6, cellRect.width * 0.18)
                    horizontalAlignment: Text.AlignHCenter
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  hoverEnabled: true
                  acceptedButtons: Qt.LeftButton
                  cursorShape: Qt.PointingHandCursor
                  preventStealing: true

                  property bool dragging: false
                  property real pressX: 0
                  property real pressY: 0

                  onEntered: {
                    root.hoverMode = cell.modeIndex
                    root.hoverDegree = cell.degreeIndex
                  }
                  onExited: {
                    if (root.hoverMode === cell.modeIndex && root.hoverDegree === cell.degreeIndex) {
                      root.hoverMode = -1
                      root.hoverDegree = -1
                    }
                  }
                  onPressed: function(mouse) {
                    pressX = mouse.x
                    pressY = mouse.y
                    dragging = false
                    root.selectedMode = cell.modeIndex
                    root.selectedDegree = cell.degreeIndex
                    root.auditionCell(cell.modeIndex, cell.degreeIndex)
                  }
                  onPositionChanged: function(mouse) {
                    if (!pressed || dragging)
                      return
                    var dx = mouse.x - pressX
                    var dy = mouse.y - pressY
                    if (dx * dx + dy * dy < 64)
                      return
                    var payload = Model.encodeChord(ParallelMode.toTriadPayload(cell.chord))
                    if (!payload)
                      return
                    dragging = true
                    root.chordDragStarted(payload)
                    Drag.active = true
                    Drag.dragType = Drag.Automatic
                    Drag.proposedAction = Qt.CopyAction
                    Drag.keys = ["text/plain"]
                    Drag.mimeData = { "text/plain": payload }
                  }
                  onReleased: function() {
                    dragging = false
                  }
                  onDoubleClicked: root.addCell(cell.modeIndex, cell.degreeIndex)
                }
              }
            }
          }
        }
      }
    }

    Column {
      width: parent.width
      spacing: Style.space(2)

      Row {
        width: parent.width
        spacing: Style.space(2)

        Button {
          text: "◀"
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Lower root"
          onClicked: root.stepRoot(-1)
        }

        Text {
          anchors.verticalCenter: parent.verticalCenter
          width: Style.space(28)
          text: ParallelMode.rootName(root.rootPc)
          color: root.foreground
          font.family: Style.font.menuFamily
          font.pixelSize: Style.font.caption
          horizontalAlignment: Text.AlignHCenter
        }

        Button {
          text: "▶"
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Raise root"
          onClicked: root.stepRoot(1)
        }

        Button {
          text: root.useSevenths ? "7ths" : "3"
          selected: root.useSevenths
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Triads vs seventh chords"
          onClicked: root.useSevenths = !root.useSevenths
        }

        Button {
          text: root.showAllModes ? "7" : "4"
          selected: root.showAllModes
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: root.showAllModes ? "Seven modes" : "Common four modes"
          onClicked: root.showAllModes = !root.showAllModes
        }
      }

      Row {
        width: parent.width
        height: root.progressionHeight
        spacing: Style.space(2)

        Button {
          text: "▲"
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Brighten progression (up a row)"
          enabled: root.progression.length > 0
          onClicked: root.shiftProgression(-1)
        }

        Button {
          text: "▼"
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Darken progression (down a row)"
          enabled: root.progression.length > 0
          onClicked: root.shiftProgression(1)
        }

        Rectangle {
          width: parent.width - Style.space(72)
          height: parent.height
          color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.06)
          radius: 2
          clip: true

          Row {
            anchors.fill: parent
            anchors.margins: Style.space(2)
            spacing: Style.space(2)

            Repeater {
              model: root.progression
              delegate: Text {
                required property int index
                required property var modelData
                readonly property var chord: ParallelMode.cellChord(
                  root.rootPc, modelData.modeIndex, modelData.degreeIndex, root.useSevenths)
                text: chord.symbol
                color: root.foreground
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.caption
                anchors.verticalCenter: parent.verticalCenter
              }
            }
          }
        }

        Button {
          text: "×"
          bordered: true
          foreground: root.foreground
          fontSize: Style.font.caption
          tooltipText: "Clear progression"
          enabled: root.progression.length > 0
          onClicked: root.clearProgression()
        }
      }
    }
  }
}
