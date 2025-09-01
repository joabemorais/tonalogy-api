from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from visualizer.harmonic_graph import HarmonicGraph


class TestHarmonicGraph:
    """Test cases for HarmonicGraph class."""

    @pytest.fixture
    def sample_theme(self) -> Dict[str, Any]:
        """Sample theme for testing."""
        return {
            "primary_fill": "#a5d8ff80",
            "primary_stroke": "#4dabf7",
            "primary_text_color": "#1971c2",
            "secondary_fill": "#ffd8a880",
            "secondary_stroke": "#ffa94d",
            "secondary_text_color": "#e8590c",
            "annotation_gray": "#555555",
        }

    @pytest.fixture
    def alternative_theme(self) -> Dict[str, Any]:
        """Alternative theme for testing secondary tonalities."""
        return {
            "primary_fill": "#ffc9c980",
            "primary_stroke": "#ff8787",
            "primary_text_color": "#e03131",
            "secondary_fill": "#d0ebff80",
            "secondary_stroke": "#74c0fc",
            "secondary_text_color": "#339af0",
            "annotation_gray": "#666666",
        }

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Temporary directory for testing."""
        return tmp_path

    @pytest.fixture
    def harmonic_graph(self, sample_theme: Dict[str, Any], temp_dir: Path) -> HarmonicGraph:
        """Create a HarmonicGraph instance for testing."""
        return HarmonicGraph(theme=sample_theme, temp_dir=temp_dir)

    def test_harmonic_graph_initialization(
        self, sample_theme: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test that HarmonicGraph initializes correctly with theme and temp_dir."""
        graph = HarmonicGraph(theme=sample_theme, temp_dir=temp_dir)

        assert graph.theme == sample_theme
        assert graph.svg_factory is not None
        assert graph.existing_connections == set()

    def test_harmonic_graph_custom_parameters(
        self, sample_theme: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test HarmonicGraph initialization with custom graph parameters."""
        graph = HarmonicGraph(
            theme=sample_theme,
            temp_dir=temp_dir,
            rankdir="TB",
            splines="curved",
            nodesep="1.0",
            ranksep="2.0",
        )

        assert graph.theme == sample_theme

    @patch("visualizer.harmonic_graph.SvgFactory")
    def test_add_primary_chord(
        self, mock_svg_factory: MagicMock, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test adding a primary chord to the graph."""
        # GIVEN
        node_id = "C_main_1"
        label = "C"
        shape = "house"
        style_variant = "solid_filled"

        # WHEN
        harmonic_graph.add_primary_chord(node_id, label, shape, style_variant)

        # THEN
        # The method should not raise any exceptions
        # We can't easily verify the internal _add_image_node call without more complex mocking

    @patch("visualizer.harmonic_graph.SvgFactory")
    def test_add_secondary_chord(
        self, mock_svg_factory: MagicMock, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test adding a secondary chord using default theme."""
        # GIVEN
        node_id = "Dm_possible_1"
        label = "Dm"
        shape = "circle"
        style_variant = "dashed_filled"

        # WHEN
        harmonic_graph.add_secondary_chord(node_id, label, shape, style_variant)

        # THEN
        # The method should not raise any exceptions

    @patch("visualizer.harmonic_graph.SvgFactory")
    def test_add_secondary_chord_with_theme(
        self,
        mock_svg_factory: MagicMock,
        harmonic_graph: HarmonicGraph,
        alternative_theme: Dict[str, Any],
    ) -> None:
        """Test adding a secondary chord with a specific theme."""
        # GIVEN
        node_id = "Em_possible_1"
        label = "Em"
        shape = "house"
        style_variant = "dashed_filled"

        # WHEN
        harmonic_graph.add_secondary_chord_with_theme(
            node_id, label, alternative_theme, shape, style_variant
        )

        # THEN
        # The method should not raise any exceptions

    @patch("visualizer.harmonic_graph.SvgFactory")
    def test_add_placeholder_chord(
        self, mock_svg_factory: MagicMock, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test adding a placeholder chord to the graph."""
        # GIVEN
        node_id = "F_main_1"
        label = "F"
        shape = "cds"
        style_variant = "dashed_filled"

        # WHEN
        harmonic_graph.add_placeholder_chord(node_id, label, shape, style_variant)

        # THEN
        # The method should not raise any exceptions

    def test_connect_nodes(self, harmonic_graph: HarmonicGraph) -> None:
        """Test connecting two nodes with default parameters."""
        # GIVEN
        from_node = "C_main_1"
        to_node = "G_main_2"

        # WHEN
        harmonic_graph.connect_nodes(from_node, to_node)

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_nodes_with_parameters(self, harmonic_graph: HarmonicGraph) -> None:
        """Test connecting nodes with custom parameters."""
        # GIVEN
        from_node = "F_main_1"
        to_node = "G_main_2"

        # WHEN
        harmonic_graph.connect_nodes(
            from_node, to_node, style="dashed", color="#ff0000", penwidth="2"
        )

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_with_double_arrow_default_theme(self, harmonic_graph: HarmonicGraph) -> None:
        """Test connecting nodes with double arrow using default theme."""
        # GIVEN
        from_node = "G_main_1"
        to_node = "C_main_2"
        color_key = "primary_stroke"

        # WHEN
        harmonic_graph.connect_with_double_arrow(from_node, to_node, color_key)

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_with_double_arrow_custom_theme(
        self, harmonic_graph: HarmonicGraph, alternative_theme: Dict[str, Any]
    ) -> None:
        """Test connecting nodes with double arrow using custom theme."""
        # GIVEN
        from_node = "B_possible_1"
        to_node = "Em_possible_2"
        color_key = "primary_stroke"

        # WHEN
        harmonic_graph.connect_with_double_arrow(from_node, to_node, color_key, alternative_theme)

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_with_double_arrow_missing_color_key(
        self, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test that missing color key raises ValueError."""
        # GIVEN
        from_node = "C_main_1"
        to_node = "G_main_2"
        invalid_color_key = "nonexistent_color"

        # WHEN & THEN
        with pytest.raises(ValueError, match="Color key 'nonexistent_color' not found in theme"):
            harmonic_graph.connect_with_double_arrow(from_node, to_node, invalid_color_key)

    def test_connect_with_single_arrow_default_theme(self, harmonic_graph: HarmonicGraph) -> None:
        """Test connecting nodes with single arrow using default theme."""
        # GIVEN
        from_node = "F_main_1"
        to_node = "C_main_2"
        color_key = "primary_stroke"

        # WHEN
        harmonic_graph.connect_with_single_arrow(from_node, to_node, color_key)

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_with_single_arrow_custom_theme(
        self, harmonic_graph: HarmonicGraph, alternative_theme: Dict[str, Any]
    ) -> None:
        """Test connecting nodes with single arrow using custom theme."""
        # GIVEN
        from_node = "Bb_possible_1"
        to_node = "F_possible_2"
        color_key = "primary_stroke"

        # WHEN
        harmonic_graph.connect_with_single_arrow(from_node, to_node, color_key, alternative_theme)

        # THEN
        # Verify connection was recorded
        expected_connection = tuple(sorted((from_node, to_node)))
        assert expected_connection in harmonic_graph.existing_connections

    def test_connect_with_single_arrow_missing_color_key(
        self, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test that missing color key raises ValueError."""
        # GIVEN
        from_node = "F_main_1"
        to_node = "C_main_2"
        invalid_color_key = "nonexistent_color"

        # WHEN & THEN
        with pytest.raises(ValueError, match="Color key 'nonexistent_color' not found in theme"):
            harmonic_graph.connect_with_single_arrow(from_node, to_node, invalid_color_key)

    def test_align_nodes_in_ranks_single_rank(self, harmonic_graph: HarmonicGraph) -> None:
        """Test aligning nodes in a single rank."""
        # GIVEN
        nodes = ["C_main_1", "C_possible_1"]

        # WHEN
        harmonic_graph.align_nodes_in_ranks(nodes)

        # THEN
        # Should not raise any exceptions
        # The actual graphviz body modification is hard to test without examining internals

    def test_align_nodes_in_ranks_multiple_ranks(self, harmonic_graph: HarmonicGraph) -> None:
        """Test aligning nodes in multiple ranks."""
        # GIVEN
        rank1 = ["C_main_1", "C_possible_1"]
        rank2 = ["G_main_2", "G_possible_2"]

        # WHEN
        harmonic_graph.align_nodes_in_ranks(rank1, rank2)

        # THEN
        # Should not raise any exceptions

    def test_align_nodes_in_ranks_empty_rank(self, harmonic_graph: HarmonicGraph) -> None:
        """Test aligning nodes with empty ranks."""
        # GIVEN
        rank1 = ["C_main_1"]
        rank2: list[str] = []  # Empty rank

        # WHEN
        harmonic_graph.align_nodes_in_ranks(rank1, rank2)

        # THEN
        # Should not raise any exceptions

    def test_build_progression_chain_single_node(self, harmonic_graph: HarmonicGraph) -> None:
        """Test building progression chain with single node."""
        # GIVEN
        node_ids = ["C_main_1"]

        # WHEN
        harmonic_graph.build_progression_chain(node_ids)

        # THEN
        # Should not raise any exceptions and not create any connections
        assert len(harmonic_graph.existing_connections) == 0

    def test_build_progression_chain_multiple_nodes(self, harmonic_graph: HarmonicGraph) -> None:
        """Test building progression chain with multiple nodes."""
        # GIVEN
        node_ids = ["C_main_1", "G_main_2", "F_main_3"]

        # WHEN
        harmonic_graph.build_progression_chain(node_ids)

        # THEN
        # Should create invisible connections between consecutive nodes
        assert len(harmonic_graph.existing_connections) == 2
        assert ("C_main_1", "G_main_2") in harmonic_graph.existing_connections
        assert ("F_main_3", "G_main_2") in harmonic_graph.existing_connections

    def test_build_progression_chain_empty_list(self, harmonic_graph: HarmonicGraph) -> None:
        """Test building progression chain with empty node list."""
        # GIVEN
        node_ids: list[str] = []

        # WHEN
        harmonic_graph.build_progression_chain(node_ids)

        # THEN
        # Should not raise any exceptions
        assert len(harmonic_graph.existing_connections) == 0

    @patch("visualizer.harmonic_graph.SvgFactory")
    def test_render_calls_svg_factory(
        self, mock_svg_factory_class: MagicMock, harmonic_graph: HarmonicGraph
    ) -> None:
        """Test that render method calls svg_factory appropriately."""
        # GIVEN
        mock_svg_factory_instance = MagicMock()
        mock_svg_factory_class.return_value = mock_svg_factory_instance

        # Recreate harmonic_graph to use the mocked SvgFactory
        harmonic_graph = HarmonicGraph(theme=harmonic_graph.theme, temp_dir=Path("/tmp"))

        output_filename = Path("/fake/output/path")

        # WHEN
        with patch.object(harmonic_graph.dot, "render") as mock_render:
            # The render method adds .png extension, so mock accordingly
            mock_render.return_value = str(output_filename) + ".png"
            result = harmonic_graph.render(output_filename)

        # THEN
        assert result == str(output_filename) + ".png"
        mock_render.assert_called_once()

    def test_existing_connections_tracking(self, harmonic_graph: HarmonicGraph) -> None:
        """Test that existing connections are properly tracked."""
        # GIVEN
        connections = [
            ("C_main_1", "G_main_2"),
            ("G_main_2", "F_main_3"),
            ("F_main_3", "C_main_1"),  # This should create a different tuple due to sorting
        ]

        # WHEN
        for from_node, to_node in connections:
            harmonic_graph.connect_nodes(from_node, to_node)

        # THEN
        assert len(harmonic_graph.existing_connections) == 3
        # Verify that connections are stored in sorted order
        assert ("C_main_1", "G_main_2") in harmonic_graph.existing_connections
        assert ("F_main_3", "G_main_2") in harmonic_graph.existing_connections
        assert ("C_main_1", "F_main_3") in harmonic_graph.existing_connections

    def test_theme_color_access(self, sample_theme: Dict[str, Any], temp_dir: Path) -> None:
        """Test that theme colors are properly accessible."""
        # GIVEN
        graph = HarmonicGraph(theme=sample_theme, temp_dir=temp_dir)

        # WHEN & THEN
        assert graph.theme["primary_stroke"] == "#4dabf7"
        assert graph.theme["secondary_fill"] == "#ffd8a880"
        assert graph.theme.get("nonexistent_key") is None
