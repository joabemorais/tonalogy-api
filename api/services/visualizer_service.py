import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from core.domain.models import to_unicode_symbols
from visualizer.harmonic_graph import HarmonicGraph
from visualizer.theming import get_theme_for_tonality

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


class VisualizerService:
    def _extract_pivot_target_tonality(self, observation: str) -> Optional[str]:
        """Extract the target tonality from a pivot modulation observation."""
        match = re.search(r"becomes the new TONIC in '([^']+)'", observation)
        return match.group(1) if match else None

    def create_graph_from_analysis(self, analysis_data: ProgressionAnalysisResponse) -> str:
        if not analysis_data.is_tonal_progression:
            raise ValueError("Cannot visualize a non-tonal progression.")

        tonality_name = analysis_data.identified_tonality
        if tonality_name is None:
            raise ValueError("Cannot visualize a progression without an identified tonality.")

        theme = get_theme_for_tonality(tonality_name)
        output_filename = TEMP_IMAGE_DIR / str(uuid.uuid4())
        graph = HarmonicGraph(theme=theme, temp_dir=TEMP_IMAGE_DIR)

        # Identify secondary tonalities used in the progression
        secondary_tonalities = set()
        for step in analysis_data.explanation_details:
            # Regular secondary tonalities
            if step.tonality_used_in_step and step.tonality_used_in_step != tonality_name:
                secondary_tonalities.add(step.tonality_used_in_step)

            # Pivot target tonalities
            if (
                step.formal_rule_applied
                and "Pivot" in step.formal_rule_applied
                and step.observation
            ):
                target_tonality = self._extract_pivot_target_tonality(step.observation)
                if target_tonality and target_tonality != tonality_name:
                    secondary_tonalities.add(target_tonality)

        # Create themes for secondary tonalities
        secondary_themes = {}
        for secondary_tonality in secondary_tonalities:
            secondary_themes[secondary_tonality] = get_theme_for_tonality(secondary_tonality)

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
            if step.evaluated_functional_state:
                # Extract function from strings like "TONIC (s_t)", "DOMINANT (s_d)", etc.
                function = step.evaluated_functional_state.split(" ")[0]

            shape = function_to_shape.get(function, "circle")
            is_primary = (
                step.tonality_used_in_step is not None
                and step.tonality_used_in_step == tonality_name
            )
            is_pivot = step.formal_rule_applied and "Pivot" in step.formal_rule_applied

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
                if is_pivot and step.observation:
                    # For pivots, extract the target tonality from the observation
                    target_tonality = self._extract_pivot_target_tonality(step.observation)
                elif step.tonality_used_in_step and step.tonality_used_in_step != tonality_name:
                    # For regular secondary chords, use the tonality from the step
                    target_tonality = step.tonality_used_in_step

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        main_node.node_id,
                        main_node.chord,
                        secondary_theme,
                        shape=main_node.shape,
                        style_variant="dashed_filled",
                    )
                else:
                    # Fallback to original placeholder chord method
                    graph.add_placeholder_chord(
                        main_node.node_id,
                        main_node.chord,
                        shape=main_node.shape,
                        style_variant="dashed_filled",
                    )

            if not is_primary or is_pivot:
                secondary_function = "TONIC" if is_pivot else function
                secondary_shape = function_to_shape.get(secondary_function, "circle")
                possible_node = NodeInfo(
                    f"{chord}_possible_{i}", chord_display, secondary_function, secondary_shape, step
                )
                possible_world_nodes[i] = possible_node

                # Use the correct theme for secondary tonality
                target_tonality = None
                if is_pivot and step.observation:
                    # For pivots, extract the target tonality from the observation
                    target_tonality = self._extract_pivot_target_tonality(step.observation)
                elif step.tonality_used_in_step and step.tonality_used_in_step != tonality_name:
                    # For regular secondary chords, use the tonality from the step
                    target_tonality = step.tonality_used_in_step

                if target_tonality and target_tonality in secondary_themes:
                    secondary_theme = secondary_themes[target_tonality]
                    graph.add_secondary_chord_with_theme(
                        possible_node.node_id,
                        possible_node.chord,
                        secondary_theme,
                        shape=possible_node.shape,
                        style_variant="dashed_filled",
                    )
                else:
                    # Fallback to original secondary chord method
                    graph.add_secondary_chord(
                        possible_node.node_id,
                        possible_node.chord,
                        shape=possible_node.shape,
                        style_variant="dashed_filled",
                    )

        # 2. SECOND PASS: Connect and align the nodes
        for i in range(len(main_world_nodes)):
            current_main_node: Optional[NodeInfo] = main_world_nodes[i]
            current_possible_node: Optional[NodeInfo] = possible_world_nodes[i]

            if current_main_node and current_possible_node:
                graph.align_nodes_in_ranks(
                    [current_main_node.node_id, current_possible_node.node_id]
                )
                color = (
                    theme["secondary_stroke"]
                    if current_main_node.step.formal_rule_applied is None
                    or "Pivot" not in current_main_node.step.formal_rule_applied
                    else theme["annotation_gray"]
                )
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
                    and prev_main.step.tonality_used_in_step == tonality_name
                    and curr_main.step.tonality_used_in_step == tonality_name
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
                        secondary_tonality = None

                        # Check current possible node for pivot target tonality
                        curr_step = curr_possible.step
                        if (
                            curr_step.formal_rule_applied
                            and "Pivot" in curr_step.formal_rule_applied
                            and curr_step.observation
                        ):
                            secondary_tonality = self._extract_pivot_target_tonality(
                                curr_step.observation
                            )
                        elif (
                            curr_step.tonality_used_in_step
                            and curr_step.tonality_used_in_step in secondary_themes
                        ):
                            secondary_tonality = curr_step.tonality_used_in_step

                        # Fallback to previous possible node
                        if not secondary_tonality:
                            prev_step = prev_possible.step
                            if (
                                prev_step.formal_rule_applied
                                and "Pivot" in prev_step.formal_rule_applied
                                and prev_step.observation
                            ):
                                secondary_tonality = self._extract_pivot_target_tonality(
                                    prev_step.observation
                                )
                            elif (
                                prev_step.tonality_used_in_step
                                and prev_step.tonality_used_in_step in secondary_themes
                            ):
                                secondary_tonality = prev_step.tonality_used_in_step

                        if secondary_tonality and secondary_tonality in secondary_themes:
                            secondary_theme = secondary_themes[secondary_tonality]
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
                    
                    elif prev_possible.function == "SUBDOMINANT" and curr_possible.function == "TONIC":
                        # Determine which secondary theme to use based on target tonality
                        secondary_tonality = None

                        # Check current possible node for pivot target tonality
                        curr_step = curr_possible.step
                        if (
                            curr_step.formal_rule_applied
                            and "Pivot" in curr_step.formal_rule_applied
                            and curr_step.observation
                        ):
                            secondary_tonality = self._extract_pivot_target_tonality(
                                curr_step.observation
                            )
                        elif (
                            curr_step.tonality_used_in_step
                            and curr_step.tonality_used_in_step in secondary_themes
                        ):
                            secondary_tonality = curr_step.tonality_used_in_step

                        # Fallback to previous possible node
                        if not secondary_tonality:
                            prev_step = prev_possible.step
                            if (
                                prev_step.formal_rule_applied
                                and "Pivot" in prev_step.formal_rule_applied
                                and prev_step.observation
                            ):
                                secondary_tonality = self._extract_pivot_target_tonality(
                                    prev_step.observation
                                )
                            elif (
                                prev_step.tonality_used_in_step
                                and prev_step.tonality_used_in_step in secondary_themes
                            ):
                                secondary_tonality = prev_step.tonality_used_in_step

                        if secondary_tonality and secondary_tonality in secondary_themes:
                            secondary_theme = secondary_themes[secondary_tonality]
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

    def get_graph_dot_source(self, analysis_data: ProgressionAnalysisResponse) -> str:
        """Get the DOT source code for testing purposes."""
        if not analysis_data.is_tonal_progression:
            raise ValueError("Cannot visualize a non-tonal progression.")

        tonality_name = analysis_data.identified_tonality
        if tonality_name is None:
            raise ValueError("Cannot visualize a progression without an identified tonality.")

        theme = get_theme_for_tonality(tonality_name)
        graph = HarmonicGraph(theme=theme, temp_dir=TEMP_IMAGE_DIR)

        # Process the analysis the same way as create_graph_from_analysis, but return DOT source
        secondary_tonalities = set()
        for step in analysis_data.explanation_details:
            if step.tonality_used_in_step and step.tonality_used_in_step != tonality_name:
                secondary_tonalities.add(step.tonality_used_in_step)

        secondary_themes: Dict[str, Dict[str, str]] = {}
        for sec_tonality in secondary_tonalities:
            secondary_themes[sec_tonality] = get_theme_for_tonality(sec_tonality)

        function_to_shape = {
            "TONIC": "house",
            "DOMINANT": "circle",
            "SUBDOMINANT": "circle",
        }

        is_minor_tonality = "minor" in tonality_name.lower()
        primary_style_variant = "dashed_filled" if is_minor_tonality else "solid_filled"

        relevant_steps = [
            step for step in analysis_data.explanation_details if step.processed_chord
        ]
        relevant_steps.reverse()

        main_world_nodes: List[Optional[NodeInfo]] = []

        # Process nodes (simplified version)
        for i, step in enumerate(relevant_steps):
            chord = step.processed_chord
            if chord is None:
                continue

            # Convert ASCII symbols to Unicode musical symbols for display
            chord_display = to_unicode_symbols(chord)

            function = "TONIC"
            if step.evaluated_functional_state:
                function = step.evaluated_functional_state.split(" ")[0]

            shape = function_to_shape.get(function, "circle")
            is_primary = (
                step.tonality_used_in_step is not None
                and step.tonality_used_in_step == tonality_name
            )

            main_node = NodeInfo(f"{chord}_main_{i}", chord_display, function, shape, step)
            main_world_nodes.append(main_node)
            
            if is_primary:
                graph.add_primary_chord(
                    main_node.node_id,
                    main_node.chord,
                    shape=main_node.shape,
                    style_variant=primary_style_variant,
                )

        return graph.get_dot_source()
