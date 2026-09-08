.pragma library

function sequencerStepWidth(viewportWidth, stepCount, minimumWidth) {
  var viewport = Number(viewportWidth)
  var steps = Number(stepCount)
  var minimum = Number(minimumWidth)
  if (!isFinite(viewport) || viewport < 1)
    viewport = 1
  if (!isFinite(steps) || steps < 1)
    steps = 1
  else
    steps = Math.floor(steps)
  if (!isFinite(minimum) || minimum < 1)
    minimum = 1
  return Math.max(minimum, viewport / steps)
}

function sequencerFocusCount(stepCount, laneCount) {
  var steps = Number(stepCount)
  var lanes = Number(laneCount)
  if (!isFinite(steps) || steps < 1)
    steps = 1
  if (!isFinite(lanes) || lanes < 1)
    lanes = 1
  return 2 + Math.floor(steps) * Math.floor(lanes)
}

function sequencerNextFocusIndex(current, delta, stepCount, laneCount) {
  var count = sequencerFocusCount(stepCount, laneCount)
  var index = Number(current)
  if (!isFinite(index))
    index = 0
  index = Math.floor(index)
  var direction = Number(delta) < 0 ? -1 : 1
  var next = (index + direction) % count
  return next < 0 ? next + count : next
}

// A pattern lane that reached QML through a model or property boundary
// arrives as a sequence wrapper: it indexes and reports length like an
// array, but Array.isArray() is false for it. Duck-type on length so both
// real arrays and wrapped sequences work.
function beatRowLength(values) {
  if (!values || typeof values === "string")
    return 0
  var n = Number(values.length)
  if (!isFinite(n) || n < 1)
    return 0
  return Math.floor(n)
}

// True when any lane in a measure's pattern has a hit. Reads sequence
// wrappers as well as real arrays, and needs no lane list because the
// pattern is keyed by lane name.
function patternHasHit(pattern) {
  if (!pattern || typeof pattern !== "object")
    return false
  for (var key in pattern) {
    var values = pattern[key]
    var count = beatRowLength(values)
    for (var step = 0; step < count; step++) {
      if (values[step])
        return true
    }
  }
  return false
}

function beatAsciiRow(values, hitChar, restChar) {
  var hit = (typeof hitChar === "string" && hitChar.length > 0) ? hitChar.charAt(0) : "x"
  var rest = (typeof restChar === "string" && restChar.length > 0) ? restChar.charAt(0) : "-"
  var count = beatRowLength(values)
  var out = ""
  for (var i = 0; i < count; i++)
    out += values[i] ? hit : rest
  return out
}
