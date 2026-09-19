import QtQuick
import qs.Commons

// Circle-with-label preview grabbed as the native drag icon while a chord is
// dragged from the palette. Kept off-canvas; only its grabToImage() output
// is ever shown, as the cursor's drag image, so it never paints on screen
// itself.
Item {
  id: root

  property string label: ""
  readonly property int diameter: Style.space(48)

  width: diameter
  height: diameter

  Rectangle {
    anchors.fill: parent
    radius: width / 2
    antialiasing: true
    color: Color.accent
    border.width: Math.max(1, Style.normalBorderWidth)
    border.color: Qt.rgba(0, 0, 0, 0.25)
  }

  Text {
    anchors.centerIn: parent
    width: parent.width - Style.space(10)
    text: root.label
    color: Color.background
    font.family: Style.font.menuFamily
    font.pixelSize: Style.font.bodySmall
    font.bold: true
    horizontalAlignment: Text.AlignHCenter
    elide: Text.ElideRight
    maximumLineCount: 1
  }
}
