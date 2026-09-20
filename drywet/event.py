class Sequence:
    def __init__(self, callback, events, subdivision="4n"):
        self.callback = callback
        self.events = events
        self.subdivision = subdivision
        self._ids = []
        self._transport = None

    def _flatten(self, events, start, width, transport):
        if not events:
            return
        slot = width / float(len(events))
        for index, event in enumerate(events):
            when = start + index * slot
            if event is None:
                continue
            if isinstance(event, list):
                self._flatten(event, when, slot, transport)
            else:
                event_id = transport.schedule(
                    lambda time, value=event: self.callback(time, value), when
                )
                self._ids.append(event_id)

    def start(self, offset=0):
        transport = self._transport
        if transport is None:
            raise ValueError("Sequence.bind(transport) required before start")
        if not isinstance(self.events, list):
            raise ValueError("events must be a list")
        start = transport.to_seconds(offset)
        width = transport.to_seconds(self.subdivision) * len(self.events)
        self._flatten(self.events, start, width, transport)
        return self

    def stop(self):
        if self._transport is None:
            return self
        ids = set(self._ids)
        self._transport._events = [
            event for event in self._transport._events if event["id"] not in ids
        ]
        self._ids = []
        return self

    def bind(self, transport):
        self._transport = transport
        return self


class Part:
    def __init__(self, callback, events):
        self.callback = callback
        self.events = events
        self._ids = []
        self._transport = None

    def bind(self, transport):
        self._transport = transport
        return self

    def start(self, offset=0):
        transport = self._transport
        if transport is None:
            raise ValueError("Part.bind(transport) required before start")
        base = transport.to_seconds(offset)
        for when, value in self.events:
            event_id = transport.schedule(
                lambda time, item=value: self.callback(time, item),
                base + transport.to_seconds(when),
            )
            self._ids.append(event_id)
        return self

    def stop(self):
        if self._transport is None:
            return self
        ids = set(self._ids)
        self._transport._events = [
            event for event in self._transport._events if event["id"] not in ids
        ]
        self._ids = []
        return self


class Loop:
    def __init__(self, callback, interval):
        self.callback = callback
        self.interval = interval
        self._id = None
        self._transport = None

    def bind(self, transport):
        self._transport = transport
        return self

    def start(self, offset=0):
        transport = self._transport
        if transport is None:
            raise ValueError("Loop.bind(transport) required before start")
        self._id = transport.schedule_repeat(
            lambda time: self.callback(time, None),
            self.interval,
            start_time=offset,
        )
        return self

    def stop(self):
        if self._transport is None or self._id is None:
            return self
        self._transport._events = [
            event for event in self._transport._events if event["id"] != self._id
        ]
        self._id = None
        return self
