import typing

import abjad  # type: ignore

from mutwo.converters.frontends import abjad_attachments
from mutwo.converters.frontends import abjad_constants as mutwo_abjad_constants

from ot2.parameters import notation_indicators
from ot2.parameters import playing_indicators


class Cue(playing_indicators.Cue, abjad_attachments.BangFirstAttachment):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        abjad.attach(
            abjad.Markup(contents=f"\\rounded-box {{ {self.nth_cue} }}", direction="^"),
            leaf,
        )
        return leaf


class Embouchure(playing_indicators.Embouchure, abjad_attachments.BangFirstAttachment):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        abjad.attach(
            abjad.Markup(contents=self.hint, direction="^"),
            leaf,
        )
        return leaf


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
            abjad.Fermata(self.fermata_type),
            leaf,
        )
        return leaf


class Noise(notation_indicators.Noise, abjad_attachments.BangFirstAttachment):
    border = 0.25
    y_center = 0.5
    maxima_width = 94
    # presence_to_height = {0: 2.5, 1: 3.5, 2: 4.7}
    presence_to_height = {0: 2.5, 1: 2.5, 2: 2.5}
    presence_to_color = {0: "#white", 1: "#(x11-color 'grey75)", 2: "#black"}
    density_to_percentage_density = {0: 0.075, 1: 0.2, 2: 0.4}

    import random

    random_module = random
    random_module.seed(100)

    @staticmethod
    def _make_box(color: str, height: float, width: float, border: float) -> str:
        def _make_coordinates(a: float, b: float) -> str:
            return f"#'({a} . {b})"

        def _make_box_part(x_start: float, height: float, width: float) -> str:
            x_coordinates = _make_coordinates(x_start, x_start + width)
            halved_height = height / 2
            y_coordinates = _make_coordinates(
                Noise.y_center + halved_height, Noise.y_center - halved_height
            )
            return f"\\filled-box {x_coordinates} {y_coordinates} #1"

        lines = (
            "\\combine",
            _make_box_part(0, height, width),
            f"\\with-color {color}",
            _make_box_part(border, height - (border * 2), width - (border * 2)),
        )
        return "\n".join(lines)

    @staticmethod
    def _make_continous_noise(presence: int, is_pitch: bool) -> str:
        if is_pitch:
            height_factor = 0.5
        else:
            height_factor = 1
        return Noise._make_box(
            Noise.presence_to_color[presence],
            Noise.presence_to_height[presence] * height_factor,
            Noise.maxima_width,
            Noise.border,
        )

    @staticmethod
    def _make_discreet_noise_blueprint_box(presence: int, box_width: float) -> str:
        border = Noise.border
        height = Noise.presence_to_height[presence]
        color = Noise.presence_to_color[presence]
        box_blueprint = Noise._make_box(color, height, box_width, border)
        return box_blueprint

    @staticmethod
    def _make_unperiodic_discreet_noise_distances(
        density: int, width: float, box_width: float
    ) -> typing.Tuple[float, ...]:
        max_n_boxes = width / (box_width + 0.25)
        n_boxes_to_distribute = int(
            Noise.density_to_percentage_density[density] * max_n_boxes
        )
        remaining_space = width - (n_boxes_to_distribute * box_width)
        horizontal_distances = [0 for _ in range(n_boxes_to_distribute)]
        horizontal_distances_indices = list(range(len(horizontal_distances)))
        Noise.random_module.shuffle(horizontal_distances_indices)
        average_horizontal_distance = remaining_space / len(horizontal_distances)
        distance_for_pair = average_horizontal_distance * 2
        max_distance = average_horizontal_distance * 1.95
        for index0, index1 in zip(
            horizontal_distances_indices[::2], horizontal_distances_indices[1::2]
        ):
            distance0 = Noise.random_module.uniform(
                average_horizontal_distance, max_distance
            )
            distance1 = distance_for_pair - distance0
            horizontal_distances[index0] = distance0
            horizontal_distances[index1] = distance1
        return tuple(horizontal_distances)

    @staticmethod
    def _make_periodic_discreet_noise_distances(
        density: int, width: float, box_width: float
    ):
        max_n_boxes = width / (box_width + 0.25)
        n_boxes_to_distribute = int(
            Noise.density_to_percentage_density[density] * max_n_boxes
        )
        remaining_space = width - (n_boxes_to_distribute * box_width)
        average_horizontal_distance = remaining_space / n_boxes_to_distribute
        return tuple(
            average_horizontal_distance for _ in range(n_boxes_to_distribute)
        )

    @staticmethod
    def _make_discreet_noise_distances(
        density: int, width: float, box_width: float, is_periodic: bool
    ) -> typing.Tuple[float, ...]:
        if is_periodic:
            return Noise._make_periodic_discreet_noise_distances(density, width, box_width)
        else:
            return Noise._make_unperiodic_discreet_noise_distances(density, width, box_width)

    @staticmethod
    def _make_discreet_noise(density: int, presence: int, is_periodic: bool) -> str:
        box_width = 0.9
        box_blueprint = Noise._make_discreet_noise_blueprint_box(presence, box_width)
        width = 80
        horizontal_distances = Noise._make_discreet_noise_distances(
            density, width, box_width, is_periodic
        )
        boxes_and_spaces = []
        for distance in horizontal_distances:
            boxes_and_spaces.append(box_blueprint)
            boxes_and_spaces.append(f"\\hspace #{distance}")
        return "\n".join(boxes_and_spaces)

    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\override Staff.StaffSymbol.line-count = #1", format_slot="before"
            ),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\once \\hide Staff.Clef", format_slot="before"),
            leaf,
        )

        if self.density == 3:
            noise_string = Noise._make_continous_noise(self.presence, self.is_pitch)
        else:
            noise_string = Noise._make_discreet_noise(
                self.density, self.presence, self.is_periodic
            )

        lilypond_literal = abjad.LilyPondLiteral(
            r"_\markup { " + noise_string + " }", "after"
        )

        abjad.attach(
            lilypond_literal,
            leaf,
        )
        return leaf


class Fingering(playing_indicators.Fingering, abjad_attachments.BangFirstAttachment):
    fingering_size = 0.7

    @staticmethod
    def _tuple_to_scheme_list(tuple_to_convert: typing.Tuple[str, ...]) -> str:
        return f"({' '.join(tuple_to_convert)})"

    def _get_markup_content(self) -> str:
        # \\override #'(graphical . #f)
        return f"""
\\override #'(size . {self.fingering_size})
{{
    \\woodwind-diagram
    #'clarinet
    #'((cc . {self._tuple_to_scheme_list(self.cc)})
       (lh . {self._tuple_to_scheme_list(self.lh)})
       (rh . {self._tuple_to_scheme_list(self.rh)}))
}}"""

    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        fingering = abjad.LilyPondLiteral(
            f"^\\markup {self._get_markup_content()}", format_slot="after"
        )
        abjad.attach(fingering, leaf)
        return leaf


class CentDeviation(
    notation_indicators.CentDeviation, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        if self.deviation % 100 != 0:
            if self.deviation > 0:
                prefix = "+"
            else:
                prefix = "-"
            adjusted_deviation = round(abs(self.deviation))
            markup = abjad.Markup(
                "\\tiny { " + f"{prefix}{adjusted_deviation} ct" + " } ", direction="up"
            )
            abjad.attach(
                markup,
                leaf,
            )
        return leaf


# override mutwo default value
mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES = (
    mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES
    + (ExplicitFermata, Embouchure, Noise, CentDeviation, Cue, Fingering)
)
