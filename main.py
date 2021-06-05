"""Main file for rendering relevant data"""


if __name__ == "__main__":
    from ot2 import parts
    from ot2 import render

    tagged_simultaneous_event, abjad_score, tempo_envelope = parts.dummy.DummyPart()()

    render.render_abjad(abjad_score)
    render.render_soundfiles(tagged_simultaneous_event, tempo_envelope)
