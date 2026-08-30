.pragma library

var REGION_COUNT = 3
var REGION_NAMES = ["Circle of fifths", "Song structure", "Keyboard"]

function cycleNavRegion(current, delta) {
  var n = Number(current)
  if (!isFinite(n))
    n = 0
  n = Math.floor(n)
  var d = Number(delta)
  if (!isFinite(d))
    d = 0
  d = Math.floor(d)
  var next = (n + d) % REGION_COUNT
  if (next < 0)
    next += REGION_COUNT
  return next
}

function regionName(index) {
  var n = Number(index)
  if (!isFinite(n))
    return ""
  n = Math.floor(n)
  if (n < 0 || n >= REGION_NAMES.length)
    return ""
  return REGION_NAMES[n]
}

function degreeIndexFromKey(key, text) {
  var t = text === undefined || text === null ? "" : String(text)
  if (t.length === 1) {
    var c = t.charCodeAt(0)
    if (c >= 0x31 && c <= 0x37)
      return c - 0x31
  }
  var k = Number(key)
  if (!isFinite(k))
    return -1
  k = Math.floor(k)
  if (k >= 0x31 && k <= 0x37)
    return k - 0x31
  if (k >= 0x01000031 && k <= 0x01000037)
    return k - 0x01000031
  return -1
}

var PREVIEW_AUDIO_GAP_MS = 100

function shouldSpawnPreviewAudio(lastMs, nowMs, minGapMs) {
  var now = Number(nowMs)
  if (!isFinite(now))
    return false
  var last = Number(lastMs)
  var gap = minGapMs === undefined || minGapMs === null ? PREVIEW_AUDIO_GAP_MS : Number(minGapMs)
  if (!isFinite(gap) || gap < 0)
    gap = PREVIEW_AUDIO_GAP_MS
  if (!isFinite(last) || last <= 0)
    return true
  return (now - last) >= gap
}
