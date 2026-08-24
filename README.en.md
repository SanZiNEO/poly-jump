# PolyJump

A configurable 3D jump-chess game framework with multiple geometries, rule modes, scoring, replay, and clean programming interfaces.

> 中文版见 [README.md](./README.md).

## Project Overview

PolyJump is a game, not an AI training framework. It provides:

- Multiple geometry models
- Multiple rule modes
- Configurable game rules
- Clean backend/game environment interfaces
- Replay / move history
- Optional external AI integration

## Geometry Models

| Model | Coordinates | Directions | Players |
|---|---|---|---|
| A | Standard XYZ cube | 6/8/12/14/18/20/26 + custom | 2/3/4/6/8 |
| B | L1 even sublattice | fixed 12 | 2/3/4/6 |
| C | L1 full integer points | fixed 20 | 2/3/4/6 |
| D | External pyramid full points | fixed 14 | 2/3/4/6 |
| A-ext | External pyramid | configurable | 2/3/4/6 |
| B-ext | External pyramid even sublattice | fixed 12 | 2/3/4/6 |
| C-ext | External pyramid full points | fixed 20 | 2/3/4/6 |

## Game Modes

| Mode | Goal | Capture |
|---|---|---|
| Chinese Checkers | Move all pieces to opponent target area | none |
| Draughts / Western | Capture all opponent pieces | remove captured |
| Mixed | Transport to target, with displacement captures | return to base |

## Scoring

| Rule | Default Points |
|---|---|
| Each chain jump | +1 temporary |
| Capture | +2 |
| Enter target zone | +1 |
| Win bonus | +10 |
| Surviving pieces in capture mode | +1 each |

## One-Click Start

```bash
python run.py
```

Starts the backend and opens the browser automatically.

## Interfaces

### HTTP API

| Method | Path | Description |
|---|---|---|
| GET | `/api/config` | Default config |
| GET | `/api/direction-sets` | Direction rules |
| POST | `/api/game/new` | Create game |
| GET | `/api/game/{id}` | Current state |
| GET | `/api/game/{id}/legal-moves` | Legal paths |
| POST | `/api/game/{id}/move` | Execute move |
| POST | `/api/game/{id}/ai-move` | Random AI move |
| GET | `/api/game/{id}/history` | Replay / history |

### Python GameEnv

```python
from backend.game.env import GameEnv

env = GameEnv(config)
result = env.reset()
actions = env.action_space()
result = env.step(actions[0]["id"])
```

### Headless

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --moves 10
```

## Documentation

- Current docs index: [docs/README.md](./docs/README.md)
- Chinese README: [README.md](./README.md)

## Hugging Face Deployment

The repository includes a Dockerfile. To deploy as an HF Space:

1. Create a Space with SDK **Docker**
2. Push this repository to the Space
3. The app starts at `http://0.0.0.0:7860`

The Space includes only the game, no AI training content.

## License

See [LICENSE](./LICENSE).
