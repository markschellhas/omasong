import shutil
import struct
import subprocess

from drywet.limits import (
    BUFFER_LATENCY_MS,
    DEFAULT_CHANNELS,
    DEFAULT_SAMPLE_RATE,
    PIPEWIRE_LATENCY_MS,
)


class BufferSink:
    latency_ms = BUFFER_LATENCY_MS

    def __init__(self, sample_rate=DEFAULT_SAMPLE_RATE, channels=DEFAULT_CHANNELS):
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self._buf = []
        self.write_cursor = 0
        self.accepted = False

    def _ensure(self, n):
        if len(self._buf) < n:
            self._buf.extend([0.0] * (n - len(self._buf)))

    def mix(self, frames, at_sample=None):
        if at_sample is None:
            at_sample = self.write_cursor
        start = int(at_sample) * self.channels
        needed = start + len(frames) * self.channels
        self._ensure(needed)
        for i, sample in enumerate(frames):
            value = float(sample)
            for ch in range(self.channels):
                self._buf[start + i * self.channels + ch] += value
        self.accepted = True

    def write(self, frames):
        self.mix(frames, at_sample=self.write_cursor)
        self.write_cursor += len(frames)

    def stop(self):
        return None

    def close(self):
        return None

    @property
    def frames(self):
        return list(self._buf)

    def to_pcm_s16le(self):
        out = bytearray()
        for sample in self._buf:
            clipped = max(-1.0, min(1.0, sample))
            out.extend(struct.pack("<h", int(round(clipped * 32767))))
        return bytes(out)


class PipeWireSink:
    latency_ms = PIPEWIRE_LATENCY_MS

    def __init__(self, sample_rate=DEFAULT_SAMPLE_RATE, channels=DEFAULT_CHANNELS):
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.write_cursor = 0
        self.accepted = False
        self._proc = None
        self._buffer = BufferSink(sample_rate=self.sample_rate, channels=self.channels)

    def _cmd(self):
        rate = str(self.sample_rate)
        ch = str(self.channels)
        if shutil.which("pw-cat"):
            return [
                "pw-cat",
                "--playback",
                "--raw",
                "--format",
                "s16",
                "--rate",
                rate,
                "--channels",
                ch,
                "-",
            ]
        if shutil.which("paplay"):
            return [
                "paplay",
                "--raw",
                "--format=s16le",
                "--rate=" + rate,
                "--channels=" + ch,
            ]
        if shutil.which("aplay"):
            return ["aplay", "-t", "raw", "-f", "S16_LE", "-r", rate, "-c", ch]
        raise RuntimeError("no pw-cat, paplay, or aplay")

    def _ensure_proc(self):
        if self._proc is not None:
            return
        self._proc = subprocess.Popen(
            self._cmd(),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def mix(self, frames, at_sample=None):
        self._buffer.mix(frames, at_sample=at_sample)
        self.accepted = True

    def write(self, frames):
        self.mix(frames, at_sample=self.write_cursor)
        self._ensure_proc()
        pcm = BufferSink(sample_rate=self.sample_rate, channels=self.channels)
        pcm.mix(frames, at_sample=0)
        self._proc.stdin.write(pcm.to_pcm_s16le())
        self._proc.stdin.flush()
        self.write_cursor += len(frames)
        self.accepted = True

    def stop(self):
        if self._proc is not None and self._proc.stdin:
            try:
                self._proc.stdin.close()
            except OSError:
                pass
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1)
            except Exception:
                pass
        self._proc = None

    def close(self):
        self.stop()
