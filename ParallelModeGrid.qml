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

  readonly property int modeCount: ParallelMode.visibleModeCount(showAllModes)
  readonly property var selectedChord: selectedMode >= 0
    ? ParallelMode.cellChord(rootPc, selectedMode, selectedDegree, useSevenths)
    : null

  signal chordAuditioned(var chord, var notes, string label)
  signal chordAdded(var chord)
  signal chordDragStarted(string payload)

  function modeAt(rowIndex) {
    return ParallelMode.visibleModeIndex(rowIndex, showAllModes)
  }

  function prevModeAt(rowIndex) {
    return rowIndex > 0 ? modeAt(rowIndex - 1) : -1
  }

  function infoAt(rowIndex, degreeIndex) {
    return ParallelMode.cellInfo(
      rootPc, modeAt(rowIndex), degreeIndex, homeModeIndex, useSevenths, prevModeAt(rowIndex))
  }

  function isDuplicateHit(modeIndex, degreeIndex) {
    if (hoverMode < 0 || hoverDegree < 0)
      return false
    var hits = ParallelMode.duplicateCells(
      ParallelMode.buildGrid(rootPc, homeModeIndex, useSevenths, showAllModes),
      hoverMode, hoverDegree, useSevenths, rootPc)
    var i
    for (i = 0; i < hits.length; i++) {
      if (hits[i].modeIndex === modeIndex && hits[i].degreeIndex === degreeIndex)
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
    root.chordAuditioned(chord, ParallelMode.chordMidiNotes(chord), chord.symbol)
  }

  function addCell(modeIndex, degreeIndex) {
    var next = progression.slice()
    next.push(ParallelMode.progressionEntry(modeIndex, degreeIndex))
    progression = next
    root.chordAdded(ParallelMode.cellChord(rootPc, modeIndex, degreeIndex, useSevenths))
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

  function cellPayload(modeIndex, degreeIndex) {
    var chord = ParallelMode.toTriadPayload(
      ParallelMode.cellChord(rootPc, modeIndex, degreeIndex, useSevenths))
    return Model.encodeChord(chord)
  }

  function startCellDragOn(item, modeIndex, degreeIndex) {
    var payload = root.cellPayload(modeIndex, degreeIndex)
    if (!payload)
      return ""
    root.chordDragStarted(payload)
    item.Drag.mimeData = { "text/plain": payload }
    return payload
  }

  Item {
    id: gridHost
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: strip.top
    anchors.bottomMargin: Style.space(4)
    clip: true

    readonly property int gridCols: 8
    readonly property int gridRows: root.modeCount + 1
    readonly property real cellW: Math.max(14, Math.floor(width / gridCols))
    readonly property real cellH: Math.max(14, Math.floor(height / gridRows))

    Column {
      anchors.centerIn: parent
      width: gridHost.cellW * gridHost.gridCols
      height: gridHost.cellH * gridHost.gridRows
      spacing: 0

      Row {
        width: parent.width
        height: gridHost.cellH
        spacing: 0

        Item {
          width: gridHost.cellW
          height: gridHost.cellH
        }

        Repeater {
          model: 7
          delegate: Text {
            required property int index
            width: gridHost.cellW
            height: gridHost.cellH
            text: String(index + 1)
            color: root.dim
            font.family: Style.font.menuFamily
            font.pixelSize: Math.max(8, Math.round(gridHost.cellH * 0.32))
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
          }
        }
      }

      Repeater {
        model: root.modeCount
        delegate: Row {
          id: modeRow
          required property int index
          readonly property int modeIndex: root.modeAt(index)
          readonly property int distance: Math.abs(modeIndex - root.homeModeIndex)
          readonly property bool isHome: modeIndex === root.homeModeIndex

          width: parent.width
          height: gridHost.cellH
          spacing: 0

          Rectangle {
            width: gridHost.cellW
            height: gridHost.cellH
            color: modeRow.isHome
              ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.16)
              : "transparent"
            border.width: modeRow.isHome ? 1 : 0
            border.color: root.foreground

            Text {
              anchors.fill: parent
              anchors.margins: 1
              text: gridHost.cellW >= 36
                ? ParallelMode.modeName(modeRow.modeIndex)
                : ParallelMode.modeAbbrev(modeRow.modeIndex)
              color: modeRow.isHome ? root.foreground : root.dim
              font.family: Style.font.menuFamily
              font.pixelSize: Math.max(7, Math.round(gridHost.cellH * 0.28))
              font.bold: modeRow.isHome
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
              elide: Text.ElideRight
              wrapMode: Text.NoWrap
              maximumLineCount: 1
            }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.homeModeIndex = modeRow.modeIndex
            }
          }

          Repeater {
            model: 7
            delegate: Rectangle {
              id: chordCell
              required property int index
              readonly property var info: root.infoAt(modeRow.index, index)
              readonly property bool dup: root.isDuplicateHit(info.modeIndex, info.degreeIndex)
              readonly property bool inProg: root.isInProgression(info.modeIndex, info.degreeIndex)
              readonly property bool selected: root.selectedMode === info.modeIndex
                && root.selectedDegree === info.degreeIndex
              readonly property bool showNumeral: gridHost.cellH >= 28 && gridHost.cellW >= 24
              readonly property bool showMarker: gridHost.cellH >= 36 && gridHost.cellW >= 30

              width: gridHost.cellW
              height: gridHost.cellH
              color: {
                if (selected)
                  return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.28)
                if (dup)
                  return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.18)
                if (inProg)
                  return Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.22)
                if (info.changedFromAbove)
                  return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.12)
                return Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.04 * modeRow.distance)
              }
              opacity: info.changedFromAbove ? 1 : 0.72
              border.width: info.unstableTonic ? 1 : (modeRow.isHome ? 1 : 1)
              border.color: info.unstableTonic
                ? root.dim
                : (inProg ? Color.accent : Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.22))

              Column {
                anchors.centerIn: parent
                width: parent.width - 2
                spacing: 0

                Text {
                  width: parent.width
                  text: chordCell.info.symbol
                  color: root.foreground
                  font.family: Style.font.menuFamily
                  font.pixelSize: Math.max(7, Math.round(Math.min(chordCell.width, chordCell.height) * 0.28))
                  font.bold: chordCell.selected
                  horizontalAlignment: Text.AlignHCenter
                  elide: Text.ElideRight
                  wrapMode: Text.NoWrap
                  maximumLineCount: 1
                }

                Text {
                  width: parent.width
                  visible: chordCell.showNumeral
                  text: chordCell.info.numeral
                  color: root.dim
                  font.family: Style.font.menuFamily
                  font.pixelSize: Math.max(6, Math.round(chordCell.height * 0.2))
                  horizontalAlignment: Text.AlignHCenter
                  elide: Text.ElideRight
                  wrapMode: Text.NoWrap
                  maximumLineCount: 1
                }

                Text {
                  width: parent.width
                  visible: chordCell.showMarker
                  text: chordCell.info.unstableTonic ? "°" : (chordCell.info.diatonic ? "·" : "○")
                  color: chordCell.info.diatonic ? root.dim : root.foreground
                  font.family: Style.font.menuFamily
                  font.pixelSize: Math.max(6, Math.round(chordCell.height * 0.16))
                  horizontalAlignment: Text.AlignHCenter
                }
              }

              MouseArea {
                id: cellMouse
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton
                cursorShape: dragging ? Qt.DragCopyCursor : Qt.PointingHandCursor
                preventStealing: true

                property bool dragging: false
                property real pressX: 0
                property real pressY: 0

                Drag.active: dragging
                Drag.dragType: Drag.Automatic
                Drag.proposedAction: Qt.CopyAction
                Drag.keys: ["text/plain"]

                onEntered: {
                  root.hoverMode = chordCell.info.modeIndex
                  root.hoverDegree = chordCell.info.degreeIndex
                }
                onExited: {
                  if (dragging)
                    return
                  if (root.hoverMode === chordCell.info.modeIndex
                      && root.hoverDegree === chordCell.info.degreeIndex) {
                    root.hoverMode = -1
                    root.hoverDegree = -1
                  }
                }
                onPressed: function(mouse) {
                  pressX = mouse.x
                  pressY = mouse.y
                  dragging = false
                  root.selectedMode = chordCell.info.modeIndex
                  root.selectedDegree = chordCell.info.degreeIndex
                  root.auditionCell(chordCell.info.modeIndex, chordCell.info.degreeIndex)
                }
                onPositionChanged: function(mouse) {
                  if (!pressed || dragging)
                    return
                  var dx = mouse.x - pressX
                  var dy = mouse.y - pressY
                  if (dx * dx + dy * dy < 64)
                    return
                  if (root.startCellDragOn(cellMouse, chordCell.info.modeIndex, chordCell.info.degreeIndex))
                    dragging = true
                }
                onReleased: function() {
                  dragging = false
                }
                onDoubleClicked: root.addCell(chordCell.info.modeIndex, chordCell.info.degreeIndex)
              }
            }
          }
        }
      }
    }
  }

  Column {
    id: strip
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
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

    Item {
      width: parent.width
      height: Style.space(28)

      Button {
        id: shiftUp
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        text: "▲"
        bordered: true
        foreground: root.foreground
        fontSize: Style.font.caption
        tooltipText: "Brighten progression (up a row)"
        enabled: root.progression.length > 0
        onClicked: root.shiftProgression(-1)
      }

      Button {
        id: shiftDown
        anchors.left: shiftUp.right
        anchors.leftMargin: Style.space(2)
        anchors.verticalCenter: parent.verticalCenter
        text: "▼"
        bordered: true
        foreground: root.foreground
        fontSize: Style.font.caption
        tooltipText: "Darken progression (down a row)"
        enabled: root.progression.length > 0
        onClicked: root.shiftProgression(1)
      }

      Button {
        id: clearProg
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        text: "×"
        bordered: true
        foreground: root.foreground
        fontSize: Style.font.caption
        tooltipText: "Clear progression"
        enabled: root.progression.length > 0
        onClicked: root.clearProgression()
      }

      Rectangle {
        anchors.left: shiftDown.right
        anchors.right: clearProg.left
        anchors.leftMargin: Style.space(2)
        anchors.rightMargin: Style.space(2)
        anchors.verticalCenter: parent.verticalCenter
        height: parent.height
        color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.06)
        radius: 2
        clip: true

        Row {
          anchors.fill: parent
          anchors.margins: Style.space(2)
          spacing: Style.space(4)

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
              wrapMode: Text.NoWrap
            }
          }
        }
      }
    }
  }
}
