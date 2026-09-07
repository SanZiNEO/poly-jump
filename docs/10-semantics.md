# 语义说明（Semantics）

本文档补充 PolyJump 中除 `action / step` 之外容易产生歧义的语义定义。

## 1. path 与 edges

| 名称 | 含义 |
|---|---|
| `path` | 一次 action 的完整移动序列，例如 `[a, b, c]` |
| `edges` | 几何图上的边，用于前端渲染，每项包含 `from / to / type` |

它们不是同一个东西：

- `path` 是“一次操作里棋子实际走的路线”
- `edges` 是“棋盘上所有允许连接的边”

## 2. 移动类型

| 字段 | 含义 |
|---|---|
| `allow_single_move` | 是否允许普通一格移动 |
| `allow_jump` | 是否允许单跳 |
| `allow_chain` | 是否允许连跳 |
| `hop_mode` | `FREE_STOP`：连跳可停在任意落点；`FORCE_ALL`：必须跳到无法继续为止 |
| `two_hop` | 是否允许两格跳（空一格跳） |
| `max_chain_steps` | 连跳最多包含多少个 step；`0` 表示不限制 |

两格跳的具体规则：

```text
p+v 空
p+2v 有子（被跳）
p+3v 空
p+4v 空
-> 棋子可以从 p 到 p+4v
```

## 3. GoalConfig 语义

```text
objective           目标类型
target_region       目标区域
must_fill_all_cells 胜利是否要求填满目标区
allow_pass_through_enemy 是否允许穿过对方棋子所在位置附近
allow_stay_in_enemy 是否允许停留在对方区域
first_to_finish_wins 是否先完成者获胜
```

当前可确认的规则：

- 中国跳棋类：把本方棋子搬到并填满对方目标区。
- `must_fill_all_cells = true` 时，胜利以“目标区全部格子被本方棋子占据”为准。
- 若未来使用 `must_fill_all_cells = false`，胜利判定需要由规则实现明确说明。
- `allow_pass_through_enemy` / `allow_stay_in_enemy` 是目标区/路径交互的开关，具体行为以规则实现为准。

## 4. Capture 语义

```text
capture.mode                 NONE / CAPTURE / MIXED
capture.capture_opponent_only 只吃对手棋子
capture.mixed_swap           混合模式吃子是否交换/回填
capture.capture_in_base      是否允许在基地内吃子
```

- `NONE`：不发生吃子。
- `CAPTURE`：被跳棋子移除。
- `MIXED`：被跳棋子返回其本方基地；基地满时按规则实现放置。
- 默认基地内不触发吃子，`capture_in_base = true` 时开启。

## 5. 积分与临时分

```text
scores       正式积分
temp_scores  连跳临时分
```

规则：

- 连跳每次产生临时分。
- 对局结束时：
  - 胜者保留临时分；
  - 败者扣除临时分；
  - 胜利奖励、吃子分、目标区进入分进入正式分。
- `chain_max_scoring` 只限制计分的连跳次数，不限制连跳本身的 step 数。

## 6. round 定义

```text
round = (action_count - 1) // players + 1
```

含义：

- `action_count = 0` 时 `round = 0`。
- 所有玩家各完成一次 action 后，进入下一轮。
- 如果某个玩家无合法 action 被自动跳过，不额外计入新的一轮。

## 7. path_stats 的 players key

`path_stats.players` 是 JSON 对象，因此 key 是字符串：

```json
{
  "players": {
    "1": { ... },
    "2": { ... }
  }
}
```

使用方需要把 key 转成整数，或按字符串处理。

## 8. 启发式 AI 命名

AI 的“距离”不是路径度量：

- `straight_distance` / `path_distance` / `step_distances`：路径度量。
- `EuclideanHeuristicAI` / `ChebyshevHeuristicAI` / `GraphHeuristicAI`：到目标区的启发式距离。
- `HeuristicAgent.heuristic_distance()`：AI 的启发式距离接口。

HTTP `ai_type` 统一为：

```text
graph_bfs      # 图距离 BFS 启发式
euclidean      # 欧氏距离启发式
chebyshev      # 切比雪夫距离启发式
```
