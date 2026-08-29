import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui
import "js/Model.js" as Model
import "js/Chords.js" as Chords
import "js/Song.js" as Song
import "js/Keyboard.js" as KeyMap

Item {
  id: root

  property string omarchyPath: Quickshell.env("OMARCHY_PATH")
  property var shell: null
  property var manifest: null
  property bool opened: false

  property color background: Color.menu.background
  property color foreground: Color.menu.text
  property color border: Color.menu.border
  property color dim: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.56)
  property color faint: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12)

  property var song: Song.defaultSong()
  property bool playing: false
  property int playIndex: -1
  property int currentBar: 1
  property int currentBeat: 1
  property int selectedSection: 0
  property int selectedSlot: 0
  property var activeNotes: []
  property bool sustain: false
  property var heldNotes: ({})
  property var tapTimes: []
  property string statusText: ""
  property bool persistReady: false

  readonly property int cardWidth: Math.min(Style.space(1180), panel.width - Style.gapsOut * 2)
  readonly property int cardHeight: Math.min(Style.space(820), panel.height - Style.gapsOut * 2)
  readonly property int headerHeight: Style.space(52)
  readonly property int transportHeight: Style.space(44)
  readonly property int pianoHeight: Style.space(146)
  readonly property string playScript: decodeURIComponent(
    Qt.resolvedUrl("play-notes.py").toString().replace(/^file:\/\//, ""))
  readonly property string songPath: Quickshell.env("HOME") + "/.local/state/omarchy/songwriter/song.json"
  readonly property string writeScript: decodeURIComponent(
    Qt.resolvedUrl("write-json.py").toString().replace(/^file:\/\//, ""))
  readonly property var playSlots: Song.flattenSlots(song)

  function open(payloadJson) {
    opened = true
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function close() {
    stopPlayback()
    opened = false
  }

  function dismiss() {
    close()
    if (shell && typeof shell.hide === "function")
      shell.hide((manifest && manifest.id) || "io.github.markschellhas.songwriter")
  }

  function clampBpm(value) {
    var n = Math.round(Number(value))
    if (!isFinite(n)) return song.bpm
    return Math.max(40, Math.min(240, n))
  }

  function clampSelection() {
    var sections = (song && song.sections) ? song.sections : []
    if (!sections.length) {
      selectedSection = 0
      selectedSlot = 0
      return
    }
    if (selectedSection >= sections.length)
      selectedSection = sections.length - 1
    if (selectedSection < 0)
      selectedSection = 0
    var chords = sections[selectedSection].chords || []
    if (selectedSlot >= chords.length)
      selectedSlot = Math.max(0, chords.length - 1)
    if (selectedSlot < 0)
      selectedSlot = 0
  }

  function textFieldHasFocus() {
    var item = keyCatcher.activeFocusItem
    if (!item)
      return structure.editingSection >= 0
    return (item instanceof TextInput) || structure.editingSection >= 0
  }

  function refocusKeys() {
    if (textFieldHasFocus())
      return
    keyCatcher.forceActiveFocus()
  }

  function updateSong(next) {
    song = Song.normalizeSong(next)
    clampSelection()
    persistSoon()
  }

  function persistSoon() {
    if (!persistReady)
      return
    persistTimer.restart()
  }

  function persistNow() {
    if (!persistReady)
      return
    Quickshell.execDetached(["python3", writeScript, songPath, JSON.stringify(song)])
  }

  function playFreqs(freqs, seconds) {
    if (!freqs || !freqs.length)
      return
    var cmd = ["python3", playScript]
    for (var i = 0; i < freqs.length; i++)
      cmd.push(String(freqs[i]))
    if (seconds)
      cmd.push("--seconds", String(seconds))
    Quickshell.execDetached(cmd)
  }

  function playMidiNotes(notes, seconds) {
    if (!notes || !notes.length)
      return
    var cmd = ["python3", playScript, "--midi"]
    for (var i = 0; i < notes.length; i++)
      cmd.push(String(notes[i]))
    if (seconds)
      cmd.push("--seconds", String(seconds))
    Quickshell.execDetached(cmd)
    var next = activeNotes.slice()
    for (var n = 0; n < notes.length; n++) {
      if (next.indexOf(notes[n]) === -1)
        next.push(notes[n])
    }
    activeNotes = next
    noteClear.restart()
  }

  function previewSymbol(symbol) {
    var parsed = Chords.parseChord(symbol, song.octave)
    if (!parsed.isValid || !parsed.chord || !parsed.chord.notes.length)
      return
    statusText = parsed.chord.symbol
    playMidiNotes(parsed.chord.notes, 0.7)
  }

  function insertSymbol(symbol) {
    updateSong(Song.setChord(song, selectedSection, selectedSlot, symbol))
    previewSymbol(symbol)
  }

  function startPlayback() {
    var first = Song.nextFilledSlot(playSlots, 0)
    if (first < 0) {
      statusText = "Add chords to play"
      return
    }
    playing = true
    playIndex = first
    currentBar = 1
    currentBeat = 1
    playCurrent()
    transportTimer.start()
  }

  function stopPlayback() {
    playing = false
    playIndex = -1
    currentBeat = 1
    transportTimer.stop()
  }

  function playCurrent() {
    var slots = playSlots
    if (playIndex < 0 || playIndex >= slots.length) {
      if (song.loop) {
        playIndex = Song.nextFilledSlot(slots, 0)
        currentBar = 1
      }
      if (playIndex < 0 || playIndex >= slots.length) {
        stopPlayback()
        return
      }
    }
    var slot = slots[playIndex]
    if (!slot || !slot.symbol) {
      advanceSlot()
      return
    }
    selectedSection = slot.sectionIndex
    selectedSlot = slot.slot
    currentBar = playIndex + 1
    previewSymbol(slot.symbol)
    statusText = slot.sectionName + " · " + slot.symbol
  }

  function advanceSlot() {
    var slots = playSlots
    var next = Song.nextFilledSlot(slots, playIndex + 1)
    if (next < 0) {
      if (song.loop) {
        playIndex = Song.nextFilledSlot(slots, 0)
        currentBar = 1
        if (playIndex < 0) {
          stopPlayback()
          return
        }
        playCurrent()
      } else {
        stopPlayback()
      }
      return
    }
    playIndex = next
    playCurrent()
  }

  function handleComputerKey(event) {
    if (event.key === Qt.Key_Space) {
      sustain = true
      event.accepted = true
      return
    }
    if (event.key === Qt.Key_T && !(event.modifiers & Qt.ControlModifier)) {
      circle.toneMode = !circle.toneMode
      event.accepted = true
      return
    }
    if (circle.toneMode) {
      var degree = 0
      if (event.key >= Qt.Key_1 && event.key <= Qt.Key_6)
        degree = event.key - Qt.Key_1 + 1
      else if (event.text && event.text >= "1" && event.text <= "6")
        degree = parseInt(event.text, 10)
      if (degree > 0) {
        circle.playWedgeDegree(degree)
        event.accepted = true
        return
      }
    }
    var midi = KeyMap.midiForKey(event.text, song.octave, song.layout)
    if (midi < 0)
      return
    if (heldNotes[midi] || heldNotes[String(midi)])
      return
    var nextHeld = {}
    for (var held in heldNotes)
      nextHeld[held] = heldNotes[held]
    nextHeld[midi] = true
    heldNotes = nextHeld
    var next = activeNotes.slice()
    if (next.indexOf(midi) === -1)
      next.push(midi)
    activeNotes = next
    playMidiNotes([midi], 0.45)
    event.accepted = true
  }

  function handleComputerKeyUp(event) {
    if (event.key === Qt.Key_Space) {
      sustain = false
      var kept = []
      for (var i = 0; i < activeNotes.length; i++) {
        var n = activeNotes[i]
        if (heldNotes[n] || heldNotes[String(n)])
          kept.push(n)
      }
      activeNotes = kept
      event.accepted = true
      return
    }
    var midi = KeyMap.midiForKey(event.text, song.octave, song.layout)
    if (midi < 0)
      return
    var nextHeld = {}
    for (var held in heldNotes) {
      if (String(held) !== String(midi))
        nextHeld[held] = heldNotes[held]
    }
    heldNotes = nextHeld
    if (!sustain) {
      activeNotes = activeNotes.filter(function(n) { return n !== midi })
    }
    event.accepted = true
  }

  function tapTempo() {
    var now = Date.now()
    var times = tapTimes.filter(function(t) { return now - t < 3000 })
    times.push(now)
    tapTimes = times
    if (times.length < 2)
      return
    var sum = 0
    for (var i = 1; i < times.length; i++)
      sum += times[i] - times[i - 1]
    var bpm = Math.round(60000 / (sum / (times.length - 1)))
    updateSong(Song.mergeSong(song, { bpm: clampBpm(bpm) }))
  }

  Timer {
    id: persistTimer
    interval: 250
    onTriggered: persistNow()
  }

  Timer {
    id: noteClear
    interval: 700
    onTriggered: {
      if (root.sustain)
        return
      var kept = []
      for (var i = 0; i < root.activeNotes.length; i++) {
        var n = root.activeNotes[i]
        if (root.heldNotes[n] || root.heldNotes[String(n)])
          kept.push(n)
      }
      root.activeNotes = kept
    }
  }

  Timer {
    id: transportTimer
    interval: Math.max(200, Math.round(60000 / Math.max(40, song.bpm)))
    repeat: true
    onTriggered: {
      currentBeat = currentBeat >= 4 ? 1 : currentBeat + 1
      if (currentBeat === 1)
        advanceSlot()
    }
  }

  FileView {
    id: songFile
    path: root.songPath
    preload: true
    blockLoading: false
    printErrors: false
    onLoaded: {
      try {
        var raw = text()
        if (raw && String(raw).trim())
          song = Song.normalizeSong(JSON.parse(raw))
      } catch (e) {
        song = Song.defaultSong()
      }
      persistReady = true
      persistFallback.stop()
    }
    onLoadFailed: {
      persistReady = true
      persistFallback.stop()
    }
  }

  Timer {
    id: persistFallback
    interval: 2000
    running: true
    onTriggered: {
      if (!persistReady)
        persistReady = true
    }
  }

  Component.onCompleted: songFile.reload()

  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    mask: Region { item: card }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-songwriter"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened && cardHover.hovered
      ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      anchors.centerIn: parent
      color: root.background
      borderSpec: Border.surfaceSpec("menu", "border", root.border, Math.max(1, Style.normalBorderWidth))
      radius: Style.cornerRadius

      HoverHandler {
        id: cardHover
        onHoveredChanged: if (hovered) root.refocusKeys()
      }

      FocusScope {
        id: keyCatcher
        anchors.fill: parent
        focus: true

        Keys.priority: Keys.AfterItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) {
            if (structure.editingSection >= 0) {
              structure.cancelEdit()
              event.accepted = true
              return
            }
            root.dismiss()
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Left) {
            circle.step(-1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Right) {
            circle.step(1)
            event.accepted = true
            return
          }
          root.handleComputerKey(event)
        }
        Keys.onReleased: function(event) {
          root.handleComputerKeyUp(event)
        }

        Item {
          id: content
          anchors.fill: parent
          anchors.margins: Style.spacing.md

        readonly property int circleHeight: {
          var rest = height - root.headerHeight - root.transportHeight - root.pianoHeight
          return Math.min(Style.space(340), Math.max(Style.space(230), Math.floor(rest / 3)))
        }

        Item {
          id: header
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: parent.top
          height: root.headerHeight

          TextInput {
            id: title
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.rightMargin: Style.spacing.sm
            height: Style.space(30)
            color: root.foreground
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.heading
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            selectByMouse: true
            onEditingFinished: {
              var next = text.trim()
              if (next && next !== root.song.title)
                root.updateSong(Song.mergeSong(root.song, { title: next }))
            }
          }

          Binding {
            target: title
            property: "text"
            value: root.song.title
            when: !title.activeFocus
          }

          Text {
            anchors.top: title.bottom
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.rightMargin: Style.spacing.sm
            anchors.bottom: parent.bottom
            text: "Circle of fifths, song structure, and keyboard"
            textFormat: Text.PlainText
            color: root.dim
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.caption
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
          }

          Button {
            id: closeButton
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            iconText: "\uf00d"
            tooltipText: "Close"
            focusable: true
            foreground: root.foreground
            accent: Color.accent
            onClicked: root.dismiss()
          }
        }

        Transport {
          id: transport
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: header.bottom
          height: root.transportHeight
          foreground: root.foreground
          dim: root.dim
          bpm: root.song.bpm
          playing: root.playing
          looping: root.song.loop
          currentBar: root.currentBar
          currentBeat: root.currentBeat
          statusText: root.statusText
          onPlayRequested: { root.startPlayback(); root.refocusKeys() }
          onStopRequested: { root.stopPlayback(); root.refocusKeys() }
          onLoopToggled: {
            root.updateSong(Song.mergeSong(root.song, { loop: !root.song.loop }))
            root.refocusKeys()
          }
          onBpmChangedByUser: function(value) {
            root.updateSong(Song.mergeSong(root.song, { bpm: root.clampBpm(value) }))
          }
          onTapTempo: { root.tapTempo(); root.refocusKeys() }
        }

        CircleOfFifths {
          id: circle
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: transport.bottom
          height: content.circleHeight
          foreground: root.foreground
          dim: root.dim
          faint: root.faint
          tonicIndex: root.song.tonicIndex
          onTonicPicked: function(index, ring) {
            var from = root.song.tonicIndex
            var triad = Model.triad(index, ring)
            root.statusText = triad.label
            root.playMidiNotes(triad.notes, 0.7)
            if (index !== from) {
              var semitones = ((Model.PITCH_CLASS[index] - Model.PITCH_CLASS[from]) % 12 + 12) % 12
              var next = Song.transposeSong(root.song, semitones, Chords.transposeChord)
              root.updateSong(Song.mergeSong(next, { tonicIndex: index }))
            }
          }
          onChordPreviewed: function(index, ring, triad) {
            root.statusText = triad.label
            root.playMidiNotes(triad.notes, 0.7)
            if (root.structure && root.structure.editingSection < 0)
              root.insertSymbol(triad.label)
          }
        }

        SongStructure {
          id: structure
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: circle.bottom
          anchors.bottom: piano.top
          foreground: root.foreground
          dim: root.dim
          faint: root.faint
          sections: root.song.sections
          selectedSection: root.selectedSection
          selectedSlot: root.selectedSlot
          playSection: root.playing && root.playIndex >= 0 && root.playSlots[root.playIndex]
            ? root.playSlots[root.playIndex].sectionIndex : -1
          playSlot: root.playing && root.playIndex >= 0 && root.playSlots[root.playIndex]
            ? root.playSlots[root.playIndex].slot : -1
          onChordEdited: function(sectionIndex, slot, symbol) {
            root.updateSong(Song.setChord(root.song, sectionIndex, slot, symbol))
            if (symbol)
              root.previewSymbol(symbol)
          }
          onChordPreviewed: function(symbol) { root.previewSymbol(symbol) }
          onSectionAdded: root.updateSong(Song.addSection(root.song, "Verse"))
          onSectionRemoved: function(sectionIndex) {
            root.updateSong(Song.removeSection(root.song, sectionIndex))
          }
          onSectionRenamed: function(sectionIndex, name) {
            root.updateSong(Song.renameSection(root.song, sectionIndex, name))
          }
          onSlotSelected: function(sectionIndex, slot) {
            root.selectedSection = sectionIndex
            root.selectedSlot = slot
          }
        }

        Piano {
          id: piano
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.bottom: parent.bottom
          height: root.pianoHeight
          foreground: root.foreground
          dim: root.dim
          octave: root.song.octave
          layoutName: root.song.layout
          activeNotes: root.activeNotes
          sustain: root.sustain
          onNoteOn: function(midi) { root.playMidiNotes([midi], 0.45) }
          onNoteOff: function(midi) {
            if (!root.sustain)
              root.activeNotes = root.activeNotes.filter(function(n) { return n !== midi })
          }
          onOctaveChangedByUser: function(value) {
            root.updateSong(Song.mergeSong(root.song, { octave: KeyMap.clampOctave(value) }))
            root.refocusKeys()
          }
        }
      }
      }
    }
  }
}
