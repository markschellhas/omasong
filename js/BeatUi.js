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

function beatAsciiRow(values, hitChar, restChar) {
  var hit = (typeof hitChar === "string" && hitChar.length > 0) ? hitChar.charAt(0) : "x"
  var rest = (typeof restChar === "string" && restChar.length > 0) ? restChar.charAt(0) : "-"
  if (!Array.isArray(values))
    return ""
  var out = ""
  for (var i = 0; i < values.length; i++)
    out += values[i] ? hit : rest
  return out
}
