import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui
import "js/Status.js" as Status

BarWidget {
  id: root
  moduleName: "markschellhas.songwriter"

  // The overlay is keepLoaded, so its transport keeps sounding after the panel
  // is closed. The two components share no object graph, so the transport state
  // arrives as a small JSON file the overlay rewrites on every change.
  readonly property string statusPath: Quickshell.env("XDG_RUNTIME_DIR")
    + "/omarchy-songwriter/status.json"
  property bool playing: false
  property bool panelOpen: false
  property string songTitle: ""
  // A watcher cannot attach to a file that is not there yet, and the overlay
  // writes the first one asynchronously at shell startup.
  property bool statusMissing: true

  function applyStatus(raw) {
    var state = Status.parseStatus(raw)
    root.playing = state.playing
    root.panelOpen = state.panelOpen
    root.songTitle = state.title
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  FileView {
    id: statusView
    path: root.statusPath
    preload: true
    watchChanges: true
    printErrors: false
    onLoaded: {
      root.statusMissing = false
      root.applyStatus(text())
    }
    onLoadFailed: {
      root.statusMissing = true
      root.applyStatus("")
    }
    onFileChanged: reload()
  }

  Timer {
    id: statusWait
    interval: 750
    repeat: true
    running: root.statusMissing
    onTriggered: statusView.reload()
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf001"
    active: root.playing
    tooltipText: Status.tooltipText(root.playing, root.songTitle, root.panelOpen)
    onPressed: function(mouseButton) {
      if (!root.bar)
        return
      if (mouseButton === Qt.RightButton) {
        if (root.playing)
          root.bar.run("omarchy-shell shell call markschellhas.songwriter stopPlayback ''")
        return
      }
      if (mouseButton !== Qt.LeftButton)
        return
      root.bar.run("omarchy-shell shell toggle markschellhas.songwriter")
    }
  }
}
