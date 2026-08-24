# PolyJump 实现指南

本文档按步骤指导实现一个最小可运行版本。

---

## 阶段 1：后端骨架

### 1.1 创建目录

```text
backend/
  app.py
  game/
    __init__.py
    config.py
    geometry_a.py
    geometry_b.py
    board.py
    moves.py
    rules.py
    winner.py
    game_state.py
```

### 1.2 依赖

```text
fastapi
uvicorn[standard]
pydantic
numpy
pytest
```

### 1.3 Config

实现 `PolyJumpConfig` 与子配置类（见 `05-configuration.md`）。

```python
from dataclasses import dataclass, field

@dataclass
class PolyJumpConfig:
    geometry: str = "A"
    board_size: tuple = (9, 9, 9)
    players: int = 2
    direction_set: list = field(default_factory=lambda: [6, 12, 8])
    movement: dict = field(default_factory=dict)
    capture: dict = field(default_factory=dict)
    goal: dict = field(default_factory=dict)
```

### 1.4 Geometry

实现抽象：

```python
class Geometry:
    def generate_points(self): ...
    def generate_routes(self, direction_set): ...
    def is_inside(self, pos): ...
    def neighbors(self, pos, direction_set): ...
```

### 1.5 Board

```python
class Board:
    def __init__(self, config):
        self.config = config
        self.points = self.geometry.generate_points()
        self.pieces = {}
        self.setup_initial_layout()
```

### 1.6 MoveGenerator

```python
class MoveGenerator:
    def legal_moves(self, board, player):
        paths = []
        for pos, owner in board.pieces.items():
            if owner != player:
                continue
            paths.extend(self.step_moves(board, pos))
            paths.extend(self.jump_moves(board, pos))
            if config.movement.allow_chain:
                paths.extend(self.chain_moves(board, pos))
        return paths
```

---

## 阶段 2：FastAPI

在 `app.py` 中实现：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.post("/api/game/new")
async def new_game(config: dict):
    state = create_game(config)
    return {"game_id": state.id}

@app.get("/api/game/{game_id}")
async def get_game(game_id: str):
    return state_to_json(states[game_id])

@app.get("/api/game/{game_id}/legal-moves")
async def legal_moves(game_id: str):
    state = states[game_id]
    paths = MoveGenerator().legal_moves(state.board, state.current_player)
    return {"player": state.current_player, "paths": paths}

@app.post("/api/game/{game_id}/move")
async def move(game_id: str, body: MoveRequest):
    state = states[game_id]
    ok = apply_move(state, body.path)
    if not ok:
        return {"ok": False}
    return {"ok": True, "state": state_to_json(state)}
```

---

## 阶段 3：前端骨架

```text
frontend/
  index.html
  main.js
  style.css
```

`index.html` 引入 Three.js CDN：

```html
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
```

### 3.1 先渲染点

```javascript
const points = await fetch("/api/game/" + gameId).then(r => r.json()).then(d => d.points);
points.forEach(p => {
    const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.15),
        new THREE.MeshBasicMaterial({ color: 0x88ccff })
    );
    mesh.position.set(p[0], p[1], p[2]);
    scene.add(mesh);
});
```

### 3.2 渲染路线

```javascript
routes.forEach(route => {
    const geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(...route.from),
        new THREE.Vector3(...route.to)
    ]);
    const material = new THREE.LineBasicMaterial({
        color: 0x88ff88,
        transparent: true,
        opacity: 0.3
    });
    scene.add(new THREE.Line(geometry, material));
});
```

### 3.3 选子 + 合法路径高亮

```javascript
function onPointClick(pos) {
    if (!isCurrentPlayerPiece(pos)) return;
    selected = pos;
    const res = await fetch("/api/game/" + gameId + "/legal-moves");
    highlightPaths(res.paths.filter(path => path[0] === pos));
}

function onDestinationClick(pos) {
    const path = findPath(selected, pos);
    if (path) submitMove(path);
}
```

---

## 阶段 4：核心规则实现检查表

实现过程中必须通过测试：

- [ ] 普通移动
- [ ] 单跳
- [ ] 连跳路径展开
- [ ] 自由停 / 必须跳到底
- [ ] 空一格跳
- [ ] 无吃子
- [ ] 吃子移除
- [ ] 混合吃子位移
- [ ] 胜负判定
- [ ] 多玩家轮转
- [ ] 目标区校验
- [ ] A 模型 / B 模型切换
- [ ] B 模型奇偶性检查

---

## 阶段 5：最小测试用例

### 5.1 普通移动

```python
def test_step_move():
    board = create_board(2, A, [6])
    assert contains_move(movegen.legal_moves(board, 1), [[0,0,0], [1,0,0]])
```

### 5.2 单跳

```python
def test_single_jump():
    board.set_piece((2,0,0), 2)
    board.set_piece((0,0,0), 1)
    paths = movegen.legal_moves(board, 1)
    assert [[0,0,0], [4,0,0]] in paths
```

### 5.3 连跳

```python
def test_chain_jump():
    board.set_piece((2,0,0), 2)
    board.set_piece((4,0,0), 2)
    board.set_piece((0,0,0), 1)
    paths = movegen.legal_moves(board, 1)
    assert [[0,0,0], [2,0,0], [4,0,0]] in paths or [[0,0,0], [4,0,0]] in paths
```

---

## 阶段 6：发布

- 本地运行：`uvicorn backend.app:app`
- 浏览器访问：`http://localhost:8000`
- B 站：录屏讲解 + 演示
- Hugging Face：Docker Space 或静态演示版

---

## 实现顺序建议

1. A 模型 + 普通移动
2. 单跳
3. 连跳
4. 吃子
5. 多人
6. 胜负
7. B 模型
8. 前端交互
9. AI 简单版
10. 发布
