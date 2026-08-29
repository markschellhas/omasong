import QtQuick
import qs.Commons
import qs.Ui
import "js/Chords.js" as Chords

Item {
  id: root

  property color foreground
  property color dim
  property color faint
  property var sections: []
  property int selectedSection: 0
  property int selectedSlot: 0
  property int playSection: -1
  property int playSlot: -1

  signal chordEdited(int sectionIndex, int slot, string symbol)
  signal chordPreviewed(string symbol)
  signal sectionAdded
  signal sectionRemoved(int sectionIndex)
  signal sectionRenamed(int sectionIndex, string name)
  signal slotSelected(int sectionIndex, int slot)

  property int editingSection: -1
  property int editingSlot: -1
  property bool renaming: false

  function beginEdit(sectionIndex, slot, current) {
    editingSection = sectionIndex
    editingSlot = slot
    chordField.text = current || ""
    chordField.forceActiveFocus()
    chordField.selectAll()
  }

  function commitEdit() {
    if (editingSection < 0)
      return
    var value = chordField.text.trim()
    if (value && !Chords.isValidChord(value)) {
      chordField.color = "#f87171"
      return
    }
    root.chordEdited(editingSection, editingSlot, value)
    cancelEdit()
  }

  function cancelEdit() {
    editingSection = -1
    editingSlot = -1
    chordField.color = root.foreground
  }

  function suggestions() {
    return Chords.getChordSuggestions(chordField.text)
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
          width: list.width
          spacing: Style.space(6)

          Row {
            width: parent.width
            spacing: Style.spacing.sm

            TextInput {
              id: nameInput
              width: Math.min(Style.space(180), parent.width * 0.35)
              text: sectionCol.modelData.name
              color: root.foreground
              font.family: Style.font.menuFamily
              font.pixelSize: Style.font.subtitle
              font.bold: true
              selectByMouse: true
              onEditingFinished: {
                if (text.trim() && text.trim() !== sectionCol.modelData.name)
                  root.sectionRenamed(sectionCol.index, text.trim())
              }
            }

            Text {
              anchors.verticalCenter: parent.verticalCenter
              text: (sectionCol.modelData.chords || []).filter(function(s) { return s && s.trim() }).length + " chords"
              color: root.dim
              font.family: Style.font.menuFamily
              font.pixelSize: Style.font.caption
            }

            Item { width: Style.spacing.md; height: 1 }

            Button {
              visible: root.sections.length > 1
              text: "Remove"
              bordered: true
              foreground: root.foreground
              tooltipText: "Remove this section"
              onClicked: root.sectionRemoved(sectionCol.index)
            }
          }

          Flow {
            width: parent.width
            spacing: Style.space(6)

            Repeater {
              model: sectionCol.modelData.chords

              delegate: Rectangle {
                id: cell
                required property var modelData
                required property int index
                readonly property bool selected: root.selectedSection === sectionCol.index && root.selectedSlot === index
                readonly property bool playing: root.playSection === sectionCol.index && root.playSlot === index
                readonly property bool editing: root.editingSection === sectionCol.index && root.editingSlot === index
                width: Style.space(72)
                height: Style.space(40)
                radius: Math.max(2, Style.cornerRadius / 2)
                color: playing ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.28)
                     : selected ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.12)
                     : "transparent"
                border.width: 1
                border.color: playing ? Color.accent
                            : selected ? root.foreground
                            : root.faint

                Text {
                  visible: !cell.editing
                  anchors.centerIn: parent
                  width: parent.width - 6
                  text: cell.modelData && String(cell.modelData).trim() ? cell.modelData : "·"
                  color: cell.modelData && String(cell.modelData).trim() ? root.foreground : root.dim
                  font.family: Style.font.menuFamily
                  font.pixelSize: Style.font.body
                  font.bold: !!cell.modelData
                  horizontalAlignment: Text.AlignHCenter
                  elide: Text.ElideRight
                }

                MouseArea {
                  anchors.fill: parent
                  acceptedButtons: Qt.LeftButton | Qt.RightButton
                  onClicked: function(mouse) {
                    root.slotSelected(sectionCol.index, cell.index)
                    if (mouse.button === Qt.RightButton && cell.modelData) {
                      root.chordPreviewed(cell.modelData)
                      return
                    }
                    if (mouse.button === Qt.LeftButton)
                      root.beginEdit(sectionCol.index, cell.index, cell.modelData)
                  }
                  onDoubleClicked: {
                    if (cell.modelData)
                      root.chordPreviewed(cell.modelData)
                  }
                }
              }
            }
          }
        }
      }

      Button {
        text: "Add section"
        bordered: true
        foreground: root.foreground
        onClicked: root.sectionAdded()
      }
    }
  }

  Rectangle {
    visible: root.editingSection >= 0
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    width: Math.min(parent.width, Style.space(360))
    height: editorCol.implicitHeight + Style.spacing.md * 2
    radius: Style.cornerRadius
    color: Color.menu.background
    border.width: 1
    border.color: Color.menu.border
    z: 4

    Column {
      id: editorCol
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.top: parent.top
      anchors.margins: Style.spacing.md
      spacing: Style.space(8)

      Text {
        text: "Chord · measure " + (root.editingSlot + 1)
        color: root.dim
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.caption
      }

      TextInput {
        id: chordField
        width: parent.width
        color: root.foreground
        font.family: Style.font.menuFamily
        font.pixelSize: Style.font.heading
        selectByMouse: true
        Keys.onReturnPressed: root.commitEdit()
        Keys.onEnterPressed: root.commitEdit()
        Keys.onEscapePressed: root.cancelEdit()
      }

      Flow {
        width: parent.width
        spacing: Style.space(6)
        Repeater {
          model: root.editingSection >= 0 ? Chords.getChordSuggestions(chordField.text) : []
          delegate: Button {
            required property var modelData
            text: modelData
            bordered: true
            foreground: root.foreground
            onClicked: {
              chordField.text = modelData
              root.commitEdit()
            }
          }
        }
      }

      Row {
        spacing: Style.spacing.sm
        Button {
          text: "Save"
          foreground: root.foreground
          accent: Color.accent
          onClicked: root.commitEdit()
        }
        Button {
          text: "Cancel"
          bordered: true
          foreground: root.foreground
          onClicked: root.cancelEdit()
        }
        Button {
          text: "Clear"
          bordered: true
          foreground: root.foreground
          onClicked: {
            chordField.text = ""
            root.commitEdit()
          }
        }
      }
    }
  }
}
