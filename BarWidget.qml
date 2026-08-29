import QtQuick
import qs.Ui

BarWidget {
  id: root
  moduleName: "markschellhas.songwriter"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf001"
    tooltipText: "Open Songwriter"
    onPressed: function(mouseButton) {
      if (!root.bar || mouseButton !== Qt.LeftButton)
        return
      root.bar.run("omarchy-shell shell toggle markschellhas.songwriter")
    }
  }
}
