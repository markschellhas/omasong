import QtQuick
import qs.Commons
import qs.Ui

FocusScope {
  id: root

  property color foreground
  property color dim
  property color faint
  property string sectionName: "Section"
  property int measureIndex: 0
  property int stepCount: 16
  property var pattern: ({ kick: [], snare: [], hihat: [] })

  signal stepToggled(string lane, int step)
  signal clearRequested
  signal closeRequested

  readonly property var lanes: [
    { key: "kick", label: "Kick" },
    { key: "snare", label: "Snare" },
    { key: "hihat", label: "Hi-hat" }
  ]
  readonly property int panelPadding: Style.spacing.md
  readonly property int headerHeight: Style.space(38)
  readonly property int labelWidth: Style.space(68)
  readonly property int rowHeight: Style.space(34)
  readonly property int rowGap: Style.space(4)

  function activeAt(lane, step) {
    var values = root.pattern && root.pattern[lane]
    return !!(values && step >= 0 && step < values.length && values[step])
  }

  function focusPanel() {
    root.forceActiveFocus()
  }

  onVisibleChanged: {
    if (visible)
      Qt.callLater(root.focusPanel)
  }

  Keys.onEscapePressed: function(event) {
    root.closeRequested()
    event.accepted = true
  }

  MouseArea {
    anchors.fill: parent
    onClicked: root.closeRequested()
  }

  Rectangle {
    id: panel
    anchors.centerIn: parent
    width: Math.min(parent.width - Style.space(32), Style.space(920))
    height: root.panelPadding * 2
      + root.headerHeight
      + root.lanes.length * root.rowHeight
      + (root.lanes.length - 1) * root.rowGap
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
      height: root.headerHeight
      text: root.sectionName + " · Bar " + (root.measureIndex + 1)
      textFormat: Text.PlainText
      color: root.foreground
      font.family: Style.font.menuFamily
      font.pixelSize: Style.font.subtitle
      font.bold: true
      verticalAlignment: Text.AlignVCenter
      elide: Text.ElideRight
    }

    Row {
      id: actions
      anchors.right: parent.right
      anchors.rightMargin: root.panelPadding
      anchors.verticalCenter: contextLabel.verticalCenter
      spacing: Style.spacing.sm

      Button {
        text: "Clear"
        bordered: true
        focusable: true
        foreground: root.foreground
        accent: Color.accent
        tooltipText: "Clear beats in this bar"
        onClicked: root.clearRequested()
      }

      Button {
        text: "Close"
        focusable: true
        foreground: root.foreground
        accent: Color.accent
        tooltipText: "Close beat sequencer"
        onClicked: root.closeRequested()
      }
    }

    Repeater {
      model: root.lanes

      delegate: Item {
        id: laneRow
        required property var modelData
        required property int index
        readonly property string laneKey: modelData.key
        x: root.panelPadding
        y: root.panelPadding + root.headerHeight + index * (root.rowHeight + root.rowGap)
        width: panel.width - root.panelPadding * 2
        height: root.rowHeight

        Text {
          anchors.left: parent.left
          anchors.top: parent.top
          anchors.bottom: parent.bottom
          width: root.labelWidth
          text: laneRow.modelData.label
          textFormat: Text.PlainText
          color: root.foreground
          font.family: Style.font.menuFamily
          font.pixelSize: Style.font.body
          verticalAlignment: Text.AlignVCenter
          elide: Text.ElideRight
        }

        Item {
          id: stepArea
          anchors.left: parent.left
          anchors.leftMargin: root.labelWidth
          anchors.right: parent.right
          anchors.top: parent.top
          anchors.bottom: parent.bottom
          clip: true

          Repeater {
            model: Math.max(1, root.stepCount)

            delegate: Item {
              id: stepCell
              required property int index
              readonly property bool active: root.activeAt(laneRow.laneKey, index)
              x: index * stepArea.width / Math.max(1, root.stepCount)
              width: (index + 1) * stepArea.width / Math.max(1, root.stepCount) - x
              height: stepArea.height

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
                onClicked: root.stepToggled(laneRow.laneKey, stepCell.index)
              }
            }
          }
        }
      }
    }
  }
}
