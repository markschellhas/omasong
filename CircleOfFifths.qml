import QtQuick
import QtQuick.Shapes
import qs.Commons
import qs.Ui
import "js/Model.js" as Model

Item {
  id: root

  property color foreground
  property color dim
  property color faint
  property int keyIndex: 0
  property int soundingIndex: -1
  property string soundingRing: ""
  property string chordDragPayload: ""

  readonly property var selected: Model.keyAt(keyIndex)
  readonly property var chips: Model.diatonicTriads(keyIndex)
  readonly property color onSelected: Color.menu.background
  readonly property color gridColor: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.35)
  readonly property color hoverFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.16)
  readonly property color soundingFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.28)
  readonly property color wedgeFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.10)
  readonly property int wedgeStroke: Math.max(3, Style.space(3))
  readonly property int cellStroke: Math.max(2, Style.space(2))

  signal tonicPicked(int index, string ring)
  signal chordPreviewed(int index, string ring, var triad)
  signal chordDragStarted(string payload)

  function step(delta) {
    root.tonicPicked(Model.rotate(root.keyIndex, delta), "major")
  }

  function stationChord(index, ringName) {
    var minor = ringName === "minor"
    var pc = Model.tonicPc(index)
    if (minor)
      pc = Model.wrapPitchClass(pc + 9)
    return { rootPc: pc, quality: minor ? "minor" : "major" }
  }

  function cellFill(index, ringName) {
    if (index === root.keyIndex)
      return root.foreground
    if (index === root.soundingIndex && root.soundingRing === ringName)
      return root.soundingFill
    if (index === ring.hoverIndex && ring.hoverRing === ringName)
      return root.hoverFill
    if (Model.inKeyWedge(index, root.keyIndex))
      return root.wedgeFill
    return "transparent"
  }

  function triadFromChord(chord) {
    var notes = Model.triadMidi(chord)
    return {
      notes: notes,
      label: Model.chordName(chord.rootPc, chord.quality),
      rootPc: chord.rootPc,
      quality: chord.quality
    }
  }

  function preview(index, ringName) {
    var t = Model.triad(index, ringName)
    root.soundingIndex = index
    root.soundingRing = ringName
    soundingTimer.restart()
    root.chordPreviewed(index, ringName, t)
  }

  function previewChip(degreeIndex) {
    var chord = root.chips[degreeIndex]
    if (!chord)
      return
    var t = root.triadFromChord(chord)
    root.soundingIndex = -1
    root.soundingRing = ""
    soundingTimer.restart()
    root.chordPreviewed(-1, "chip", t)
  }

  function beginChordDrag(chord) {
    if (!chord)
      return ""
    var payload = Model.encodeChord(chord)
    root.chordDragPayload = payload
    root.chordDragStarted(payload)
    return payload
  }

  function startChordDragOn(item, chord) {
    var payload = root.beginChordDrag(chord)
    if (!payload)
      return ""
    item.Drag.mimeData = { "text/plain": payload }
    return payload
  }

  function onWedgeClicked(index, ringName) {
    root.tonicPicked(index, ringName)
  }

  Timer {
    id: soundingTimer
    interval: 750
    onTriggered: {
      root.soundingIndex = -1
      root.soundingRing = ""
    }
  }

  component AnnularWedge: Shape {
    id: wedge
    property real cx
    property real cy
    property real rInner
    property real rOuter
    property real startDeg
    property real sweepDeg
    property color fill: "transparent"
    property color stroke: "transparent"
    property real strokeWidth: 0

    antialiasing: true
    preferredRendererType: Shape.CurveRenderer

    ShapePath {
      fillColor: wedge.fill
      strokeColor: wedge.strokeWidth > 0 ? wedge.stroke : "transparent"
      strokeWidth: wedge.strokeWidth
      fillRule: ShapePath.WindingFill
      capStyle: ShapePath.FlatCap
      joinStyle: ShapePath.MiterJoin
      startX: Model.polarX(wedge.cx, wedge.rOuter, wedge.startDeg)
      startY: Model.polarY(wedge.cy, wedge.rOuter, wedge.startDeg)

      PathAngleArc {
        centerX: wedge.cx
        centerY: wedge.cy
        radiusX: wedge.rOuter
        radiusY: wedge.rOuter
        startAngle: wedge.startDeg
        sweepAngle: wedge.sweepDeg
        moveToStart: false
      }
      PathAngleArc {
        centerX: wedge.cx
        centerY: wedge.cy
        radiusX: wedge.rInner
        radiusY: wedge.rInner
        startAngle: wedge.startDeg + wedge.sweepDeg
        sweepAngle: -wedge.sweepDeg
        moveToStart: false
      }
      PathLine {
        x: Model.polarX(wedge.cx, wedge.rOuter, wedge.startDeg)
        y: Model.polarY(wedge.cy, wedge.rOuter, wedge.startDeg)
      }
    }
  }

  component RingOutline: Rectangle {
    property real ringRadius
    width: ringRadius * 2
    height: ringRadius * 2
    radius: ringRadius
    color: "transparent"
    border.width: 1
    border.color: root.gridColor
    anchors.centerIn: parent
    antialiasing: true
  }

  component KeyLabel: Text {
    id: keyLabel
    property int sector
    property real labelRadius
    property bool majorRing
    readonly property string ringName: majorRing ? "major" : "minor"
    readonly property int visual: Model.visualSector(sector, root.keyIndex)
    readonly property bool active: sector === root.keyIndex
    readonly property bool inWedge: Model.inKeyWedge(sector, root.keyIndex)
    readonly property bool hovered: sector === ring.hoverIndex && ring.hoverRing === ringName
    readonly property bool sounding: sector === root.soundingIndex && root.soundingRing === ringName

    x: Model.polarX(ring.cx, labelRadius, Model.sectorMidDeg(visual)) - width / 2
    y: Model.polarY(ring.cy, labelRadius, Model.sectorMidDeg(visual)) - height / 2
    text: majorRing ? Model.keyAt(sector).major : Model.keyAt(sector).minor
    color: active ? root.onSelected : root.foreground
    opacity: active || hovered || sounding || inWedge ? 1 : 0.55
    font.family: Style.font.menuFamily
    font.pixelSize: majorRing ? Style.font.body : Style.font.caption
    font.bold: active
  }

  Column {
    anchors.fill: parent
    spacing: Style.space(8)

    Text {
      width: parent.width
      text: selected.major + " major · " + selected.minor + " minor"
      color: root.foreground
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.subtitle
      font.bold: true
      horizontalAlignment: Text.AlignHCenter
    }

    Text {
      width: parent.width
      text: selected.accidentals === "0" ? "no sharps or flats" : selected.accidentals
      color: root.dim
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.caption
      horizontalAlignment: Text.AlignHCenter
    }

    Item {
      id: ring
      width: parent.width
      height: Math.max(Style.space(180), parent.height - Style.space(108))

      property int hoverIndex: -1
      property string hoverRing: ""
      property bool dragging: false
      property var pressHit: null
      property real pressX: 0
      property real pressY: 0
      readonly property real cx: width / 2
      readonly property real cy: height / 2
      readonly property real outerR: Math.min(width, height) / 2 - Style.space(6)
      readonly property real majorOuterR: outerR
      readonly property real majorInnerR: outerR * 0.64
      readonly property real minorOuterR: outerR * 0.60
      readonly property real minorInnerR: outerR * 0.32
      readonly property real splitR: (majorInnerR + minorOuterR) / 2
      readonly property real majorLabelR: (majorOuterR + majorInnerR) / 2
      readonly property real minorLabelR: (minorOuterR + minorInnerR) / 2

      function pick(px, py) {
        return Model.hitTest(px, py, cx, cy, minorInnerR, minorOuterR, majorInnerR, majorOuterR, root.keyIndex)
      }

      function setHover(px, py) {
        var hit = pick(px, py)
        var nextIndex = hit ? hit.index : -1
        var nextRing = hit ? hit.ring : ""
        if (nextIndex === hoverIndex && nextRing === hoverRing)
          return
        hoverIndex = nextIndex
        hoverRing = nextRing
      }

      Repeater {
        model: 12
        delegate: AnnularWedge {
          required property int index
          readonly property int visual: Model.visualSector(index, root.keyIndex)
          readonly property bool inWedge: Model.inKeyWedge(index, root.keyIndex)
          anchors.fill: parent
          cx: ring.cx
          cy: ring.cy
          rInner: ring.majorInnerR
          rOuter: ring.majorOuterR
          startDeg: Model.sectorStartDeg(visual)
          sweepDeg: Model.sectorSweepDeg()
          fill: root.cellFill(index, "major")
          stroke: inWedge ? root.foreground : "transparent"
          strokeWidth: inWedge ? root.cellStroke : 0
        }
      }

      Repeater {
        model: 12
        delegate: AnnularWedge {
          required property int index
          readonly property int visual: Model.visualSector(index, root.keyIndex)
          readonly property bool inWedge: Model.inKeyWedge(index, root.keyIndex)
          anchors.fill: parent
          cx: ring.cx
          cy: ring.cy
          rInner: ring.minorInnerR
          rOuter: ring.minorOuterR
          startDeg: Model.sectorStartDeg(visual)
          sweepDeg: Model.sectorSweepDeg()
          fill: root.cellFill(index, "minor")
          stroke: inWedge ? root.foreground : "transparent"
          strokeWidth: inWedge ? root.cellStroke : 0
        }
      }

      RingOutline { ringRadius: ring.majorOuterR }
      RingOutline { ringRadius: ring.splitR }
      RingOutline { ringRadius: ring.minorInnerR }

      Shape {
        anchors.fill: parent
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
          fillColor: "transparent"
          strokeColor: root.gridColor
          strokeWidth: 1
          capStyle: ShapePath.FlatCap
          PathSvg { path: Model.radialSvg(ring.cx, ring.cy, ring.minorInnerR, ring.majorOuterR) }
        }
      }

      AnnularWedge {
        z: 4
        anchors.fill: parent
        cx: ring.cx
        cy: ring.cy
        rInner: ring.minorInnerR
        rOuter: ring.majorOuterR
        startDeg: Model.wedgeStartDeg(0)
        sweepDeg: Model.wedgeSweepDeg()
        fill: "transparent"
        stroke: root.foreground
        strokeWidth: root.wedgeStroke
      }

      Repeater {
        model: 12
        delegate: KeyLabel {
          required property int index
          sector: index
          labelRadius: ring.majorLabelR
          majorRing: true
        }
      }

      Repeater {
        model: 12
        delegate: KeyLabel {
          required property int index
          sector: index
          labelRadius: ring.minorLabelR
          majorRing: false
        }
      }

      MouseArea {
        id: ringMouse
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        cursorShape: ring.hoverIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        preventStealing: true

        Drag.active: ring.dragging
        Drag.dragType: Drag.Automatic
        Drag.proposedAction: Qt.CopyAction
        Drag.keys: ["text/plain"]

        onPressed: function(mouse) {
          ring.pressHit = ring.pick(mouse.x, mouse.y)
          ring.pressX = mouse.x
          ring.pressY = mouse.y
          ring.dragging = false
          if (ring.pressHit)
            root.preview(ring.pressHit.index, ring.pressHit.ring)
        }
        onPositionChanged: function(mouse) {
          if (pressed && ring.pressHit && !ring.dragging) {
            var dx = mouse.x - ring.pressX
            var dy = mouse.y - ring.pressY
            if (dx * dx + dy * dy >= 64) {
              root.startChordDragOn(ringMouse, root.stationChord(ring.pressHit.index, ring.pressHit.ring))
              ring.dragging = true
            }
          }
          if (!ring.dragging)
            ring.setHover(mouse.x, mouse.y)
        }
        onReleased: function(mouse) {
          if (!ring.dragging && ring.pressHit)
            root.onWedgeClicked(ring.pressHit.index, ring.pressHit.ring)
          ring.dragging = false
          ring.pressHit = null
        }
        onExited: {
          if (ring.dragging)
            return
          ring.hoverIndex = -1
          ring.hoverRing = ""
        }
      }

      WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function(event) {
          var dy = event.angleDelta.y
          var dx = event.angleDelta.x
          if (dy > 0 || dx > 0)
            root.step(-1)
          else if (dy < 0 || dx < 0)
            root.step(1)
        }
      }
    }

    Row {
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: Style.space(6)

      Repeater {
        model: 7
        delegate: Item {
          id: chip
          required property int index
          readonly property var chipChord: root.chips[index]
          implicitWidth: chipButton.implicitWidth
          implicitHeight: chipButton.implicitHeight
          width: implicitWidth
          height: implicitHeight
          property bool dragging: false
          property real pressX: 0
          property real pressY: 0

          Button {
            id: chipButton
            anchors.centerIn: parent
            enabled: false
            text: Model.NUMERALS[index]
            bordered: true
            foreground: root.foreground
            fontFamily: Style.font.menuFamily
            fontSize: Style.font.bodySmall
            tooltipText: chip.chipChord ? Model.chordName(chip.chipChord.rootPc, chip.chipChord.quality) : ""
          }

          MouseArea {
            id: chipMouse
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.PointingHandCursor
            preventStealing: true

            Drag.active: chip.dragging
            Drag.dragType: Drag.Automatic
            Drag.proposedAction: Qt.CopyAction
            Drag.keys: ["text/plain"]

            onPressed: function(mouse) {
              chip.pressX = mouse.x
              chip.pressY = mouse.y
              chip.dragging = false
            }
            onPositionChanged: function(mouse) {
              if (!pressed || chip.dragging || !chip.chipChord)
                return
              var dx = mouse.x - chip.pressX
              var dy = mouse.y - chip.pressY
              if (dx * dx + dy * dy >= 64) {
                root.startChordDragOn(chipMouse, chip.chipChord)
                chip.dragging = true
              }
            }
            onReleased: function() {
              if (!chip.dragging)
                root.previewChip(chip.index)
              chip.dragging = false
            }
          }
        }
      }
    }
  }
}
