"""Tests for v1.5 patch: SVG and TikZ Penrose renderers.

The v1.5 patch implements ``render_svg`` and ``render_tikz`` in
``spacetime_lab.diagrams.render`` (Phase 2 left them as stubs that
raised ``NotImplementedError``).  Both are pure-string renderers
sharing the same kind-to-style mapping with each other and with the
already-shipped matplotlib backend.

Tests are pinned to structural invariants of the output:

1. Output is non-empty and has the expected envelope (``<svg>...</svg>``
   or ``\\begin{tikzpicture}...\\end{tikzpicture}``).
2. Every Path's ``kind`` produces a corresponding marker in output
   (an ``<g class="kind-{kind}">`` for SVG or a ``% --- {kind} ---``
   comment for TikZ).
3. Every named Infinity produces exactly one label entry (one
   ``<text>`` for SVG, one ``\\node`` for TikZ).
4. The ``standalone=True`` TikZ output starts with the standalone
   document preamble and ends with ``\\end{document}``.
5. The kind-to-style table is the same as the one used by
   ``render_matplotlib`` (boundary solid, horizon dashed, etc.).
6. SVG output is well-formed XML (parseable by xml.etree).
7. Empty scene yields a valid placeholder, not a crash.
"""

import xml.etree.ElementTree as ET

import pytest

from spacetime_lab.diagrams import (
    MinkowskiPenrose,
    SchwarzschildPenrose,
    Path,
    PathStyle,
    Scene,
    Vec2,
)
from spacetime_lab.diagrams.render import render_svg, render_tikz


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def minkowski_scene() -> Scene:
    return MinkowskiPenrose().to_scene()


@pytest.fixture
def schwarzschild_scene() -> Scene:
    return SchwarzschildPenrose(mass=1.0).to_scene()


# ─────────────────────────────────────────────────────────────────────
# render_svg
# ─────────────────────────────────────────────────────────────────────


class TestRenderSVGStructure:
    def test_envelope(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")

    def test_xml_well_formed_minkowski(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        # Should parse without raising
        ET.fromstring(svg)

    def test_xml_well_formed_schwarzschild(self, schwarzschild_scene):
        svg = render_svg(schwarzschild_scene)
        ET.fromstring(svg)

    def test_includes_title(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        assert "<title>" in svg
        assert "Minkowski" in svg

    def test_canvas_size_respected(self, minkowski_scene):
        svg = render_svg(minkowski_scene, width=800, height=600)
        assert 'width="800"' in svg
        assert 'height="600"' in svg

    def test_kind_groups_present_minkowski(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        # Minkowski has only boundaries
        assert 'class="kind-boundary"' in svg

    def test_kind_groups_present_schwarzschild(self, schwarzschild_scene):
        svg = render_svg(schwarzschild_scene)
        # Schwarzschild has boundaries, horizons, singularities
        assert 'class="kind-boundary"' in svg
        assert 'class="kind-horizon"' in svg
        assert 'class="kind-singularity"' in svg

    def test_horizon_is_dashed(self, schwarzschild_scene):
        svg = render_svg(schwarzschild_scene)
        # Horizons must have stroke-dasharray attribute
        # Find the horizon group and check it contains dasharray
        horizon_start = svg.index('class="kind-horizon"')
        horizon_end = svg.index("</g>", horizon_start)
        assert "stroke-dasharray" in svg[horizon_start:horizon_end]

    def test_boundary_is_solid(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        boundary_start = svg.index('class="kind-boundary"')
        boundary_end = svg.index("</g>", boundary_start)
        # Solid paths should NOT have dasharray
        assert "stroke-dasharray" not in svg[boundary_start:boundary_end]

    def test_one_text_per_infinity(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        n_text = svg.count("<text ")
        assert n_text == len(minkowski_scene.infinities)

    def test_no_labels_when_disabled(self, minkowski_scene):
        svg = render_svg(minkowski_scene, show_labels=False)
        assert "<text " not in svg

    def test_invalid_canvas_raises(self, minkowski_scene):
        with pytest.raises(ValueError):
            render_svg(minkowski_scene, width=0)
        with pytest.raises(ValueError):
            render_svg(minkowski_scene, height=-100)
        with pytest.raises(ValueError):
            render_svg(minkowski_scene, padding=-5)

    def test_empty_scene_does_not_crash(self):
        empty = Scene(name="empty")
        svg = render_svg(empty)
        # Should be a valid SVG even with no content
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")
        ET.fromstring(svg)

    def test_pathstyle_stroke_override(self):
        # A custom PathStyle stroke should override the kind default.
        scene = Scene(name="custom")
        scene.add(
            Path(
                points=(Vec2(0.0, 0.0), Vec2(1.0, 1.0)),
                style=PathStyle(stroke="#abcdef", width=3.0),
                kind="boundary",
            )
        )
        svg = render_svg(scene)
        assert "#abcdef" in svg
        assert 'stroke-width="3"' in svg


# ─────────────────────────────────────────────────────────────────────
# render_tikz
# ─────────────────────────────────────────────────────────────────────


class TestRenderTikzStructure:
    def test_envelope(self, minkowski_scene):
        tz = render_tikz(minkowski_scene)
        assert r"\begin{tikzpicture}" in tz
        assert tz.rstrip().endswith(r"\end{tikzpicture}")

    def test_no_standalone_preamble_by_default(self, minkowski_scene):
        tz = render_tikz(minkowski_scene)
        assert r"\documentclass" not in tz
        assert r"\begin{document}" not in tz

    def test_standalone_envelope(self, minkowski_scene):
        tz = render_tikz(minkowski_scene, standalone=True)
        assert tz.startswith(r"\documentclass")
        assert r"\usepackage{tikz}" in tz
        assert r"\usepackage{mathrsfs}" in tz
        assert r"\begin{document}" in tz
        assert tz.rstrip().endswith(r"\end{document}")

    def test_scale_option_emitted(self, minkowski_scene):
        tz = render_tikz(minkowski_scene, scale=4.5)
        assert "scale=4.5" in tz

    def test_invalid_scale_raises(self, minkowski_scene):
        with pytest.raises(ValueError, match="scale"):
            render_tikz(minkowski_scene, scale=0.0)
        with pytest.raises(ValueError, match="scale"):
            render_tikz(minkowski_scene, scale=-1.0)

    def test_kind_section_comments_present(self, schwarzschild_scene):
        tz = render_tikz(schwarzschild_scene)
        assert "% --- boundary ---" in tz
        assert "% --- horizon ---" in tz
        assert "% --- singularity ---" in tz

    def test_horizon_uses_dashed_style(self, schwarzschild_scene):
        tz = render_tikz(schwarzschild_scene)
        # Find the horizon section and confirm the dashed style appears
        idx = tz.index("% --- horizon ---")
        nxt_section = tz.find("% ---", idx + 1)
        section = tz[idx:nxt_section if nxt_section != -1 else len(tz)]
        assert "dashed" in section

    def test_one_node_per_infinity(self, minkowski_scene):
        tz = render_tikz(minkowski_scene)
        n_nodes = tz.count(r"\node ")
        assert n_nodes == len(minkowski_scene.infinities)

    def test_no_labels_when_disabled(self, minkowski_scene):
        tz = render_tikz(minkowski_scene, show_labels=False)
        assert r"\node " not in tz

    def test_infinity_latex_symbols(self, minkowski_scene):
        tz = render_tikz(minkowski_scene)
        # Minkowski has all five infinity types
        for symbol_latex in [
            r"$i^{+}$",
            r"$i^{-}$",
            r"$i^{0}$",
            r"$\mathscr{I}^{+}$",
            r"$\mathscr{I}^{-}$",
        ]:
            assert symbol_latex in tz

    def test_draw_command_format(self, minkowski_scene):
        tz = render_tikz(minkowski_scene)
        # Each \draw should look like \draw[opts] (X,T) -- (X,T) ... ;
        assert tz.count(r"\draw[") == len(minkowski_scene.paths)
        assert " -- " in tz

    def test_pathstyle_stroke_override(self):
        scene = Scene(name="custom")
        scene.add(
            Path(
                points=(Vec2(0.0, 0.0), Vec2(1.0, 1.0)),
                style=PathStyle(stroke="#abcdef", width=2.5),
                kind="boundary",
            )
        )
        tz = render_tikz(scene)
        # Hex colour should land as an rgb255 spec
        assert "rgb,255:" in tz
        assert "171" in tz  # 0xab
        assert "205" in tz  # 0xcd
        assert "239" in tz  # 0xef
        assert "line width=2.50pt" in tz


# ─────────────────────────────────────────────────────────────────────
# Cross-renderer consistency
# ─────────────────────────────────────────────────────────────────────


class TestCrossRendererConsistency:
    def test_svg_and_tikz_see_same_paths(self, schwarzschild_scene):
        svg = render_svg(schwarzschild_scene)
        tz = render_tikz(schwarzschild_scene)
        # Each Path emits exactly one <path> in SVG and one \draw in TikZ
        assert svg.count("<path ") == len(schwarzschild_scene.paths)
        assert tz.count(r"\draw[") == len(schwarzschild_scene.paths)

    def test_svg_and_tikz_see_same_infinities(self, minkowski_scene):
        svg = render_svg(minkowski_scene)
        tz = render_tikz(minkowski_scene)
        n_inf = len(minkowski_scene.infinities)
        assert svg.count("<text ") == n_inf
        assert tz.count(r"\node ") == n_inf

    def test_kind_count_matches(self, schwarzschild_scene):
        # Both renderers organise paths by kind in the same z-order.
        svg = render_svg(schwarzschild_scene)
        tz = render_tikz(schwarzschild_scene)
        kinds = {p.kind for p in schwarzschild_scene.paths}
        for kind in kinds:
            assert f'class="kind-{kind}"' in svg
            assert f"% --- {kind} ---" in tz
