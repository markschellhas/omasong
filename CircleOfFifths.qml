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
  property int tonicIndex: 0
  property bool toneMode: false
  property int toneCursor: 0
  property int soundingIndex: -1
  property string soundingRing: ""

  readonly property var selected: Model.keyAt(tonicIndex)
  readonly property var chords: Model.diatonic(tonicIndex)
  readonly property color onSelected: Color.menu.background
  readonly property color gridColor: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.35)
  readonly property color hoverFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.16)
  readonly property color soundingFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.28)
  readonly property color wedgeFill: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.10)
  readonly property int wedgeStroke: Math.max(3, Style.space(3))
  readonly property int cellStroke: Math.max(2, Style.space(2))

  signal tonicPicked(int index, string ring)
  signal chordPreviewed(int index, string ring, var triad)

  function step(delta) {
    if (root.toneMode) {
      root.stepTone(delta)
      return
    }
    root.tonicPicked(Model.wrap(root.tonicIndex + delta), "major")
  }

  function stepTone(delta) {
    var list = Model.wedgeChords(root.tonicIndex)
    root.toneCursor = Model.wrapCursor(root.toneCursor + delta, list.length)
    var chord = list[root.toneCursor]
    root.preview(chord.index, chord.ring)
  }

  function playWedgeDegree(degree) {
    var list = Model.wedgeChords(root.tonicIndex)
    if (degree < 1 || degree > list.length)
      return
    var chord = list[degree - 1]
    root.toneCursor = degree - 1
    root.preview(chord.index, chord.ring)
  }

  function isToneCursor(index, ringName) {
    if (!root.toneMode)
      return false
    var chord = Model.wedgeChordAt(root.tonicIndex, root.toneCursor)
    return chord && index === chord.index && ringName === chord.ring
  }

  function cellFill(index, ringName) {
    if (root.toneMode) {
      if (root.isToneCursor(index, ringName))
        return root.foreground
    } else if (index === root.tonicIndex) {
      return root.foreground
    }
    if (index === root.soundingIndex && root.soundingRing === ringName)
      return root.soundingFill
    if (index === ring.hoverIndex && ring.hoverRing === ringName)
      return root.hoverFill
    if (Model.inKeyWedge(index, root.tonicIndex))
      return root.wedgeFill
    return "transparent"
  }

  function preview(index, ringName) {
    var t = Model.triad(index, ringName)
    root.soundingIndex = index
    root.soundingRing = ringName
    soundingTimer.restart()
    root.chordPreviewed(index, ringName, t)
  }

  function onChordClicked(index, ringName) {
    if (!root.toneMode) {
      root.tonicPicked(index, ringName)
      return
    }
    var cursor = Model.wedgeChordIndex(root.tonicIndex, index, ringName)
    if (cursor >= 0)
      root.toneCursor = cursor
    root.preview(index, ringName)
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
    readonly property bool active: root.toneMode
      ? root.isToneCursor(sector, ringName)
      : sector === root.tonicIndex
    readonly property bool inWedge: Model.inKeyWedge(sector, root.tonicIndex)
    readonly property bool hovered: sector === ring.hoverIndex && ring.hoverRing === ringName
    readonly property bool sounding: sector === root.soundingIndex && root.soundingRing === ringName

    x: Model.polarX(ring.cx, labelRadius, Model.sectorMidDeg(sector)) - width / 2
    y: Model.polarY(ring.cy, labelRadius, Model.sectorMidDeg(sector)) - height / 2
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
      height: Math.max(Style.space(180), parent.height - Style.space(118))

      property int hoverIndex: -1
      property string hoverRing: ""
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
        return Model.hitTest(px, py, cx, cy, minorInnerR, minorOuterR, majorInnerR, majorOuterR)
      }

      function setHover(px, py) {
        var hit = pick(px, py)
        if (hit) {
          hoverIndex = hit.index
          hoverRing = hit.ring
        } else {
          hoverIndex = -1
          hoverRing = ""
        }
      }

      Repeater {
        model: 12
        delegate: AnnularWedge {
          required property int index
          readonly property bool inWedge: Model.inKeyWedge(index, root.tonicIndex)
          anchors.fill: parent
          cx: ring.cx
          cy: ring.cy
          rInner: ring.majorInnerR
          rOuter: ring.majorOuterR
          startDeg: Model.sectorStartDeg(index)
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
          readonly property bool inWedge: Model.inKeyWedge(index, root.tonicIndex)
          anchors.fill: parent
          cx: ring.cx
          cy: ring.cy
          rInner: ring.minorInnerR
          rOuter: ring.minorOuterR
          startDeg: Model.sectorStartDeg(index)
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
        startDeg: Model.wedgeStartDeg(root.tonicIndex)
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
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: ring.hoverIndex >= 0 ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPositionChanged: function(mouse) { ring.setHover(mouse.x, mouse.y) }
        onExited: {
          ring.hoverIndex = -1
          ring.hoverRing = ""
        }
        onClicked: function(mouse) {
          var hit = ring.pick(mouse.x, mouse.y)
          if (hit)
            root.onChordClicked(hit.index, hit.ring)
        }
      }
    }

    Text {
      width: parent.width
      text: "I " + chords.I + "  IV " + chords.IV + "  V " + chords.V + "  vi " + chords.vi
      color: root.foreground
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.body
      horizontalAlignment: Text.AlignHCenter
    }

    Row {
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: Style.space(8)

      Button {
        text: root.toneMode ? "Tone on" : "Tone"
        selected: root.toneMode
        bordered: true
        foreground: root.foreground
        fontFamily: Style.font.menuFamily
        fontSize: Style.font.bodySmall
        tooltipText: root.toneMode
          ? "Clicks play chords in the key. Click again to pick a key."
          : "Play clicked triads without changing key"
        onClicked: root.toneMode = !root.toneMode
      }

      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: root.toneMode ? "1–6 play degrees  T toggle" : "click a key  T tone"
        color: root.dim
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.caption
      }
    }
  }
}
