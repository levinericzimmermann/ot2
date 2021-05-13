import abjad  # type: ignore

from mutwo.converters.frontends import abjad_attachments
from mutwo.converters.frontends import abjad_constants as mutwo_abjad_constants

from ot2.parameters import playing_indicators


class ExplicitFermata(
    playing_indicators.ExplicitFermata, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        abjad.attach(
            abjad.Markup(
                contents="\\small {}-{} s".format(*self.waiting_range), direction="^"
            ),
            leaf,
        )
        abjad.attach(
            abjad.Fermata(self.fermata_type), leaf,
        )
        return leaf


# override mutwo default value
mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES = (
    mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES + (ExplicitFermata,)
)
