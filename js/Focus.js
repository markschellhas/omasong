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
