import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from core.domain.models import to_unicode_symbols
from core.i18n import T
from visualizer.harmonic_graph import HarmonicGraph
from visualizer.theming import ThemeMode, get_theme_for_tonality

TEMP_IMAGE_DIR = Path(__file__).resolve().parent.parent.parent / "temp_images"
TEMP_IMAGE_DIR.mkdir(exist_ok=True)


@dataclass
class NodeInfo:
    """Structure to hold information for each node to be drawn."""

    node_id: str
    chord: str
    function: str
    shape: str
    step: ExplanationStepAPI


def _is_pivot_modulation(step: ExplanationStepAPI) -> bool:
    """Check if a step represents a pivot modulation using structured data."""
    return step.rule_type == "pivot_modulation"


def _get_secondary_style_variant(target_tonality: str) -> str:
    """Determine the style variant for secondary chords based on tonality quality.
    
    Args:
        target_tonality: The name of the target tonality (e.g., "G Major", "D minor")
        
    Returns:
        "dashed_filled" for minor tonalities, "solid_filled" for major tonalities
    """
    is_minor_secondary = "minor" in target_tonality.lower()
    return "dashed_filled" if is_minor_secondary else "solid_filled"


def _extract_pivot_target_tonality(step: ExplanationStepAPI) -> Optional[str]:
    """Extract the target tonality from pivot modulation using structured data."""
    return step.pivot_target_tonality


class VisualizerService:
    def create_graph_from_analysis(
        self, analysis_data: ProgressionAnalysisResponse, theme_mode: ThemeMode = "light"
    ) -> str:
        if not analysis_data.is_tonal_progression:
            raise ValueError(T("errors.cannot_visualize_non_tonal"))

        tonality_name = analysis_data.identified_tonality
        if tonality_name is None:
            raise ValueError(T("errors.cannot_visualize_no_tonality"))

        # Get the raw (untranslated) tonality name for comparisons
        raw_tonality_name = None
        for step in analysis_data.explanation_details:
            if step.raw_tonality_used_in_step:
                raw_tonality_name = step.raw_tonality_used_in_step
                break

        # Fallback if no raw tonality found
        if raw_tonality_name is None:
            raw_tonality_name = tonality_name

        theme = get_theme_for_tonality(raw_tonality_name, theme_mode)
        output_filename = TEMP_IMAGE_DIR / str(uuid.uuid4())
        graph = HarmonicGraph(theme=theme, temp_dir=TEMP_IMAGE_DIR)

        # Identify secondary tonalities used in the progression
        secondary_tonalities = set()
        for step in analysis_data.explanation_details:
            # Regular secondary tonalities
            raw_tonality = step.raw_tonality_used_in_step or step.tonality_used_in_step
            if raw_tonality and raw_tonality != raw_tonality_name:
                secondary_tonalities.add(raw_tonality)

            # Pivot target tonalities
            if _is_pivot_modulation(step):
                target_tonality = _extract_pivot_target_tonality(step)
                if target_tonality and target_tonality != raw_tonality_name:
                    secondary_tonalities.add(target_tonality)

        # Create themes for secondary tonalities
        secondary_themes = {}
        for secondary_tonality in secondary_tonalities:
            secondary_themes[secondary_tonality] = get_theme_for_tonality(
                secondary_tonality, theme_mode
            )

        function_to_shape = {"TONIC": "house", "DOMINANT": "circle", "SUBDOMINANT": "cds"}

        # Determine the style for primary chords based on the tonality mode
        is_minor_tonality = "minor" in tonality_name.lower()
        primary_style_variant = "dashed_filled" if is_minor_tonality else "solid_filled"

        relevant_steps = [
            step for step in analysis_data.explanation_details if step.processed_chord
        ]
        relevant_steps.reverse()

        main_world_nodes: List[Optional[NodeInfo]] = []
        possible_world_nodes: List[Optional[NodeInfo]] = [None] * len(relevant_steps)

        # 1. FIRST PASS: Classify and create nodes for each world
        for i, step in enumerate(relevant_steps):
            chord = step.processed_chord
            if chord is None:
                continue

            # Convert ASCII symbols to Unicode musical symbols for display
            chord_display = to_unicode_symbols(chord)

            function = "TONIC"
            if step.tonal_function:
                # Use the structured non-translated function field
                function = step.tonal_function
            elif step.evaluated_functional_state:
                # Fallback: Extract function from translated string
                function = step.evaluated_functional_state.split(" ")[0]

            shape = function_to_shape.get(function, "circle")
            raw_tonality = step.raw_tonality_used_in_step or step.tonality_used_in_step
            is_primary = raw_tonality is not None and raw_tonality == raw_tonality_name
            is_pivot = _is_pivot_modulation(step)

            main_node = NodeInfo(f"{chord}_main_{i}", chord_display, function, shape, step)
            main_world_nodes.append(main_node)
            if is_primary:
                # Apply the style determined by the tonality's mode
                graph.add_primary_chord(
                    main_node.node_id,
                    main_node.chord,
                    shape=main_node.shape,
                    style_variant=primary_style_variant,
                )
            else:
                # Non-diatonic chords - use the correct theme for secondary tonality
                target_tonality = None
                if is_pivot:
                    # For pivots, extract the target tonality from structured data
                    target_tonality = _extract_pivot_target_tonality(step)
                elif raw_tonality and raw_tonality != raw_tonality_name:
                    # For regular secondary chords, use the raw tonality from the step
                    target_tonality = raw_tonality

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        main_node.node_id,
                        main_node.chord,
                        secondary_theme,
                        shape=main_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )
                else:
                    # Fallback to original placeholder chord method
                    graph.add_placeholder_chord(
                        main_node.node_id,
                        main_node.chord,
                        shape=main_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )

            if not is_primary or is_pivot:
                secondary_function = "TONIC" if is_pivot else function
                secondary_shape = function_to_shape.get(secondary_function, "circle")
                possible_node = NodeInfo(
                    f"{chord}_possible_{i}",
                    chord_display,
                    secondary_function,
                    secondary_shape,
                    step,
                )
                possible_world_nodes[i] = possible_node

                # Use the correct theme for secondary tonality
                target_tonality = None
                if is_pivot:
                    # For pivots, extract the target tonality from structured data
                    target_tonality = _extract_pivot_target_tonality(step)
                elif raw_tonality and raw_tonality != raw_tonality_name:
                    # For regular secondary chords, use the raw tonality from the step
                    target_tonality = raw_tonality

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        possible_node.node_id,
                        possible_node.chord,
                        secondary_theme,
                        shape=possible_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )
                else:
                    # Fallback to original secondary chord method
                    graph.add_secondary_chord(
                        possible_node.node_id,
                        possible_node.chord,
                        shape=possible_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )

        # 2. SECOND PASS: Connect and align the nodes
        for i in range(len(main_world_nodes)):
            current_main_node: Optional[NodeInfo] = main_world_nodes[i]
            current_possible_node: Optional[NodeInfo] = possible_world_nodes[i]

            if current_main_node and current_possible_node:
                graph.align_nodes_in_ranks(
                    [current_main_node.node_id, current_possible_node.node_id]
                )

                # Determine the appropriate stroke color based on the node's tonality
                step = current_main_node.step
                raw_tonality = step.raw_tonality_used_in_step or step.tonality_used_in_step
                is_primary = raw_tonality is not None and raw_tonality == raw_tonality_name
                is_pivot = _is_pivot_modulation(step)

                if is_primary:
                    # Use primary theme stroke color
                    color = theme["primary_stroke"]
                else:
                    # Use secondary theme stroke color
                    target_tonality = None
                    if is_pivot:
                        target_tonality = _extract_pivot_target_tonality(step)
                    elif raw_tonality and raw_tonality != raw_tonality_name:
                        target_tonality = raw_tonality

                    if target_tonality and target_tonality in secondary_themes:
                        secondary_theme = secondary_themes[target_tonality]
                        color = secondary_theme["primary_stroke"]
                    else:
                        color = theme["secondary_stroke"]

                graph.connect_nodes(
                    current_main_node.node_id,
                    current_possible_node.node_id,
                    style="dotted",
                    color=color,
                    arrowhead="none",
                    constraint="false",
                )

            if i > 0:
                prev_main = main_world_nodes[i - 1]
                curr_main = main_world_nodes[i]
                if (
                    prev_main
                    and curr_main
                    and (
                        prev_main.step.raw_tonality_used_in_step
                        or prev_main.step.tonality_used_in_step
                    )
                    == raw_tonality_name
                    and (
                        curr_main.step.raw_tonality_used_in_step
                        or curr_main.step.tonality_used_in_step
                    )
                    == raw_tonality_name
                ):
                    # Como a lista foi revertida, curr_main é cronologicamente anterior a prev_main
                    # Para cadências, queremos: curr_main (anterior) -> prev_main (posterior)
                    # Mas nos índices: prev_main[i-1] -> curr_main[i]
                    if prev_main.function == "SUBDOMINANT" and curr_main.function == "DOMINANT":
                        graph.connect_nodes(
                            prev_main.node_id,
                            curr_main.node_id,
                            style="dashed",
                            color=theme["primary_stroke"],
                            penwidth="2",
                        )
                    elif prev_main.function == "DOMINANT" and curr_main.function == "TONIC":
                        graph.connect_with_double_arrow(
                            prev_main.node_id, curr_main.node_id, "primary_stroke"
                        )
                    elif prev_main.function == "SUBDOMINANT" and curr_main.function == "TONIC":
                        graph.connect_with_single_arrow(
                            prev_main.node_id, curr_main.node_id, "primary_stroke"
                        )

                prev_possible = possible_world_nodes[i - 1]
                curr_possible = possible_world_nodes[i]
                if prev_possible and curr_possible:
                    # Como a lista foi revertida, curr_possible é cronologicamente anterior a prev_possible
                    # Para cadências, queremos: curr_possible (anterior) -> prev_possible (posterior)
                    # Mas nos índices: prev_possible[i-1] -> curr_possible[i]
                    if prev_possible.function == "DOMINANT" and curr_possible.function == "TONIC":
                        # Determine which secondary theme to use based on target tonality
                        target_tonality_for_cadence: Optional[str] = None

                        # Check current possible node for pivot target tonality
                        curr_step = curr_possible.step
                        curr_raw_tonality = (
                            curr_step.raw_tonality_used_in_step or curr_step.tonality_used_in_step
                        )
                        if _is_pivot_modulation(curr_step):
                            target_tonality_for_cadence = _extract_pivot_target_tonality(curr_step)
                        elif curr_raw_tonality and curr_raw_tonality in secondary_themes:
                            target_tonality_for_cadence = curr_raw_tonality

                        # Fallback to previous possible node
                        if not target_tonality_for_cadence:
                            prev_step = prev_possible.step
                            prev_raw_tonality = (
                                prev_step.raw_tonality_used_in_step
                                or prev_step.tonality_used_in_step
                            )
                            if _is_pivot_modulation(prev_step):
                                target_tonality_for_cadence = _extract_pivot_target_tonality(
                                    prev_step
                                )
                            elif prev_raw_tonality and prev_raw_tonality in secondary_themes:
                                target_tonality_for_cadence = prev_raw_tonality

                        if (
                            target_tonality_for_cadence
                            and target_tonality_for_cadence in secondary_themes
                        ):
                            secondary_theme = secondary_themes[target_tonality_for_cadence]
                            graph.connect_with_double_arrow(
                                prev_possible.node_id,
                                curr_possible.node_id,
                                "primary_stroke",
                                secondary_theme,
                            )
                        else:
                            graph.connect_with_double_arrow(
                                prev_possible.node_id, curr_possible.node_id, "secondary_stroke"
                            )

                    elif (
                        prev_possible.function == "SUBDOMINANT"
                        and curr_possible.function == "TONIC"
                    ):
                        # Determine which secondary theme to use based on target tonality
                        target_tonality_for_plagal: Optional[str] = None

                        # Check current possible node for pivot target tonality
                        curr_step = curr_possible.step
                        curr_raw_tonality = (
                            curr_step.raw_tonality_used_in_step or curr_step.tonality_used_in_step
                        )
                        if _is_pivot_modulation(curr_step):
                            target_tonality_for_plagal = _extract_pivot_target_tonality(curr_step)
                        elif curr_raw_tonality and curr_raw_tonality in secondary_themes:
                            target_tonality_for_plagal = curr_raw_tonality

                        # Fallback to previous possible node
                        if not target_tonality_for_plagal:
                            prev_step = prev_possible.step
                            prev_raw_tonality = (
                                prev_step.raw_tonality_used_in_step
                                or prev_step.tonality_used_in_step
                            )
                            if _is_pivot_modulation(prev_step):
                                target_tonality_for_plagal = _extract_pivot_target_tonality(
                                    prev_step
                                )
                            elif prev_raw_tonality and prev_raw_tonality in secondary_themes:
                                target_tonality_for_plagal = prev_raw_tonality

                        if (
                            target_tonality_for_plagal
                            and target_tonality_for_plagal in secondary_themes
                        ):
                            secondary_theme = secondary_themes[target_tonality_for_plagal]
                            graph.connect_with_single_arrow(
                                prev_possible.node_id,
                                curr_possible.node_id,
                                "primary_stroke",
                                secondary_theme,
                            )
                        else:
                            graph.connect_with_single_arrow(
                                prev_possible.node_id, curr_possible.node_id, "secondary_stroke"
                            )

        # 3. Build the invisible chain for horizontal layout and Render
        main_ids = [n.node_id for n in main_world_nodes if n]
        graph.build_progression_chain(main_ids)

        return graph.render(output_filename)

    def get_graph_dot_source(
        self, analysis_data: ProgressionAnalysisResponse, theme_mode: ThemeMode = "light"
    ) -> str:
        """Get the DOT source code for testing purposes."""
        if not analysis_data.is_tonal_progression:
            raise ValueError(T("errors.cannot_visualize_non_tonal"))

        tonality_name = analysis_data.identified_tonality
        if tonality_name is None:
            raise ValueError(T("errors.cannot_visualize_no_tonality"))

        # Get the raw (untranslated) tonality name for comparisons
        raw_tonality_name = None
        for step in analysis_data.explanation_details:
            if step.raw_tonality_used_in_step:
                raw_tonality_name = step.raw_tonality_used_in_step
                break

        # Fallback if no raw tonality found
        if raw_tonality_name is None:
            raw_tonality_name = tonality_name

        theme = get_theme_for_tonality(raw_tonality_name, theme_mode)
        graph = HarmonicGraph(theme=theme, temp_dir=TEMP_IMAGE_DIR)

        # Identify secondary tonalities used in the progression (same logic as create_graph_from_analysis)
        secondary_tonalities = set()
        for step in analysis_data.explanation_details:
            # Regular secondary tonalities
            raw_tonality = step.raw_tonality_used_in_step or step.tonality_used_in_step
            if raw_tonality and raw_tonality != raw_tonality_name:
                secondary_tonalities.add(raw_tonality)

            # Pivot target tonalities
            if _is_pivot_modulation(step):
                target_tonality = _extract_pivot_target_tonality(step)
                if target_tonality and target_tonality != raw_tonality_name:
                    secondary_tonalities.add(target_tonality)

        # Create themes for secondary tonalities
        secondary_themes = {}
        for secondary_tonality in secondary_tonalities:
            secondary_themes[secondary_tonality] = get_theme_for_tonality(
                secondary_tonality, theme_mode
            )

        function_to_shape = {"TONIC": "house", "DOMINANT": "circle", "SUBDOMINANT": "cds"}

        # Determine the style for primary chords based on the tonality mode
        is_minor_tonality = "minor" in tonality_name.lower()
        primary_style_variant = "dashed_filled" if is_minor_tonality else "solid_filled"

        relevant_steps = [
            step for step in analysis_data.explanation_details if step.processed_chord
        ]
        relevant_steps.reverse()

        main_world_nodes: List[Optional[NodeInfo]] = []
        possible_world_nodes: List[Optional[NodeInfo]] = [None] * len(relevant_steps)

        # 1. FIRST PASS: Classify and create nodes for each world (same logic as create_graph_from_analysis)
        for i, step in enumerate(relevant_steps):
            chord = step.processed_chord
            if chord is None:
                continue

            # Convert ASCII symbols to Unicode musical symbols for display
            chord_display = to_unicode_symbols(chord)

            function = "TONIC"
            if step.tonal_function:
                # Use the structured non-translated function field
                function = step.tonal_function
            elif step.evaluated_functional_state:
                # Fallback: Extract function from translated string
                function = step.evaluated_functional_state.split(" ")[0]

            shape = function_to_shape.get(function, "circle")
            raw_tonality = step.raw_tonality_used_in_step or step.tonality_used_in_step
            is_primary = raw_tonality is not None and raw_tonality == raw_tonality_name
            is_pivot = _is_pivot_modulation(step)

            main_node = NodeInfo(f"{chord}_main_{i}", chord_display, function, shape, step)
            main_world_nodes.append(main_node)
            if is_primary:
                # Apply the style determined by the tonality's mode
                graph.add_primary_chord(
                    main_node.node_id,
                    main_node.chord,
                    shape=main_node.shape,
                    style_variant=primary_style_variant,
                )
            else:
                # Non-diatonic chords - use the correct theme for secondary tonality
                target_tonality = None
                if is_pivot:
                    # For pivots, extract the target tonality from structured data
                    target_tonality = _extract_pivot_target_tonality(step)
                elif raw_tonality and raw_tonality != raw_tonality_name:
                    # For regular secondary chords, use the raw tonality from the step
                    target_tonality = raw_tonality

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        main_node.node_id,
                        main_node.chord,
                        secondary_theme,
                        shape=main_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )
                else:
                    # Fallback to original placeholder chord method
                    graph.add_placeholder_chord(
                        main_node.node_id,
                        main_node.chord,
                        shape=main_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )

            if not is_primary or is_pivot:
                secondary_function = "TONIC" if is_pivot else function
                secondary_shape = function_to_shape.get(secondary_function, "circle")
                possible_node = NodeInfo(
                    f"{chord}_possible_{i}",
                    chord_display,
                    secondary_function,
                    secondary_shape,
                    step,
                )
                possible_world_nodes[i] = possible_node

                # Use the correct theme for secondary tonality
                target_tonality = None
                if is_pivot:
                    # For pivots, extract the target tonality from structured data
                    target_tonality = _extract_pivot_target_tonality(step)
                elif raw_tonality and raw_tonality != raw_tonality_name:
                    # For regular secondary chords, use the raw tonality from the step
                    target_tonality = raw_tonality

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        possible_node.node_id,
                        possible_node.chord,
                        secondary_theme,
                        shape=possible_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )
                else:
                    # Fallback to original secondary chord method
                    graph.add_secondary_chord(
                        possible_node.node_id,
                        possible_node.chord,
                        shape=possible_node.shape,
                        style_variant=_get_secondary_style_variant(target_tonality),
                    )

        # Build the invisible chain for horizontal layout
        main_ids = [n.node_id for n in main_world_nodes if n]
        graph.build_progression_chain(main_ids)

        return graph.get_dot_source()
