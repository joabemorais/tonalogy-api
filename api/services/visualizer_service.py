import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
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
    def create_graph_from_analysis(self, analysis_data: ProgressionAnalysisResponse) -> str:
        if not analysis_data.is_tonal_progression:
            raise ValueError("Cannot visualize a non-tonal progression.")

        tonality_name = analysis_data.identified_tonality
        theme = get_theme_for_tonality(tonality_name)
        output_filename = TEMP_IMAGE_DIR / str(uuid.uuid4())
        graph = HarmonicGraph(theme=theme, temp_dir=TEMP_IMAGE_DIR)

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
            function = "TONIC"
            if step.evaluated_functional_state:
                function = step.evaluated_functional_state.split(" ")[0]

            shape = function_to_shape.get(function, "circle")
            is_primary = step.tonality_used_in_step == tonality_name
            is_pivot = "Pivot" in step.formal_rule_applied

            main_node = NodeInfo(f"{chord}_main_{i}", chord, function, shape, step)
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
                # Non-diatonic chords are always dashed
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
                    f"{chord}_possible_{i}", chord, secondary_function, secondary_shape, step
                )
                possible_world_nodes[i] = possible_node
                # Secondary chords are always dashed
                graph.add_secondary_chord(
                    possible_node.node_id,
                    possible_node.chord,
                    shape=possible_node.shape,
                    style_variant="dashed_filled",
                )

        # 2. SECOND PASS: Connect and align the nodes
        for i in range(len(main_world_nodes)):
            main_node = main_world_nodes[i]
            possible_node = possible_world_nodes[i]

            if main_node and possible_node:
                graph.align_nodes_in_ranks([main_node.node_id, possible_node.node_id])
                color = (
                    theme["secondary_stroke"]
                    if "Pivot" not in main_node.step.formal_rule_applied
                    else theme["annotation_gray"]
                )
                graph.connect_nodes(
                    main_node.node_id,
                    possible_node.node_id,
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

                prev_possible = possible_world_nodes[i - 1]
                curr_possible = possible_world_nodes[i]
                if prev_possible and curr_possible:
                    if prev_possible.function == "DOMINANT" and curr_possible.function == "TONIC":
                        graph.connect_with_double_arrow(
                            prev_possible.node_id, curr_possible.node_id, "secondary_stroke"
                        )

        # 3. Build the invisible chain for horizontal layout and Render
        main_ids = [n.node_id for n in main_world_nodes if n]
        graph.build_progression_chain(main_ids)

        return graph.render(output_filename)
