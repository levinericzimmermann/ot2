import typing

import expenvelope
import pyo


class Resonator(object):
    def __init__(
        self,
        path: str,
        frequencies: typing.Sequence[float],
        output_name: typing.Optional[str] = None,
        output_path: str = "builds/tape",
        minfreq: float = 80,
        waveguide_mul: float = 1,
        bandpass_mul: float = 1,
        waveguide_dur: float = 5,
        source_envelope: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 1), (180, 0.9)
        ),
        waveguide_envelope: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 0.2), (180, 0.2)
        ),
        filter_envelope: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 0.2), (180, 0.2)
        ),
        filter_q_envelope: expenvelope.Envelope = expenvelope.Envelope.from_points(
            (0, 2), (180, 2)
        ),
        pan_lfo_frequency: float = 1,
    ):
        if not output_name:
            output_name = path.split("/")[-1].split(".")[0] + "-resonated"

        self.frequencies = frequencies
        self.path = path
        self.output_name = output_name
        self.output_path = output_path
        self.complete_output_path = f"{output_path}/{output_name}.wav"
        self.minfreq = minfreq
        self.source_envelope = source_envelope
        self.waveguide_envelope = waveguide_envelope
        self.filter_envelope = filter_envelope
        self.filter_q_envelope = filter_q_envelope
        self.waveguide_mul = waveguide_mul
        self.waveguide_dur = waveguide_dur
        self.bandpass_mul = bandpass_mul
        self.pan_lfo_frequency = pan_lfo_frequency

    def render(self):
        s = pyo.Server(audio="offline")
        s.boot()

        sndinfo = pyo.sndinfo(self.path)
        s.recordOptions(filename=self.complete_output_path, dur=sndinfo[1])

        source = pyo.SfPlayer(self.path)
        source_envelope = pyo.Expseg(
            list(zip(self.source_envelope.times, self.source_envelope.levels)), exp=5
        )
        waveguide_envelope = pyo.Expseg(
            list(zip(self.waveguide_envelope.times, self.waveguide_envelope.levels)),
            exp=5,
        )
        filter_envelope = pyo.Expseg(
            list(zip(self.filter_envelope.times, self.filter_envelope.levels)),
            exp=5,
        )
        filter_q_envelope = pyo.Linseg(
            list(zip(self.filter_q_envelope.times, self.filter_q_envelope.levels))
        )

        waveguide = pyo.Waveguide(
            source,
            freq=self.frequencies,
            minfreq=self.minfreq,
            mul=self.waveguide_mul,
            dur=self.waveguide_dur,
        )
        bandpass = pyo.Resonx(
            waveguide,
            self.frequencies,
            q=filter_q_envelope,
            stages=4,
            mul=self.bandpass_mul,
        )

        lfo = pyo.Sine(freq=self.pan_lfo_frequency, mul=0.5, add=0.5)
        bandpass_pan = pyo.Pan(bandpass, outs=2, pan=lfo)

        filter_q_envelope.play()
        filter_envelope.play()
        source_envelope.play()
        waveguide_envelope.play()

        (bandpass_pan * filter_envelope).out()
        (waveguide * waveguide_envelope).out()
        (source * source_envelope).out()

        s.start()
