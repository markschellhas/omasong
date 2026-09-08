pragma ComponentBehavior: Bound

import QtQuick
import qs.Commons
import qs.Ui
import "js/BeatUi.js" as BeatUi

FocusScope {
  id: root

  property color foreground
  property color dim
  property color faint
  property string sectionName: "Section"
  property int measureIndex: 0
  property int stepCount: 16
  property var pattern: ({ kick: [], snare: [], hihat: [] })
  property int focusIndex: 2

  signal stepToggled(string lane, int step)
  signal clearRequested
  signal closeRequested

  readonly property var lanes: [
    { key: "kick", label: "Kick" },
    { key: "snare", label: "Snare" },
    { key: "hihat", label: "Hi-hat" }
  ]
  readonly property int panelPadding: Style.spacing.md
  readonly property int headerHeight: Style.space(46)
  readonly property int labelWidth: Style.space(68)
  readonly property int rowHeight: Style.space(34)
  readonly property int rowGap: Style.space(4)
  readonly property int gridHeight: lanes.length * rowHeight + (lanes.length - 1) * rowGap
  readonly property real stepCellWidth: BeatUi.sequencerStepWidth(
    Math.max(1, panel.width - panelPadding * 2 - labelWidth),
    Math.max(1, stepCount),
    Style.space(24)
  )
  readonly property bool stepGridOverflowing: stepScroller.contentWidth > stepScroller.width + 0.5
  readonly property int scrollIndicatorHeight: stepGridOverflowing ? Style.space(7) : 0
  readonly property string focusDescription: descriptionForFocus(focusIndex)

  function activeAt(lane, step) {
    var values = root.pattern && root.pattern[lane]
    return !!(values && step >= 0 && step < values.length && values[step])
  }

  function descriptionForFocus(index) {
    if (index === 0)
      return "Clear all steps in this bar"
    if (index === 1)
      return "Close sequencer"
    var offset = index - 2
    var laneIndex = Math.floor(offset / Math.max(1, root.stepCount))
    var step = offset % Math.max(1, root.stepCount)
    if (laneIndex < 0 || laneIndex >= root.lanes.length)
      return "Beat sequencer"
    var lane = root.lanes[laneIndex]
    return lane.label + " · step " + (step + 1) + " of " + root.stepCount
      + (root.activeAt(lane.key, step) ? " · on" : " · off")
  }

  function focusControl(index) {
    var count = BeatUi.sequencerFocusCount(root.stepCount, root.lanes.length)
    var safe = Math.max(0, Math.min(count - 1, Number(index) || 0))
    root.focusIndex = safe
    if (safe === 0) {
      clearButton.forceActiveFocus()
      return
    }
    if (safe === 1) {
      closeButton.forceActiveFocus()
      return
    }
    var offset = safe - 2
    var laneIndex = Math.floor(offset / Math.max(1, root.stepCount))
    var step = offset % Math.max(1, root.stepCount)
    var laneItem = laneRepeater.itemAt(laneIndex)
    if (laneItem)
      laneItem.focusStep(step)
    else
      clearButton.forceActiveFocus()
  }

  function cycleFocus(delta) {
    focusControl(BeatUi.sequencerNextFocusIndex(
      root.focusIndex,
      delta,
      root.stepCount,
      root.lanes.length
    ))
  }

  function focusPanel() {
    // The first kick step is the primary action; Tab still reaches Close/Clear.
    focusControl(2)
  }

  onVisibleChanged: {
    if (visible)
      Qt.callLater(root.focusPanel)
  }

  Keys.priority: Keys.BeforeItem
  Keys.onPressed: function(event) {
    if (event.key === Qt.Key_Escape) {
      root.closeRequested()
      event.accepted = true
      return
    }
    if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
      var backwards = event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier)
      root.cycleFocus(backwards ? -1 : 1)
      event.accepted = true
      return
    }
    event.accepted = false
  }

  MouseArea {
    anchors.fill: parent
    onClicked: root.closeRequested()
  }

  Rectangle {
    id: panel
    anchors.centerIn: parent
    width: Math.min(parent.width - Style.space(32), Style.space(920))
    height: root.panelPadding * 2 + root.headerHeight + root.gridHeight + root.scrollIndicatorHeight
    radius: Style.cornerRadius
    color: Color.menu.background
    border.width: Math.max(1, Style.normalBorderWidth)
    border.color: Color.menu.border

    MouseArea {
      anchors.fill: parent
      onClicked: function(mouse) { mouse.accepted = true }
    }

    Text {
      id: contextLabel
      anchors.left: parent.left
      anchors.leftMargin: root.panelPadding
      anchors.right: actions.left
      anchors.rightMargin: Style.spacing.sm
      anchors.top: parent.top
      anchors.topMargin: root.panelPadding
      height: Style.space(22)
      text: root.sectionName + " · Bar " + (root.measureIndex + 1)
      textFormat: Text.PlainText
      color: root.foreground
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.subtitle
      font.bold: true
      verticalAlignment: Text.AlignVCenter
      elide: Text.ElideRight
    }

    Text {
      anchors.left: contextLabel.left
      anchors.right: contextLabel.right
      anchors.top: contextLabel.bottom
      height: root.headerHeight - contextLabel.height
      text: root.focusDescription
      textFormat: Text.PlainText
      color: root.dim
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.caption
      verticalAlignment: Text.AlignVCenter
      elide: Text.ElideRight
    }

    Row {
      id: actions
      anchors.right: parent.right
      anchors.rightMargin: root.panelPadding
      anchors.top: parent.top
      anchors.topMargin: root.panelPadding
      height: root.headerHeight
      spacing: Style.spacing.sm

      Button {
        id: clearButton
        anchors.verticalCenter: parent.verticalCenter
        text: "Clear"
        bordered: true
        focusable: true
        foreground: root.foreground
        accent: Color.accent
        tooltipText: "Clear beats in this bar"
        Accessible.name: "Clear all beats in " + root.sectionName + ", bar " + (root.measureIndex + 1)
        onActiveFocusChanged: if (activeFocus) root.focusIndex = 0
        onClicked: root.clearRequested()
      }

      Button {
        id: closeButton
        anchors.verticalCenter: parent.verticalCenter
        text: "Close"
        focusable: true
        foreground: root.foreground
        accent: Color.accent
        tooltipText: "Close beat sequencer"
        Accessible.name: "Close beat sequencer"
        onActiveFocusChanged: if (activeFocus) root.focusIndex = 1
        onClicked: root.closeRequested()
      }
    }

    Item {
      id: laneLabels
      x: root.panelPadding
      y: root.panelPadding + root.headerHeight
      width: root.labelWidth
      height: root.gridHeight

      Repeater {
        model: root.lanes

        delegate: Text {
          required property var modelData
          required property int index
          y: index * (root.rowHeight + root.rowGap)
          width: laneLabels.width
          height: root.rowHeight
          text: modelData.label
          textFormat: Text.PlainText
          color: root.foreground
          font.family: Style.font.menuFamily
          font.pixelSize: Style.font.body
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
        }
      }
    }

    Flickable {
      id: stepScroller
      anchors.left: parent.left
      anchors.leftMargin: root.panelPadding + root.labelWidth
      anchors.right: parent.right
      anchors.rightMargin: root.panelPadding
      anchors.top: parent.top
      anchors.topMargin: root.panelPadding + root.headerHeight
      height: root.gridHeight
      contentWidth: Math.max(width, Math.max(1, root.stepCount) * root.stepCellWidth)
      contentHeight: height
      flickableDirection: Flickable.HorizontalFlick
      boundsBehavior: Flickable.StopAtBounds
      interactive: root.stepGridOverflowing
      clip: true

      function revealStep(step) {
        var leftEdge = step * root.stepCellWidth
        var rightEdge = leftEdge + root.stepCellWidth
        if (leftEdge < contentX)
          contentX = leftEdge
        else if (rightEdge > contentX + width)
          contentX = Math.min(contentWidth - width, rightEdge - width)
      }

      Item {
        id: stepGrid
        width: stepScroller.contentWidth
        height: stepScroller.height

        Repeater {
          id: laneRepeater
          model: root.lanes

          delegate: Item {
            id: laneRow
            required property var modelData
            required property int index
            readonly property string laneKey: modelData.key
            y: index * (root.rowHeight + root.rowGap)
            width: stepGrid.width
            height: root.rowHeight

            function focusStep(step) {
              var cell = stepRepeater.itemAt(step)
              if (!cell)
                return
              cell.focusButton()
              stepScroller.revealStep(step)
            }

            Repeater {
              id: stepRepeater
              model: Math.max(1, root.stepCount)

              delegate: Item {
                id: stepCell
                required property int index
                readonly property bool active: root.activeAt(laneRow.laneKey, index)
                readonly property int controlIndex: 2
                  + laneRow.index * Math.max(1, root.stepCount) + index
                x: index * root.stepCellWidth
                width: root.stepCellWidth
                height: laneRow.height

                function focusButton() {
                  stepButton.forceActiveFocus()
                }

                Rectangle {
                  visible: stepCell.index % 4 === 0
                  anchors.left: parent.left
                  anchors.top: parent.top
                  anchors.bottom: parent.bottom
                  width: Math.max(1, Style.normalBorderWidth)
                  color: root.foreground
                  opacity: stepCell.index === 0 ? 0.7 : 0.46
                  z: 2
                }

                Button {
                  id: stepButton
                  anchors.fill: parent
                  anchors.leftMargin: Style.space(2)
                  anchors.rightMargin: Style.space(1)
                  anchors.topMargin: Style.space(3)
                  anchors.bottomMargin: Style.space(3)
                  text: ""
                  bordered: true
                  selected: stepCell.active
                  focusable: true
                  foreground: stepCell.active ? Color.accent : root.dim
                  accent: Color.accent
                  opacity: stepCell.active ? 1 : 0.72
                  tooltipText: laneRow.modelData.label + ", step " + (stepCell.index + 1)
                  Accessible.name: laneRow.modelData.label + " step " + (stepCell.index + 1)
                    + " of " + root.stepCount + (stepCell.active ? ", on" : ", off")
                  onActiveFocusChanged: {
                    if (activeFocus) {
                      root.focusIndex = stepCell.controlIndex
                      stepScroller.revealStep(stepCell.index)
                    }
                  }
                  onClicked: root.stepToggled(laneRow.laneKey, stepCell.index)
                }
              }
            }
          }
        }
      }
    }

    Rectangle {
      id: scrollTrack
      visible: root.stepGridOverflowing
      x: root.panelPadding + root.labelWidth
      y: root.panelPadding + root.headerHeight + root.gridHeight + Style.space(2)
      width: panel.width - root.panelPadding * 2 - root.labelWidth
      height: Style.space(2)
      radius: 1
      color: root.faint

      Rectangle {
        x: stepScroller.contentWidth > stepScroller.width
          ? stepScroller.contentX / (stepScroller.contentWidth - stepScroller.width)
            * (scrollTrack.width - width)
          : 0
        width: Math.max(Style.space(18), scrollTrack.width * stepScroller.width / stepScroller.contentWidth)
        height: parent.height
        radius: parent.radius
        color: root.foreground
        opacity: 0.48
      }
    }
  }
}
