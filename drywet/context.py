from drywet.limits import DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE
from drywet.sink import BufferSink


class Context:
    def __init__(self, sample_rate=DEFAULT_SAMPLE_RATE, channels=DEFAULT_CHANNELS, sink=None):
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.sink = sink if sink is not None else BufferSink(
            sample_rate=self.sample_rate, channels=self.channels
        )
        from drywet.transport import Transport

        self.transport = Transport(self)
