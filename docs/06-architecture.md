# PolyJump 项目架构

## 1. 总览

PolyJump 分为两部分：

```text
backend/   Python 规则引擎 + FastAPI
frontend/  HTML + Three.js 渲染 / 交互
docs/      设计文档
```

规则由后端维护，前端只负责显示和发送用户选择。

---

## 2. 目录结构

```text
poly-jump/
├── backend/
│   ├── app.py                 # FastAPI 入口
│   └── game/
│       ├── config.py          # 配置类与校验
│       ├── geometry_a.py      # A 模型几何
│       ├── geometry_b.py      # B 模型几何
│       ├── board.py           # 棋盘状态
│       ├── moves.py           # 移动生成 / 跳跃 / 连跳
│       ├── rules.py           # 规则开关逻辑
│       ├── winner.py          # 胜负判定
│       └── game_state.py      # 单局状态管理
├── frontend/
│   ├── index.html             # 主菜单 + 游戏入口
│   ├── main.js                # Three.js 渲染
│   ├── menu.js                # 主菜单配置生成
│   └── style.css
├── docs/
└── README.md
```

---

## 3. 核心类设计

### 3.1 `PolyJumpConfig`

配置类。所有规则、几何、玩家、渲染选项都从这里读。

```python
@dataclass
class PolyJumpConfig:
    geometry: str
    board_size: tuple
    players: int
    direction_set: list
    movement: MovementConfig
    capture: CaptureConfig
    goal: GoalConfig
    initial_layout: InitialLayoutConfig
```

### 3.2 `Geometry`

几何抽象接口：

```python
class Geometry:
    def generate_points(self) -> list[tuple]: ...
    def generate_routes(self, direction_set) -> list[tuple]: ...
    def is_inside(self, pos) -> bool: ...
    def neighbors(self, pos, direction_set) -> list[tuple]: ...
    def distance(self, a, b) -> float: ...
    def home_region(self, player) -> set: ...
    def target_region(self, player) -> set: ...
```

实现类：

- `GeometryA`
- `GeometryB`

### 3.3 `Board`

棋盘状态：

```python
class Board:
    config: PolyJumpConfig
    points: list[tuple]
    pieces: dict[tuple, int]   # pos -> player
    player_bases: dict[int, set]
    player_targets: dict[int, set]
```

### 3.4 `MoveGenerator`

根据配置生成合法移动：

```python
class MoveGenerator:
    def legal_moves(self, board: Board, player: int) -> list[Path]: ...
```

返回的是路径列表，不是简单起终点。

### 3.5 `Rules`

规则判定：

```python
class Rules:
    def is_legal(self, board, path, player) -> bool: ...
    def apply_move(self, board, path, player) -> None: ...
    def check_winner(self, board) -> int | None: ...
```

### 3.6 `GameState`

单局状态：

```python
class GameState:
    board: Board
    current_player: int
    move_history: list[MoveRecord]
    winner: int | None
```

---

## 4. 后端 API 设计

### 4.1 基础 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/config` | 获取前端可配置项 |
| POST | `/api/game/new` | 创建新对局，返回 game_id |
| GET | `/api/game/{id}` | 获取当前局面 |
| GET | `/api/game/{id}/legal-moves` | 获取当前玩家合法路径 |
| POST | `/api/game/{id}/move` | 提交移动路径 |
| POST | `/api/game/{id}/ai-move` | 请求 AI 走一步 |
| GET | `/api/game/{id}/history` | 获取棋谱 |

### 4.2 请求示例

创建新对局：

```json
POST /api/game/new
{
  "config": {
    "geometry": "A",
    "board_size": [9, 9, 9],
    "players": 2,
    "direction_set": [6, 12, 8],
    "capture": {"mode": "NONE"}
  }
}
```

获取合法路径：

```json
GET /api/game/{id}/legal-moves
{
  "player": 1,
  "paths": [
    [[0,0,0], [1,0,0]],
    [[0,0,0], [2,0,0], [4,0,0]]
  ]
}
```

提交移动：

```json
POST /api/game/{id}/move
{
  "path": [[0,0,0], [2,0,0], [4,0,0]]
}
```

---

## 5. 数据流

```text
用户在主菜单选择选项
        |
        v
前端生成 JSON 配置
        |
        v
后端 /api/game/new 创建 GameState
        |
        v
前端拿到棋盘点集 / 路线 / 棋子位置
        |
        v
玩家点击选子
        |
        v
前端请求 legal-moves
        |
        v
后端返回合法路径列表
        |
        v
前端高亮所有合法路径
        |
        v
玩家选择一条路径
        |
        v
前端提交 move
        |
        v
后端校验并更新局面
        |
        v
返回新状态
```

---

## 6. 配置生成模式

用户要求“主菜单生成配置，而不是代码写死”。

实现方式：

```text
主菜单 UI
  -> 收集用户选择
  -> 生成 PolyJumpConfig 实例 / JSON
  -> 传给游戏界面
  -> 游戏界面请求后端创建对局
```

这样同一个后端可以接受任意配置。

---

## 7. 前端与后端职责划分

| 职责 | 后端 | 前端 |
|---|---|---|
| 规则判定 | ✅ | ❌ |
| 合法路径生成 | ✅ | ❌ |
| 胜负判定 | ✅ | ❌ |
| 点阵渲染 | ❌ | ✅ |
| 路线渲染 | ❌ | ✅ |
| 相机操作 | ❌ | ✅ |
| 交互高亮 | ❌ | ✅ |
| 配置表单 | ❌ | ✅ |

---

## 8. 可选 AI 接口

后端提供统一 AI 接口：

```python
class AI:
    def select_move(self, state: GameState, legal_paths: list[Path]) -> Path:
        ...
```

AI 类型：

- `RandomAI`
- `GreedyAI`
- `MCTSAI`
- 以后：神经网络 / RL agent

AI 只接收合法路径列表，不接收其他提示。这保证了人类和 AI 使用同一份信息。

---

## 9. 部署建议

- 本地：`uvicorn backend.app:app`
- Hugging Face Space：Docker 或 Gradio
- 纯演示版：静态 HTML + Three.js（可另做一份 JS 规则）
