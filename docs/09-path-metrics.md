# 路径度量（Action / Step）

PolyJump 在后端提供统一的路径度量数据，供 AI 研究、训练和回放使用。前端不依赖这些字段。

## 术语

| 概念 | 定义 |
|---|---|
| `action` | 一次玩家操作，对应一条合法路径 / 一条历史记录 |
| `step` | 一条 action 路径中的一次移动，即 `path[i] -> path[i+1]` |
| `step_count` | 一条 action 中包含多少个 step |
| `straight_distance` | action 起点到终点的直线距离（欧氏距离） |
| `path_distance` | 沿 action 实际路径累计移动的总距离 |
| `step_distances` | 每个 step 的移动距离明细 |

示例：

```text
path = [6,7,8] -> [8,7,8] -> [6,5,6] -> [4,5,4] -> [4,3,4] -> [2,3,2] -> [0,3,2] -> [0,3,0]
```

对应的度量：

```text
step_count = 7
straight_distance = 从第一个点到最后一个点的直线距离
path_distance = 7 段 step 的实际位移距离之和
step_distances = [d1, d2, d3, d4, d5, d6, d7]
```

## 数据位置

### 1. 合法动作

`GameEnv.action_space()` 返回的每个 action 都包含：

```json
{
  "id": 12,
  "path": [[6,7,8], [8,7,8], [6,5,6], [4,5,4], [4,3,4], [2,3,2], [0,3,2], [0,3,0]],
  "step_count": 7,
  "straight_distance": 11.31,
  "path_distance": 18.6,
  "step_distances": [2.0, 2.8, 1.4, 2.0, 2.8, 2.0, 1.4]
}
```

### 2. 历史记录

`move_history` 中每个 action 同样记录这些字段：

```json
{
  "player": 2,
  "path": [...],
  "step_count": 7,
  "straight_distance": 11.31,
  "path_distance": 18.6,
  "step_distances": [2.0, 2.8, ...]
}
```

### 3. 状态 / 汇总

`state_dict()`、`history_to_dict()` 和 `StepResult` 中提供汇总：

```json
{
  "action_count": 14,
  "total_steps": 63,
  "total_straight_distance": 120.3,
  "total_path_distance": 189.7,
  "players": {
    "1": {
      "action_count": 7,
      "step_count": 28,
      "straight_distance": 55.2,
      "path_distance": 83.4
    },
    "2": {
      "action_count": 7,
      "step_count": 35,
      "straight_distance": 65.1,
      "path_distance": 106.3
    }
  }
}
```

`StepResult` 包含：

```text
action_count
total_steps
total_straight_distance
total_path_distance
```

## 设计说明

- 这些字段由后端统一计算和记录。
- 平台只提供数据，不规定 AI 训练时使用哪些字段。
- 训练方可以自行选择：
  - 只优化胜利
  - 在 reward 中加入步数惩罚
  - 在观测中加入路径距离
  - 根据 `step_distances` 自定义更细的度量
- 前端不读取这些字段，不修改前端行为。

## AI 基准评测

`ai_research` 汇总中新增了：

- `avg_moves`：平均 action 数
- `avg_step_count`：平均 step 数
- `avg_straight_distance`：平均直线距离
- `avg_path_distance`：平均路径距离
- `avg_step_per_action`：平均每个 action 包含的 step 数
