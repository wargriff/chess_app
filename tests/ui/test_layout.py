"""Tests layout responsive / breakpoints."""

from src.ui.layout import Breakpoint, UILayout


def test_breakpoints_and_square_board():
    cases = [
        (1920, 1080, Breakpoint.XL, True, True),
        (1600, 900, Breakpoint.LG, True, True),
        (1366, 768, Breakpoint.MD, True, False),
        (1024, 768, Breakpoint.SM, False, False),
        (800, 600, Breakpoint.XS, False, False),
    ]
    for w, h, bp, left, right in cases:
        layout = UILayout()
        layout.resize(w, h)
        assert layout.breakpoint == bp
        assert layout.board_pixel_size % 8 == 0
        ox, oy = layout.board_origin()
        assert ox >= 0 and oy >= 0
        assert ox + layout.board_pixel_size <= w + 4
        assert (layout.left_panel_rect() is not None) == left
        assert (layout.right_panel_rect() is not None) == right


def test_brand_title_adapts():
    layout = UILayout()
    layout.resize(800, 600)
    assert layout.brand_title() == "D4"
    layout.resize(1000, 700)
    assert layout.brand_title() == "Chess Pro"
    layout.resize(1440, 900)
    assert layout.brand_title() == "Chess Pro D4"


def test_essential_actions_only_on_partie():
    layout = UILayout()
    layout.active_nav = "partie"
    assert set(layout.control_buttons()) == {"Nouvelle partie", "Annuler", "Refaire"}
    layout.active_nav = "analyse"
    assert layout.control_buttons() == {}
