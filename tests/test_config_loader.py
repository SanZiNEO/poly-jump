"""配置文件加载测试。"""

from __future__ import annotations

from pathlib import Path

from backend.game.config_loader import load_config
from backend.game.game_state import GameState

ROOT = Path(__file__).resolve().parent.parent


def test_load_a_config_and_create_game():
    cfg = load_config(ROOT / "configs" / "a_2p_6dir.json")
    assert cfg.geometry == "A"
    assert cfg.players == 2

    state = GameState(cfg)
    assert len(state.board.pieces) == 40


def test_load_b_config_and_create_game():
    cfg = load_config(ROOT / "configs" / "b_6p_radius6.json")
    assert cfg.geometry == "B"
    assert cfg.b_radius == 6
    assert cfg.players == 6

    state = GameState(cfg)
    assert len(state.board.points) == 231
    assert len(state.board.pieces) == 84


def test_load_c_config_and_create_game():
    cfg = load_config(ROOT / "configs" / "c_6p_radius6.json")
    assert cfg.geometry == "C"
    assert cfg.c_radius == 6
    assert cfg.players == 6

    state = GameState(cfg)
    assert len(state.board.points) == 377
    assert len(state.board.pieces) == 6 * 19
