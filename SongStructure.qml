import QtQuick
import qs.Commons
import qs.Ui
import "js/Model.js" as Model

Item {
  id: root

  property color foreground
  property color dim
  property color faint
  property var sections: []
  property int selectedSection: 0
  property int selectedMeasure: 0
  property int selectedSlot: 0
  property int playSection: -1
  property int playMeasure: -1
  property int playSlot: -1
  property bool playing: false
  property int playScopeSection: -1
  property int fillSection: -1
  property int fillMeasure: -1
  property int fillSlot: -1
  property real slotFillProgress: 0
  property string chordDragPayload: ""
  property var internalDragSource: null

  readonly property int barsPerRow: 4
  readonly property int slotHeight: Style.space(40)
  readonly property int repeatWidth: Style.space(36)
  readonly property int measureGap: Style.space(6)
  readonly property bool renaming: renamingSection >= 0

  property int renamingSection: -1
  property string menuKind: ""
  property int menuSection: -1
  property real menuX: 0
  property real menuY: 0
  property Item menuLayer: root
  property var menuAnchor: null

  signal chordDropped(int sectionIndex, int measureIndex, int slotIndex, var chord, bool insertAfter)
  signal chordMoved(int fromSection, int fromMeasure, int fromSlot, int toSection, int toMeasure, int toSlot, bool insertAfter)
  signal slotResized(int sectionIndex, int measureIndex, int slotIndex, int newSpan, string edge)
  signal slotCleared(int sectionIndex, int measureIndex, int slotIndex)
  signal slotAuditioned(int sectionIndex, int measureIndex, int slotIndex)
  signal sectionAdded(string name)
  signal sectionRemoved(int sectionIndex)
  signal sectionRenamed(int sectionIndex, string name)
  signal timeSignatureChanged(int sectionIndex, int numerator, int denominator)
  signal rowRepeatToggled(int sectionIndex, int rowIndex, bool shouldRepeat)
  signal slotSelected(int sectionIndex, int measureIndex, int slotIndex)
  signal sectionPlayToggled(int sectionIndex)

  readonly property var appendChoices: [
    { label: "Verse", name: "Verse" },
    { label: "Chorus", name: "Chorus" },
    { label: "Pre-Chorus", name: "Pre-Chorus" },
    { label: "Bridge", name: "Bridge" },
    { label: "Intro", name: "Intro" },
    { label: "Outro", name: "Outro" },
    { label: "Solo", name: "Solo" },
    { label: "Custom", name: "" }
  ]

  readonly property var meterChoices: [
    { label: "4/4 (4 bars)", numerator: 4, denominator: 4 },
    { label: "3/4 (3 bars)", numerator: 3, denominator: 4 },
    { label: "2/4 (2 bars)", numerator: 2, denominator: 4 },
    { label: "6/8 (6 bars)", numerator: 6, denominator: 8 }
  ]

  function cancelRename() {
    renamingSection = -1
  }

  function beginRename(sectionIndex) {
    closeMenu()
    renamingSection = sectionIndex
  }

  function commitRename(sectionIndex, name) {
    if (renamingSection !== sectionIndex)
      return
    var value = String(name || "").trim()
    renamingSection = -1
    var current = root.sections[sectionIndex]
    if (current && value === current.name)
      return
    root.sectionRenamed(sectionIndex, value)
  }

  function closeMenu() {
    menuKind = ""
    menuSection = -1
    menuAnchor = null
  }

  function openMenu(kind, sectionIndex, anchor) {
    menuKind = kind
    menuSection = sectionIndex
    menuAnchor = anchor
    positionMenu()
  }

  function positionMenu() {
    var layer = root.menuLayer ? root.menuLayer : root
    var anchor = root.menuAnchor
    if (!anchor)
      return
    var gap = Style.space(4)
    var menuW = Style.space(180)
    var menuH = menuPanel.height
    var below = anchor.mapToItem(layer, 0, anchor.height + gap)
    menuX = Math.max(0, Math.min(below.x, Math.max(0, layer.width - menuW)))
    var y = below.y
    if (y + menuH > layer.height)
      y = layer.height - menuH
    if (y < 0)
      y = 0
    menuY = y
  }

  function rowCount(measureCount) {
    if (measureCount <= 0)
      return 0
    return Math.floor((measureCount + root.barsPerRow - 1) / root.barsPerRow)
  }

  function slotLabel(chord) {
    if (!chord)
      return ""
    return Model.chordName(chord.rootPc, chord.quality)
  }

  function decodeDrop(drop) {
    var payload = ""
    if (drop && typeof drop.text === "string" && drop.text)
      payload = drop.text
    if (!payload)
      payload = root.chordDragPayload
    return Model.decodeChord(payload)
  }

  function beginSlotChordDrag(sectionIndex, measureIndex, slotIndex, chord) {
    if (!chord)
      return ""
    var payload = Model.encodeChord(chord)
    root.chordDragPayload = payload
    root.internalDragSource = {
      section: sectionIndex,
      measure: measureIndex,
      slot: slotIndex
    }
    return payload
  }

  function clearSlotChordDrag() {
    root.internalDragSource = null
  }

  function spanFromResizeX(slots, slotIndex, fromLeft, x, width) {
    if (!slots || slotIndex < 0 || slotIndex >= slots.length)
      return 1
    var start = 0
    var i
    for (i = 0; i < slotIndex; i++)
      start += Math.max(1, Number(slots[i].span) || 1)
    var span = Math.max(1, Number(slots[slotIndex].span) || 1)
    var capacity = 0
    for (i = 0; i < slots.length; i++)
      capacity += Math.max(1, Number(slots[i].span) || 1)
    if (capacity < 1)
      capacity = 1
    var unit = Math.round(x / Math.max(1, width) * capacity)
    if (unit < 0)
      unit = 0
    if (unit > capacity)
      unit = capacity
    var next = fromLeft ? (start + span) - unit : unit - start
    if (next < 1)
      next = 1
    return next
  }

  function pickMenu(item) {
    var kind = root.menuKind
    var sectionIndex = root.menuSection
    root.closeMenu()
    if (!item)
      return
    if (item.kind === "add")
      root.sectionAdded(item.name)
    else if (item.kind === "meter")
      root.timeSignatureChanged(sectionIndex, item.numerator, item.denominator)
    else if (item.kind === "rename")
      root.beginRename(sectionIndex)
    else if (item.kind === "delete" && root.sections.length > 1)
      root.sectionRemoved(sectionIndex)
  }

  function menuItems() {
    var items = []
    var i
    if (root.menuKind === "append") {
      for (i = 0; i < root.appendChoices.length; i++) {
        items.push({
          kind: "add",
          label: root.appendChoices[i].label,
          name: root.appendChoices[i].name,
          selected: false,
          enabled: true
        })
      }
      return items
    }
    if (root.menuKind === "more") {
      var section = root.sections[root.menuSection]
      var ts = section && section.timeSig ? section.timeSig : {}
      for (i = 0; i < root.meterChoices.length; i++) {
        var meter = root.meterChoices[i]
        items.push({
          kind: "meter",
          label: meter.label,
          numerator: meter.numerator,
          denominator: meter.denominator,
          selected: ts.numerator === meter.numerator && ts.denominator === meter.denominator,
          enabled: true
        })
      }
      items.push({ kind: "rename", label: "Rename", selected: false, enabled: true })
      items.push({
        kind: "delete",
        label: "Delete section",
        selected: false,
        enabled: root.sections.length > 1
      })
    }
    return items
  }

  Flickable {
    id: scroller
    anchors.fill: parent
    clip: true
    contentWidth: width
    contentHeight: list.implicitHeight
    boundsBehavior: Flickable.StopAtBounds

    Column {
      id: list
      width: scroller.width
      spacing: Style.space(10)

      Repeater {
        model: root.sections

        delegate: Column {
          id: sectionCol
          required property var modelData
          required property int index
          readonly property var section: modelData
          readonly property int sectionIndex: index
          readonly property var measures: section && section.measures ? section.measures : []
          readonly property var rowRepeats: section && section.rowRepeats ? section.rowRepeats : []
          readonly property int rows: root.rowCount(measures.length)
          width: list.width
          spacing: Style.space(6)

          Row {
            width: parent.width
            spacing: Style.spacing.sm

            Button {
              id: moreButton
              text: "···"
              bordered: true
              foreground: root.foreground
              tooltipText: "Section options"
              onClicked: root.openMenu("more", sectionCol.sectionIndex, moreButton)
            }

            Button {
              id: playButton
              iconText: root.playing && root.playScopeSection === sectionCol.sectionIndex ? "\uf04d" : "\uf04b"
              bordered: true
              selected: root.playing && root.playScopeSection === sectionCol.sectionIndex
              foreground: root.foreground
              accent: Color.accent
              tooltipText: root.playing && root.playScopeSection === sectionCol.sectionIndex
                ? "Stop section"
                : "Play section"
              onClicked: root.sectionPlayToggled(sectionCol.sectionIndex)
            }

            Item {
              width: Math.min(Style.space(180), parent.width * 0.4)
              height: Style.space(28)

              Text {
                visible: root.renamingSection !== sectionCol.sectionIndex
                anchors.fill: parent
                text: sectionCol.section && sectionCol.section.name ? sectionCol.section.name : "Section"
                color: root.foreground
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.subtitle
                font.bold: true
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight

                MouseArea {
                  anchors.fill: parent
                  onDoubleClicked: root.beginRename(sectionCol.sectionIndex)
                }
              }

              TextInput {
                id: nameInput
                visible: root.renamingSection === sectionCol.sectionIndex
                anchors.fill: parent
                text: sectionCol.section && sectionCol.section.name ? sectionCol.section.name : ""
                color: root.foreground
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.subtitle
                font.bold: true
                selectByMouse: true
                onVisibleChanged: {
                  if (visible) {
                    text = sectionCol.section && sectionCol.section.name ? sectionCol.section.name : ""
                    forceActiveFocus()
                    selectAll()
                  }
                }
                onEditingFinished: root.commitRename(sectionCol.sectionIndex, text)
                Keys.onEscapePressed: root.cancelRename()
              }
            }
          }

          Repeater {
            model: sectionCol.rows

            delegate: Item {
              id: barRow
              required property int index
              readonly property int rowIndex: index
              readonly property int rowStart: rowIndex * root.barsPerRow
              readonly property int rowEnd: Math.min(rowStart + root.barsPerRow, sectionCol.measures.length)
              readonly property int boxW: {
                var usable = width - root.repeatWidth - root.measureGap * root.barsPerRow
                return Math.max(Style.space(56), Math.floor(usable / root.barsPerRow))
              }
              width: list.width
              height: root.slotHeight

              Repeater {
                model: barRow.rowEnd - barRow.rowStart

                delegate: Rectangle {
                  id: measureBox
                  required property int index
                  readonly property int measureIndex: barRow.rowStart + index
                  readonly property var measure: sectionCol.measures[measureIndex]
                  readonly property var slots: measure && measure.slots ? measure.slots : []
                  readonly property int capacity: {
                    var ts = sectionCol.section && sectionCol.section.timeSig
                    var n = ts ? Number(ts.numerator) : 4
                    return n < 1 ? 1 : n
                  }
                  x: index * (barRow.boxW + root.measureGap)
                  width: barRow.boxW
                  height: root.slotHeight
                  radius: Math.max(2, Style.cornerRadius / 2)
                  color: "transparent"
                  border.width: 1
                  border.color: root.faint

                  function slotX(slotIndex) {
                    var acc = 0
                    var i
                    for (i = 0; i < slotIndex && i < slots.length; i++)
                      acc += Math.max(1, Number(slots[i].span) || 1)
                    return Math.floor(acc * width / Math.max(1, capacity))
                  }

                  function slotW(slotIndex) {
                    if (slotIndex < 0 || slotIndex >= slots.length)
                      return Style.space(8)
                    var start = slotX(slotIndex)
                    var next = slotIndex === slots.length - 1
                      ? width
                      : slotX(slotIndex + 1)
                    return Math.max(Style.space(8), next - start)
                  }

                  Repeater {
                    model: measureBox.slots

                    delegate: Item {
                      id: slotBox
                      required property var modelData
                      required property int index
                      readonly property var slot: modelData
                      readonly property int slotIndex: index
                      readonly property var chord: slot && slot.chord ? slot.chord : null
                      readonly property int span: Math.max(1, Number(slot && slot.span) || 1)
                      readonly property bool selected: root.selectedSection === sectionCol.sectionIndex
                        && root.selectedMeasure === measureBox.measureIndex
                        && root.selectedSlot === slotIndex
                      readonly property bool playing: root.playSection === sectionCol.sectionIndex
                        && root.playMeasure === measureBox.measureIndex
                        && root.playSlot === slotIndex
                      readonly property bool filling: root.fillSection === sectionCol.sectionIndex
                        && root.fillMeasure === measureBox.measureIndex
                        && root.fillSlot === slotIndex
                      x: measureBox.slotX(slotIndex)
                      y: 0
                      width: measureBox.slotW(slotIndex)
                      height: measureBox.height
                      opacity: slotMouse.dragging ? 0.45 : 1

                      Rectangle {
                        id: slotChip
                        anchors.fill: parent
                        anchors.margins: 2
                        radius: Math.max(2, Style.cornerRadius / 2)
                        color: slotBox.playing
                          ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.28)
                          : dropArea.containsDrag
                            ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.16)
                            : slotBox.selected
                              ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.12)
                              : "transparent"
                        border.width: 1
                        border.color: slotBox.playing ? Color.accent
                                    : slotBox.selected || dropArea.containsDrag ? root.foreground
                                    : root.faint
                        clip: true

                        Rectangle {
                          anchors.left: parent.left
                          anchors.top: parent.top
                          anchors.bottom: parent.bottom
                          width: Math.max(0, parent.width * root.slotFillProgress)
                          radius: parent.radius
                          visible: slotBox.filling && root.slotFillProgress > 0
                          color: slotBox.chord
                            ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.42)
                            : Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.18)
                        }

                        Text {
                          anchors.centerIn: parent
                          width: parent.width - Style.space(16)
                          text: root.slotLabel(slotBox.chord)
                          color: slotBox.chord ? root.foreground : root.dim
                          font.family: Style.font.menuFamily
                          font.pixelSize: Style.font.body
                          font.bold: !!slotBox.chord
                          horizontalAlignment: Text.AlignHCenter
                          elide: Text.ElideRight
                        }

                        Rectangle {
                          visible: slotMouse.containsMouse && !!slotBox.chord && !slotMouse.pendingClear
                          width: 3
                          height: Math.max(Style.space(8), parent.height - Style.space(16))
                          radius: 1
                          x: 0
                          anchors.verticalCenter: parent.verticalCenter
                          color: Color.accent
                          opacity: 0.65
                        }

                        Rectangle {
                          visible: slotMouse.containsMouse && !!slotBox.chord && !slotMouse.pendingClear
                          width: 3
                          height: Math.max(Style.space(8), parent.height - Style.space(16))
                          radius: 1
                          anchors.right: parent.right
                          anchors.verticalCenter: parent.verticalCenter
                          color: Color.accent
                          opacity: 0.65
                        }

                        Text {
                          visible: slotMouse.containsMouse && !!slotBox.chord
                          anchors.top: parent.top
                          anchors.right: parent.right
                          anchors.margins: 2
                          text: "×"
                          color: root.dim
                          font.family: Style.font.menuFamily
                          font.pixelSize: Style.font.caption
                        }
                      }

                      DropArea {
                        id: dropArea
                        anchors.fill: parent
                        keys: ["text/plain"]
                        onEntered: function(drag) {
                          if (drag.hasText)
                            drag.acceptProposedAction()
                        }
                        onDropped: function(drop) {
                          var chord = root.decodeDrop(drop)
                          if (!chord)
                            return
                          drop.acceptProposedAction()
                          var insertAfter = drop.x >= slotBox.width * 0.5
                          var source = root.internalDragSource
                          if (source) {
                            root.chordMoved(
                              source.section,
                              source.measure,
                              source.slot,
                              sectionCol.sectionIndex,
                              measureBox.measureIndex,
                              slotBox.slotIndex,
                              insertAfter
                            )
                            root.clearSlotChordDrag()
                            return
                          }
                          root.chordDropped(
                            sectionCol.sectionIndex,
                            measureBox.measureIndex,
                            slotBox.slotIndex,
                            chord,
                            insertAfter
                          )
                        }
                      }

                      MouseArea {
                        id: slotMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton
                        preventStealing: true
                        Drag.active: dragging
                        Drag.dragType: Drag.Automatic
                        Drag.proposedAction: Qt.MoveAction
                        Drag.keys: ["text/plain"]
                        cursorShape: {
                          if (!slotBox.chord)
                            return Qt.ArrowCursor
                          if (clearHit(mouseX, mouseY))
                            return Qt.ArrowCursor
                          var edge = edgeAt(mouseX)
                          if (edge)
                            return Qt.SizeHorCursor
                          return Qt.DragMoveCursor
                        }

                        property bool pendingClear: false
                        property bool resizing: false
                        property bool dragging: false
                        property string pressEdge: ""
                        property real pressX: 0
                        property real pressY: 0

                        function edgeAt(px) {
                          if (!slotBox.chord || width < 16)
                            return ""
                          var grip = Math.max(12, width * 0.33)
                          if (px <= grip)
                            return "left"
                          if (px >= width - grip)
                            return "right"
                          return ""
                        }

                        function clearHit(px, py) {
                          return !!slotBox.chord && px >= width - 16 && py <= 16
                        }

                        onPressed: function(mouse) {
                          pressX = mouse.x
                          pressY = mouse.y
                          pendingClear = clearHit(mouse.x, mouse.y)
                          pressEdge = pendingClear ? "" : edgeAt(mouse.x)
                          resizing = false
                          root.slotSelected(sectionCol.sectionIndex, measureBox.measureIndex, slotBox.slotIndex)
                        }

                        onPositionChanged: function(mouse) {
                          if (pressed && slotBox.chord && !resizing && !pendingClear && !pressEdge && !dragging) {
                            var ddx = mouse.x - pressX
                            var ddy = mouse.y - pressY
                            if (ddx * ddx + ddy * ddy >= 64) {
                              var payload = root.beginSlotChordDrag(
                                sectionCol.sectionIndex,
                                measureBox.measureIndex,
                                slotBox.slotIndex,
                                slotBox.chord
                              )
                              if (payload) {
                                slotMouse.Drag.mimeData = { "text/plain": payload }
                                dragging = true
                              }
                            }
                          }
                          if (!pressed || resizing || pendingClear || !pressEdge)
                            return
                          var dx = mouse.x - pressX
                          var dy = mouse.y - pressY
                          if (dx * dx + dy * dy >= 4)
                            resizing = true
                        }

                        onReleased: function(mouse) {
                          if (dragging) {
                            if (root.internalDragSource
                                && root.internalDragSource.section === sectionCol.sectionIndex
                                && root.internalDragSource.measure === measureBox.measureIndex
                                && root.internalDragSource.slot === slotBox.slotIndex)
                              root.clearSlotChordDrag()
                            dragging = false
                            return
                          }
                          if (pendingClear && clearHit(mouse.x, mouse.y)) {
                            root.slotCleared(sectionCol.sectionIndex, measureBox.measureIndex, slotBox.slotIndex)
                          } else if (resizing && pressEdge) {
                            var x = mapToItem(measureBox, mouse.x, 0).x
                            var next = root.spanFromResizeX(
                              measureBox.slots,
                              slotBox.slotIndex,
                              pressEdge === "left",
                              x,
                              measureBox.width
                            )
                            if (next !== slotBox.span)
                              root.slotResized(
                                sectionCol.sectionIndex,
                                measureBox.measureIndex,
                                slotBox.slotIndex,
                                next,
                                pressEdge
                              )
                          } else if (slotBox.chord) {
                            root.slotSelected(sectionCol.sectionIndex, measureBox.measureIndex, slotBox.slotIndex)
                            root.slotAuditioned(sectionCol.sectionIndex, measureBox.measureIndex, slotBox.slotIndex)
                          }
                          pendingClear = false
                          resizing = false
                          pressEdge = ""
                        }
                      }
                    }
                  }
                }
              }

              Button {
                id: repeatButton
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: root.repeatWidth
                text: ":||"
                bordered: true
                selected: !!(sectionCol.rowRepeats[barRow.rowIndex])
                foreground: root.foreground
                tooltipText: "Repeat this row once"
                onClicked: root.rowRepeatToggled(
                  sectionCol.sectionIndex,
                  barRow.rowIndex,
                  !sectionCol.rowRepeats[barRow.rowIndex]
                )
              }
            }
          }
        }
      }

      Button {
        id: addButton
        text: "Add section"
        bordered: true
        foreground: root.foreground
        tooltipText: "Append a section"
        onClicked: root.openMenu("append", -1, addButton)
      }
    }
  }

  MouseArea {
    parent: root.menuLayer
    visible: root.menuKind !== ""
    anchors.fill: parent
    z: 1000
    onClicked: root.closeMenu()
  }

  Rectangle {
    id: menuPanel
    parent: root.menuLayer
    visible: root.menuKind !== ""
    x: root.menuX
    y: root.menuY
    z: 1001
    width: Style.space(180)
    height: menuCol.implicitHeight + Style.spacing.sm * 2
    radius: Style.cornerRadius
    color: Color.menu.background
    border.width: 1
    border.color: Color.menu.border
    onHeightChanged: if (root.menuKind !== "") root.positionMenu()

    Column {
      id: menuCol
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.top: parent.top
      anchors.margins: Style.spacing.sm
      spacing: Style.space(4)

      Repeater {
        model: root.menuKind !== "" ? root.menuItems() : []

        delegate: Button {
          required property var modelData
          width: parent.width
          text: modelData.label
          bordered: true
          selected: !!modelData.selected
          enabled: modelData.enabled !== false
          foreground: root.foreground
          onClicked: root.pickMenu(modelData)
        }
      }
    }
  }
}
