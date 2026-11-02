import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF  # noqa: E402

from zavero.orchestrator import Orchestrator  # noqa: E402

from test_follow import _overlay  # noqa: E402


def _paint(ov):
    """Lay the bubble out once (buttons get their rects while painting)."""
    from PyQt6.QtGui import QImage, QPainter

    img = QImage(ov.width(), ov.height(), QImage.Format.Format_ARGB32)
    p = QPainter(img)
    ov._t += 5  # past pop-in and typing
    ov._paint_bubble(p)
    p.end()


def test_buttons_per_mood():
    ov = _overlay()
    ov._on_text("Listening…", "listen")
    assert ov._buttons == []                       # live transcript: nothing to click
    ov._on_text("Here is the answer", "info")
    assert ov._buttons == ["close"]                # every other bubble has ✕
    ov._on_text("Pay now?", "hold", ["yes", "no"])
    assert ov._buttons == ["close", "yes", "no"]
    ov._on_text("అక్కడ క్లిక్ చేయండి", "hold", ["do", "next"])
    _paint(ov)
    assert [b for b, _ in ov._btn_rects] == ["close", "do", "next"]
    assert ov._button_label("do") == "నువ్వే చెయ్"  # labels follow the bubble's language


def test_button_hit_and_actions():
    ov = _overlay()
    ov._on_text("Pay now?", "hold", ["yes", "no"])
    _paint(ov)
    clicked = []
    ov.button_clicked.connect(clicked.append)
    yes = dict(ov._btn_rects)["yes"]
    assert ov._button_at(yes.center()) == "yes"
    assert ov._button_at(QPointF(-50, -50)) is None
    ov._on_button("yes")
    ov._on_button("close")
    assert clicked == ["yes", "close"] and ov._text == ""


def test_click_on_button_is_not_an_off_target_guide_click():
    o = Orchestrator.__new__(Orchestrator)
    o._worker = None
    o.mode = "guide"
    o._waiting = True
    o._guide_target = (100, 100)
    o._off_target = False
    o._acted = threading.Event()
    o.ui = type("UI", (), {"is_on_avatar": lambda s, x, y: False, "is_on_bubble_button": lambda s, x, y: True})()
    o._on_click(900, 700, None, True)
    assert not o._acted.is_set() and not o._off_target


def test_yes_button_answers_the_question():
    o = Orchestrator.__new__(Orchestrator)
    o._worker = None
    o._asking, o._answer, o._answered = True, None, threading.Event()
    o.coach = type("NoCoach", (), {"active": False})()
    o._waiting = False
    o.on_button("yes")
    assert o._answer is True and o._answered.is_set()


def test_guide_arrow_snaps_to_the_exact_button(monkeypatch):
    from zavero import driver, talk
    from zavero.brain import Step

    from test_interrupt import FakeUI

    o = Orchestrator.__new__(Orchestrator)
    o.ui, o.user_text, o._waiting, o._guide_token, o._snapped = FakeUI(), "pay bill", True, 7, {}
    shot = driver.Shot("", 1280, 720, 1.5)
    step = Step("c1", [{"type": "click", "x": 400, "y": 300}], text='I will click "Pay Bill".')
    asked = []
    monkeypatch.setattr(talk, "refine_point", lambda s, pt, what: asked.append(what) or {"x": 430, "y": 310})
    o._snap_guide(step, shot, 7)
    assert asked == ["Pay Bill"]                                   # looks for the quoted button
    assert o._guide_target == (645, 465) and o._snapped[7] == (645, 465)
    assert ("point_at", (645, 465)) in o.ui.log                     # the arrow moves to the exact spot
    monkeypatch.setattr(talk, "refine_point", lambda s, pt, what: {"x": 900, "y": 600})
    o._snapped = {}
    o._snap_guide(step, shot, 7)
    assert o._snapped == {}                                         # a far jump is a different button: ignored
