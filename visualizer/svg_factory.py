import os
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

class SvgFactory:
    """
    Responsible for creating and managing temporary and styled image files.
    Converts SVGs to PNG to ensure compatibility with Graphviz.
    """
    def __init__(self, temp_dir: Path):
        if not CAIROSVG_AVAILABLE:
            warnings.warn(
                "The 'cairosvg' library was not found. Custom SVG shape rendering will fail. "
                "Install it with: pip install cairosvg",
                RuntimeWarning
            )

        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.temp_files = []

    def create_styled_image_file(self, node_id, svg_template, fill, stroke, penwidth='1.5'):
        """
        Takes an SVG template, applies styles, converts to PNG and saves to a temporary file.
        Returns the absolute path of the created PNG file.
        """
        cleaned_template = svg_template.replace('\xa0', ' ').strip()
        root = ET.fromstring(cleaned_template)

        def parse_color_with_alpha(color_string):
            if len(color_string) == 9 and color_string.startswith('#'):
                base_color = color_string[:7]
                alpha_hex = color_string[7:]
                alpha_float = int(alpha_hex, 16) / 255.0
                return base_color, f"{alpha_float:.2f}"
            return color_string, "1.0"

        fill_color, fill_opacity = parse_color_with_alpha(fill)
        stroke_color, stroke_opacity = parse_color_with_alpha(stroke)

        for elem in root.iter():
            if 'class' in elem.attrib:
                classes = elem.attrib['class'].split()
                if 'shape-fill' in classes:
                    elem.set('fill', fill_color)
                    elem.set('fill-opacity', fill_opacity)
                if 'shape-stroke' in classes:
                    elem.set('stroke', stroke_color)
                    elem.set('stroke-opacity', stroke_opacity)
                    elem.set('stroke-width', str(penwidth))
        
        svg_string_styled = ET.tostring(root, encoding='unicode')

            raise RuntimeError("The 'cairosvg' library is not installed, cannot convert SVG to PNG.")
            
        png_data = cairosvg.svg2png(bytestring=svg_string_styled.encode('utf-8'))

        filepath = self.temp_dir / f"temp_img_{node_id}.png"
        with open(filepath, 'wb') as f:
            f.write(png_data)

        self.temp_files.append(filepath)
        return str(filepath.resolve())

    def cleanup_files(self):
        """Removes all temporary files created by the factory."""
        for f in self.temp_files:
            if os.path.exists(f):
                os.remove(f)
