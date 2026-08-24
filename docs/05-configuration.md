# PolyJump 配置与规则开关

所有规则都是配置项。本文档定义完整配置结构。

---

## 1. 配置定位

项目使用“类定义 + 配置实例”的模式：

```text
代码定义 Config 类
配置实例（JSON / YAML / 前端表单生成）指定具体规则
```

同一个框架通过不同配置生成不同游戏场景。

---

## 2. 顶层配置结构

```json
{
  "game_name": "PolyJump",
  "geometry": "A",
  "board_size": [9, 9, 9],
  "b_radius": 6,
  "players": 2,
  "player_assignments": [],
  "direction_set": [6, 12, 8],
  "custom_vectors": [],
  "movement": {
    "allow_step": true,
    "allow_jump": true,
    "allow_chain": true,
    "hop_mode": "FREE_STOP",
    "two_step_hop": false,
    "max_chain_length": 0
  },
  "capture": {
    "mode": "NONE",
    "capture_opponent_only": true,
    "mixed_swap": false
  },
  "goal": {
    "objective": "FILL_TARGET",
    "target_region": "OPPOSITE_CORNER",
    "must_fill_all_cells": true,
    "allow_pass_through_enemy": true,
    "allow_stay_in_enemy": false
  },
  "initial_layout": {
    "shape": "TETRA_PYRAMID",
    "layers": 4,
    "custom_layout": []
  },
  "rules": {
    "pass_allowed": false,
    "draw_when_no_moves": false,
    "first_to_finish_wins": true
  },
  "render": {
    "show_points": true,
    "show_routes": true,
    "route_colors": {},
    "point_size": 1.0,
    "line_opacity": 0.3
  }
}
```

---

## 3. 几何配置

| 字段 | 值 | 说明 |
|---|---|---|
| `geometry` | `A` / `B` | 选择几何模型 |
| `board_size` | `[x, y, z]` | A 模型使用 |
| `b_radius` | 偶数，如 `6` | B 模型 L1 球半径 |
| `origin` | `CORNER` / `CENTER` | A 用 CORNER，B 用 CENTER |
| `fcc_parity` | `0` | B 模型固定使用偶子晶格 |
| `valid_points` | list | 可选：显式给出合法点集 |

---

## 4. 玩家配置

| 字段 | 值 | 说明 |
|---|---|---|
| `players` | 2 / 3 / 4 / 6 / 8 | 玩家数 |
| `player_assignments` | list | 每个玩家的基地、目标区 |
| `target_empty` | bool | 多人模式目标角是否初始为空 |
| `turn_order` | `CLOCKWISE` / `EXPLICIT` | 轮转方式 |

---

## 5. 方向配置

### 5.1 基础方向集

```json
"direction_set": [6, 12, 8]
```

可组合：

```text
6
8
12
14
18
20
26
```

### 5.2 自定义向量

```json
"custom_vectors": [
  [2, 1, 0],
  [2, 3, 0],
  [2, 1, 1],
  [2, 2, 1],
  [2, 2, 3],
  [2, 3, 1]
]
```

所有自定义向量自动生成正负方向。

### 5.3 方向规则注册表

方向规则不写死在前端代码中，统一在以下文件维护：

```text
configs/directions.json
```

- `base_sets`：基础方向集 6 / 8 / 12
- `custom_sets`：后端/配置文件新增的自定义向量

后端提供：

```text
GET /api/direction-sets
```

前端通过该接口自动扫描并显示可用的方向集。  
后续新增自定义方向只需要修改 `configs/directions.json`，前端无需改代码。

---

## 6. 移动规则开关

| 字段 | 类型 | 说明 |
|---|---|---|
| `allow_step` | bool | 是否允许普通走一步 |
| `allow_jump` | bool | 是否允许跳跃 |
| `allow_chain` | bool | 是否允许连跳 |
| `hop_mode` | enum | `FREE_STOP` 或 `FORCE_ALL` |
| `two_step_hop` | bool | 是否允许空一格跳 |
| `max_chain_length` | int | 0 = 不限制；正整数 = 最大连跳次数 |

### 6.1 连跳模式

```text
FREE_STOP  = 中国跳棋式，可停在任意合法落点
FORCE_ALL  = 国际跳棋式，必须跳到不能跳为止
```

---

## 7. 对局规则（游戏模式）

| 字段 | 说明 |
|---|---|
| `mode` | `NONE` / `CAPTURE` / `MIXED` |
| `capture_opponent_only` | 是否只吃对方棋子 |
| `mixed_swap` | 混合模式下，被吃子送回原位/本方基地 |

三种游戏模式：

```text
NONE     ：中国跳棋。
            目标：把己方棋子搬运并填满对方目标区。

CAPTURE  ：西洋跳棋。
            目标：吃光所有对手棋子，最后保留己方棋子者获胜。

MIXED    ：混合模式（优化变体）。
            主要目标仍是搬运填目标区；
            吃子时被跳过的棋子不消失，而是送回它自己的初始/本方基地。
```

---

## 8. 目标 / 胜负配置

| 字段 | 说明 |
|---|---|
| `objective` | `FILL_TARGET` |
| `target_region` | `OPPOSITE_CORNER` / 自定义 |
| `must_fill_all_cells` | 是否必须精确填满目标区所有格位 |
| `allow_pass_through_enemy` | 是否允许经过敌方目标区 |
| `allow_stay_in_enemy` | 是否允许最终停留在敌方目标区 |
| `first_to_finish_wins` | 多人局是否先完成者获胜 |

---

## 9. 初始布局配置

| 字段 | 说明 |
|---|---|
| `shape` | `TETRA_PYRAMID` / `SQUARE_PYRAMID` / `B_TIP_PYRAMID` / `CUSTOM` |
| `layers` | A 模型金字塔层数；B 模型由 b_radius 自动取 R/2 |
| `custom_layout` | 显式坐标列表 |

### 9.1 形状区别

```text
TETRA_PYRAMID   = 1+3+6+10+... (20子/4层)
SQUARE_PYRAMID  = 1+4+9+16+... (30子/4层)
B_TIP_PYRAMID   = B 模型尖端基地：1+4+9+... 共 R/2 层
```

---

## 10. 渲染配置

| 字段 | 说明 |
|---|---|
| `show_points` | 是否显示点 |
| `show_routes` | 是否显示路线 |
| `route_colors` | 不同方向类型颜色 |
| `point_size` | 点大小 |
| `line_opacity` | 线的透明度 |
| `camera` | 初始相机参数 |

---

## 11. 配置类定义示例（Python）

```python
from dataclasses import dataclass, field
from typing import Literal, List, Tuple


@dataclass
class MovementConfig:
    allow_step: bool = True
    allow_jump: bool = True
    allow_chain: bool = True
    hop_mode: Literal["FREE_STOP", "FORCE_ALL"] = "FREE_STOP"
    two_step_hop: bool = False
    max_chain_length: int = 0


@dataclass
class CaptureConfig:
    mode: Literal["NONE", "CAPTURE", "MIXED"] = "NONE"
    capture_opponent_only: bool = True
    mixed_swap: bool = False


@dataclass
class GoalConfig:
    objective: str = "FILL_TARGET"
    target_region: str = "OPPOSITE_CORNER"
    must_fill_all_cells: bool = True


@dataclass
class PolyJumpConfig:
    geometry: Literal["A", "B"] = "A"
    board_size: Tuple[int, int, int] = (9, 9, 9)
    b_radius: int = 6
    players: int = 2
    direction_set: List[int] = field(default_factory=lambda: [6, 12, 8])
    custom_vectors: List[Tuple[int, int, int]] = field(default_factory=list)
    movement: MovementConfig = field(default_factory=MovementConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    goal: GoalConfig = field(default_factory=GoalConfig)
    initial_layout: dict = field(default_factory=lambda: {"shape": "TETRA_PYRAMID", "layers": 4})
```

---

## 12. 配置校验器

实现时建议包含一个校验器：

- 检查 B 模型 b_radius 是否为偶数
- 检查方向集是否合法
- 检查玩家数是否在允许列表
- 检查基地之间是否重叠
- 检查目标区是否可达
- 检查棋子数是否超过棋盘容量

```text
validate(config) -> list[str]  # 返回错误列表
```
