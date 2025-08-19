import graphviz
from pathlib import Path
from .styles import SVG_TEMPLATES
from .svg_factory import SvgFactory

class HarmonicGraph:
    """
    "Builder" class that orchestrates the construction of a harmonic progression diagram.
    """

    def __init__(self, theme: dict, temp_dir: Path, rankdir='LR', splines='line', nodesep='0.8', ranksep='1.5'):
        self.dot = graphviz.Digraph('HarmonicProgression')
        self.dot.attr('graph', rankdir=rankdir, splines=splines, nodesep=nodesep, ranksep=ranksep, bgcolor='transparent')
        self.dot.attr('node', fontname='MuseJazzText', fontsize='22')
        self.dot.attr('edge', fontname='Arial', fontsize='10')
        self.existing_connections = set()
        self.theme = theme 
        self.svg_factory = SvgFactory(temp_dir)

    def _add_image_node(self, node_id, label, shape_name, style_variant, fill, stroke, penwidth='4', fontcolor=None):
        shape_variants = SVG_TEMPLATES.get(shape_name)
        if not shape_variants:
            raise ValueError(f"Shape '{shape_name}' not found in SVG_TEMPLATES.")

        svg_template = shape_variants.get(style_variant)
        if not svg_template:
            raise ValueError(f"Style variant '{style_variant}' not found for shape '{shape_name}'.")

        image_path = self.svg_factory.create_styled_image_file(node_id, svg_template, fill, stroke, penwidth)

        node_kwargs = {
            'label': label, 'image': image_path, 'shape': 'none', 'labelloc': 'c',
            'width': '0.9', 'height': '0.9', 'fixedsize': 'true', 'imagescale': 'true'
        }
        if fontcolor:
            node_kwargs['fontcolor'] = fontcolor

        self.dot.node(node_id, **node_kwargs)


    def add_primary_chord(self, node_id, label, shape='house', style_variant='solid_filled'):
        font_color = self.theme.get('primary_text_color')
        self._add_image_node(node_id, label, shape, style_variant,
                             self.theme['primary_fill'],
                             self.theme['primary_stroke'],
                             fontcolor=font_color)

    def add_secondary_chord(self, node_id, label, shape='circle', style_variant='dashed_filled'):
        font_color = self.theme.get('secondary_text_color')
        self._add_image_node(node_id, label, shape, style_variant,
                             self.theme['secondary_fill'],
                             self.theme['secondary_stroke'],
                             fontcolor=font_color)

    def add_placeholder_chord(self, node_id, label, shape='circle', style_variant='dashed_filled'):
        """Adds a translucent placeholder node in the main world."""
        fill = self.theme.get('secondary_fill', '#FFFFFF80') 
        stroke = self.theme.get('secondary_stroke', '#000000')
        font_color = self.theme.get('secondary_text_color')
        self._add_image_node(node_id, label, shape, style_variant,
                             fill, stroke, fontcolor=font_color)

    def connect_nodes(self, from_node, to_node, **kwargs):
        self.dot.edge(from_node, to_node, **kwargs)
        self.existing_connections.add(tuple(sorted((from_node, to_node))))


    def connect_with_double_arrow(self, from_node, to_node, color_key: str, **kwargs):
        color = self.theme.get(color_key)
        if not color:
            raise ValueError(f"Color key '{color_key}' not found in theme.")
        double_line_color = f"{color}:invis:{color}"
        self.connect_nodes(from_node, to_node, color=double_line_color, penwidth='3', **kwargs)


    def align_nodes_in_ranks(self, *ranks):
        """Aligns nodes in separate ranks (rows)."""
        for rank in ranks:
            if rank:
                nodes_str = '; '.join(f'"{nid}"' for nid in rank)
                self.dot.body.append(f'{{ rank=same; {nodes_str} }}')

    def build_progression_chain(self, node_ids):
        for i in range(len(node_ids) - 1):
            from_node = node_ids[i]
            to_node = node_ids[i+1]
            if tuple(sorted((from_node, to_node))) not in self.existing_connections:
                self.connect_nodes(from_node, to_node, style='invis')


    def render(self, filename: Path) -> str:
        output_path = filename.with_suffix('.png')
        try:
            self.dot.render(str(filename), view=False, cleanup=True, format='png')
            return str(output_path)
        except Exception as e:
            print(f"Error generating graph: {e}")
            raise
        finally:
            self.svg_factory.cleanup_files()
