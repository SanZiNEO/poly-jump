# PolyJump 当前实现状态

> 本文档描述当前代码库的真实状态，优先于早期设计文档。

---

## 1. 项目定位

PolyJump 是一个可配置的三维跳棋游戏框架：

- 不是 AI 训练框架
- 提供完整游戏玩法
- 提供干净的后端/编程接口
- 外部程序可以基于该接口运行自己的 AI/分析程序

---

## 2. 几何模型

### 2.1 基础模型

| 模型 | 坐标 | 移动方向 | 玩家数 | 说明 |
|---|---|---|---|---|
| A | 标准 XYZ 正方体/长方体 | 6/8/12/14/18/20/26 + 自定义 | 2/3/4/6/8 | 最直观 |
| B | L1 球偶子晶格 | 固定 12 | 2/3/4/6 | FCC 单子晶格 |
| C | L1 球全整数点 | 固定 20 | 2/3/4/6 | 20 向晶体 |
| D | 外接金字塔全整数点 | 固定 14 | 2/3/4/6 | 外接金字塔版 |

### 2.2 外接金字塔家族

| 模型 | 坐标 | 移动方向 | 玩家数 |
|---|---|---|---|
| A-ext | 外接金字塔 | 可配置 6/8/12/... | 2/3/4/6 |
| B-ext | 外接金字塔偶子晶格 | 固定 12 | 2/3/4/6 |
| C-ext | 外接金字塔全整数点 | 固定 20 | 2/3/4/6 |

### 2.3 外接金字塔层数

配置字段：

```text
ep_side：中心正方体边长，必须为奇数
```

| ep_side | 外接层 | 每面子数 |
|---|---|---|
| 5 | 3×3, 1×1 | 10 |
| 7 | 5×5, 3×3, 1×1 | 35 |
| 9 | 7×7, 5×5, 3×3, 1×1 | 84 |

---

## 3. 玩法规则

### 3.1 三种游戏模式

| 模式 | 目标 | 吃子 |
|---|---|---|
| 中国跳棋 | 把己方棋子搬运并填满对方目标区 | 无 |
| 西洋跳棋 | 吃光所有对手棋子 | 被跳棋子移除 |
| 混合模式 | 仍以搬运填目标区为主 | 被跳棋子送回本方基地 |

### 3.2 移动规则

- 普通移动
- 单跳
- 连跳
- 两格跳（空一格跳）
- FREE_STOP / FORCE_ALL
- 无棋可走自动跳过

### 3.3 积分制

配置字段：

```text
ScoringConfig
```

| 规则 | 默认分 |
|---|---|
| 连跳每次 | +1（临时分） |
| 吃子每次 | +2 |
| 进入目标区 | +1 |
| 胜利奖励 | +10 |
| 西洋棋存活棋子 | 每子 +1 |

- 连跳临时分：胜者保留，败者扣除
- 普通跳不加分

---

## 4. 接口

### 4.1 HTTP API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/config` | 默认配置 |
| GET | `/api/direction-sets` | 方向规则 |
| POST | `/api/game/new` | 创建对局 |
| GET | `/api/game/{id}` | 当前局面 |
| GET | `/api/game/{id}/legal-moves` | 合法路径 |
| POST | `/api/game/{id}/move` | 执行移动 |
| POST | `/api/game/{id}/ai-move` | AI 随机走 |
| GET | `/api/game/{id}/history` | 棋谱/回放 |

### 4.2 纯 Python 接口

```python
from backend.game.env import GameEnv

env = GameEnv(config)
result = env.reset()

actions = env.action_space()
result = env.step(actions[0]["id"])
```

方法：

```text
reset()
legal_moves()
action_space()
step(action)
observe()
state_dict()
```

`StepResult` 包含：

```text
game_id
current_player
winner
last_move
legal_paths
legal_actions
done
scores
temp_scores
```

### 4.3 Headless 运行

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --moves 10
```

---

## 5. 配置

配置文件位于：

```text
configs/
├── a_2p_6dir.json
├── a_4p_6dir.json
├── a_capture.json
├── b_6p_radius6.json
├── c_6p_radius6.json
└── directions.json
```

主要配置字段：

```text
geometry
board_size
b_radius
c_radius
ep_side
players
direction_set
custom_vectors
movement
capture
goal
initial_layout
scoring
render
```

---

## 6. 前端功能

- 黑白灰主菜单
- A / B / C / D / A-ext / B-ext / C-ext 模型选择
- 方向规则自动扫描
- 玩家数联动
- 3D 棋盘渲染
- 选子、合法路径高亮、落子
- 玩家列表 / 当前玩家高亮
- 对局历史与回放
- HUD 积分表

---

## 7. 测试

```text
48 passed in 0.18s
```

---

## 8. 后续计划

- 基础 AI（Random / Greedy）示例
- AI 自对弈 demo
- 克隆/撤销接口（MCTS 用）
- 紧凑观测（神经网络用）
- 发布准备
