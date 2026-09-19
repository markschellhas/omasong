.pragma library

// The overlay and the bar widget are separate QML components with no shared
// object graph, so playback state crosses between them as a small JSON file
// under XDG_RUNTIME_DIR. Keep the document flat: the widget must be able to
// trust whatever a stale or truncated file hands it.

var TEXT_LIMIT = 120
var MAX_RAW_BYTES = 65536

function sanitizeLine(value, limit) {
  var text = value === undefined || value === null ? "" : String(value)
  var max = Number(limit)
  if (!isFinite(max) || max <= 0)
    max = TEXT_LIMIT
  return text.replace(/[\r\n\t]+/g, " ").slice(0, max)
}

function emptyStatus() {
  return { playing: false, panelOpen: false, title: "" }
}

function statusDocument(playing, title, panelOpen) {
  return {
    playing: playing === true,
    panelOpen: panelOpen === true,
    title: sanitizeLine(title, TEXT_LIMIT)
  }
}

function parseStatus(raw) {
  if (typeof raw !== "string" || !raw.length || raw.length > MAX_RAW_BYTES)
    return emptyStatus()
  var parsed
  try {
    parsed = JSON.parse(raw)
  } catch (e) {
    return emptyStatus()
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
    return emptyStatus()
  return statusDocument(parsed.playing, parsed.title, parsed.panelOpen)
}

// Bar tooltips render as rich text, so angle brackets in a song title would be
// read as markup.
function tooltipText(playing, title, panelOpen) {
  if (playing !== true)
    return "Open Songwriter"
  var name = sanitizeLine(title, TEXT_LIMIT) || "Untitled"
  name = name.replace(/</g, "\u2039").replace(/>/g, "\u203a")
  return (panelOpen === true ? "Playing: " : "Playing in background: ")
    + name + "  \u00b7  right-click to stop"
}
