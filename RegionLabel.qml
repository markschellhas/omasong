import QtQuick
import qs.Commons

// A small serif caption naming one region of the card, so a first-time reader
// can tell the parts apart at a glance. Colour and height come from the host.
Text {
  text: ""
  textFormat: Text.PlainText
  font.family: "serif"
  font.pixelSize: Style.font.caption
  font.letterSpacing: 0.5
  verticalAlignment: Text.AlignVCenter
  elide: Text.ElideRight
}
