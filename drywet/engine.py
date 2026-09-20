import json
import sys

from drywet.context import Context
from drywet.event import Loop, Part, Sequence
from drywet.instrument import Drum, Sampler, Synth
from drywet.sink import BufferSink, PipeWireSink


def _instrument(ctx, msg):
    kind = msg.get("instrument", "synth")
    if kind == "synth":
        return Synth(ctx)
    if kind == "drum":
        return Drum(ctx)
    if kind == "sampler":
        return Sampler(ctx, msg.get("map") or {})
    raise ValueError("unknown instrument: %r" % (kind,))


def _attach_schedule(ctx, inst, payload):
    if not payload:
        return
    if isinstance(payload.get("sequence"), dict):
        spec = payload["sequence"]
        seq = Sequence(
            lambda time, note: inst.trigger_attack_release(note, "8n", time),
            spec.get("events") or [],
            spec.get("subdivision", "4n"),
        )
        seq.bind(ctx.transport).start(0)
    if isinstance(payload.get("part"), dict):
        spec = payload["part"]
        part = Part(
            lambda time, note: inst.trigger_attack_release(note, "8n", time),
            spec.get("events") or [],
        )
        part.bind(ctx.transport).start(0)
    if isinstance(payload.get("loop"), dict):
        spec = payload["loop"]
        loop = Loop(
            lambda time, _value: inst.trigger_attack_release("C4", "8n", time),
            spec.get("interval", "4n"),
        )
        loop.bind(ctx.transport).start(0)


def run(stdin, stdout, sink=None):
    ctx = Context(sink=sink if sink is not None else PipeWireSink())
    inst = Synth(ctx)

    def emit(obj):
        stdout.write(json.dumps(obj) + "\n")
        stdout.flush()

    for raw in stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            cmd = msg.get("cmd")
            if cmd == "warmup":
                inst = _instrument(ctx, msg)
                emit({"ok": True})
            elif cmd == "start":
                if "bpm" in msg:
                    ctx.transport.bpm = msg["bpm"]
                ctx.transport.loop = bool(msg.get("loop", False))
                _attach_schedule(ctx, inst, msg)
                ctx.transport.start()
                emit(
                    {
                        "event": "started",
                        "latencyMs": ctx.transport.latency_ms,
                        "position": ctx.transport.position,
                    }
                )
            elif cmd == "stop":
                ctx.transport.stop()
                emit({"ok": True})
            elif cmd == "pause":
                ctx.transport.pause()
                emit({"ok": True})
            elif cmd == "resume":
                ctx.transport.start()
                emit({"ok": True})
            elif cmd == "play-midi":
                inst.trigger_attack_release(
                    msg.get("note", "C4"), msg.get("duration", "8n")
                )
                emit({"ok": True})
            elif cmd == "bpm":
                ctx.transport.bpm = msg.get("value", ctx.transport.bpm)
                emit({"ok": True})
            elif cmd == "shutdown":
                ctx.transport.dispose()
                emit({"ok": True})
                return
            else:
                emit({"error": "unknown cmd: %s" % cmd})
        except Exception as exc:
            emit({"error": str(exc)})


def main(argv=None):
    del argv
    sink = BufferSink() if sys.argv[1:] == ["--buffer"] else None
    run(sys.stdin, sys.stdout, sink=sink)


if __name__ == "__main__":
    main()
