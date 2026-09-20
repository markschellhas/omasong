from drywet.limits import BUFFER_LATENCY_MS, DEFAULT_PPQ, MAX_SCHEDULE_SECONDS


class Transport:
    def __init__(self, context):
        self.context = context
        self.state = "stopped"
        self.PPQ = DEFAULT_PPQ
        self._seconds = 0.0
        self._listeners = {"start": [], "stop": [], "pause": [], "loop": []}
        self._bpm = 120
        self._running_bpm = 120
        self._time_signature = (4, 4)
        self.loop = False
        self._loop_start = 0.0
        self._loop_end = 0.0
        self._events = []
        self._next_event_id = 1
        self._fired = set()

    @property
    def latency_ms(self):
        return getattr(self.context.sink, "latency_ms", BUFFER_LATENCY_MS)

    @property
    def seconds(self):
        return self._seconds

    def _normalize_signature(self, value):
        if isinstance(value, int):
            if value <= 0:
                raise ValueError("invalid time_signature")
            return (value, 4) if value != 4 else (4, 4)
        if (
            isinstance(value, tuple)
            and len(value) == 2
            and all(isinstance(x, int) and x > 0 for x in value)
        ):
            return (int(value[0]), int(value[1]))
        raise ValueError("time_signature must be (n, d) or int")

    @property
    def bpm(self):
        return self._bpm

    @bpm.setter
    def bpm(self, value):
        from drywet.limits import BPM_MAX, BPM_MIN

        bpm = float(value)
        if bpm < BPM_MIN or bpm > BPM_MAX:
            raise ValueError("BPM must be 40–240")
        self._bpm = bpm
        if self.state != "started":
            self._running_bpm = bpm

    @property
    def time_signature(self):
        return self._time_signature

    @time_signature.setter
    def time_signature(self, value):
        self._time_signature = self._normalize_signature(value)

    def _clock(self):
        return dict(
            bpm=self._running_bpm if self.state == "started" else self._bpm,
            time_signature=self._time_signature,
            now=self._seconds,
            ppq=self.PPQ,
        )

    def to_seconds(self, value):
        from drywet.time import to_seconds

        return to_seconds(value, **self._clock())

    def to_ticks(self, value):
        from drywet.time import to_ticks

        return to_ticks(value, **self._clock())

    def to_frequency(self, value):
        from drywet.time import to_frequency

        return to_frequency(value, **self._clock())

    @property
    def ticks(self):
        return self.to_ticks(self._seconds)

    @property
    def position(self):
        num, den = self._time_signature
        quarter = 60.0 / self._clock()["bpm"]
        beat = quarter * (4.0 / den)
        bar = num * beat
        sixteenth = quarter / 4.0
        remaining = self._seconds
        bars = int(remaining // bar) if bar else 0
        remaining -= bars * bar
        beats = int(remaining // beat) if beat else 0
        remaining -= beats * beat
        sixteenths = int(round(remaining / sixteenth)) if sixteenth else 0
        if sixteenths == 4:
            sixteenths = 0
            beats += 1
        if beats >= num:
            beats = 0
            bars += 1
        return "%d:%d:%d" % (bars, beats, sixteenths)

    @property
    def loop_start(self):
        return self._loop_start

    @loop_start.setter
    def loop_start(self, value):
        self._loop_start = self.to_seconds(value)

    @property
    def loop_end(self):
        return self._loop_end

    @loop_end.setter
    def loop_end(self, value):
        self._loop_end = self.to_seconds(value)

    def set_loop_points(self, start, end):
        start_s = self.to_seconds(start)
        end_s = self.to_seconds(end)
        if end_s <= start_s:
            raise ValueError("loop_end must be after loop_start")
        self._loop_start = start_s
        self._loop_end = end_s

    def on(self, name, callback):
        if name not in self._listeners:
            raise ValueError("unknown event: %r" % (name,))
        self._listeners[name].append(callback)

    def _emit(self, name, time):
        for callback in list(self._listeners.get(name, [])):
            callback(time)

    def start(self):
        if self.state == "started":
            return self
        if self.state == "paused":
            self.state = "started"
            self._emit("start", self._seconds)
            return self
        self._running_bpm = self._bpm
        self.state = "started"
        self._seconds = 0.0
        self.context.sink.accepted = True
        self._emit("start", self._seconds)
        return self

    def pause(self):
        if self.state == "started":
            self.state = "paused"
            self._emit("pause", self._seconds)
        return self

    def stop(self):
        self.state = "stopped"
        self._seconds = 0.0
        self.context.sink.stop()
        self._emit("stop", self._seconds)
        return self

    def toggle(self):
        if self.state == "started":
            return self.pause()
        return self.start()

    def _event_time(self, value):
        seconds = self.to_seconds(value)
        if seconds < 0 or seconds > MAX_SCHEDULE_SECONDS:
            raise ValueError("schedule time out of range")
        return seconds

    def schedule(self, callback, time):
        event_id = self._next_event_id
        self._next_event_id += 1
        self._events.append(
            {
                "id": event_id,
                "time": self._event_time(time),
                "callback": callback,
                "interval": None,
            }
        )
        return event_id

    def schedule_once(self, callback, time):
        return self.schedule(callback, time)

    def schedule_repeat(self, callback, interval, start_time=0):
        event_id = self._next_event_id
        self._next_event_id += 1
        self._events.append(
            {
                "id": event_id,
                "time": self._event_time(start_time),
                "callback": callback,
                "interval": self.to_seconds(interval),
            }
        )
        return event_id

    def cancel(self, after):
        after_s = self.to_seconds(after)
        self._events = [event for event in self._events if event["time"] < after_s]

    def clear(self):
        self._events = []
        self._fired = set()

    def dispose(self):
        self.clear()
        self.stop()
        self.context.sink.close()

    def _occurrences(self, event, until):
        start = event["time"]
        interval = event["interval"]
        if interval is None:
            return [start] if start <= until + 1e-12 else []
        if interval <= 0:
            raise ValueError("repeat interval must be > 0")
        times = []
        cursor = start
        while cursor <= until + 1e-12:
            times.append(cursor)
            cursor += interval
        return times

    def _fire_until(self, until):
        until_s = self.to_seconds(until)
        pending = []
        for event in self._events:
            for when in self._occurrences(event, until_s):
                key = (event["id"], round(when, 9))
                if key in self._fired:
                    continue
                pending.append((when, event["id"], event["callback"], key))
        pending.sort(key=lambda item: (item[0], item[1]))
        for when, _eid, callback, key in pending:
            self._seconds = when
            callback(when)
            self._fired.add(key)
        self._seconds = until_s

    def render(self, duration):
        if self.state != "started":
            self.start()
        until = self.to_seconds(duration)
        if self.loop and self._loop_end > self._loop_start:
            length = self._loop_end - self._loop_start
            repeats = []
            for event in list(self._events):
                if event["interval"] is not None:
                    continue
                if self._loop_start <= event["time"] < self._loop_end:
                    cursor = event["time"] + length
                    while cursor <= until + 1e-12:
                        repeats.append(
                            {
                                "id": self._next_event_id,
                                "time": cursor,
                                "callback": event["callback"],
                                "interval": None,
                            }
                        )
                        self._next_event_id += 1
                        cursor += length
            self._events.extend(repeats)
        self._fire_until(until)
        needed = int(round(until * self.context.sample_rate))
        if self.context.sink.write_cursor < needed:
            self.context.sink.write([0.0] * (needed - self.context.sink.write_cursor))
        return list(self.context.sink.frames)
