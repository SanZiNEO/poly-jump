# 动作表示与合法路径生成

## 1. 基本动作

PolyJump 中，单个动作表示为一个**路径**：

```text
Path = [pos_0, pos_1, ..., pos_n]
```

- `pos_0`：起点，必须是当前玩家的棋子
- `pos_n`：终点
- 中间点：连跳的每次落点

---

## 2. 动作分类

### 2.1 普通移动

```text
[[0,0,0], [0,1,0]]
```

长度 2。

### 2.2 单次跳跃

```text
[[0,0,0], [2,0,0]]  // 跳过一个棋子
```

长度 2，但实际跨越了中间一个格子。

### 2.3 连跳

```text
[[0,0,0], [2,0,0], [4,2,0], ...]
```

长度 > 2。

### 2.4 两步跳 / 空一格跳

```text
[[0,0,0], [4,0,0]]  // 跳过隔一格棋子
```

具体由 `two_step_hop` 开关控制。

---

## 3. 为什么用路径而不是起终点

- 连跳需要记录所有经过的落点
- 可以支持“中国跳棋式停止在中间”与“国际跳棋式跳到尽头”
- 前端能直观展示跳跃轨迹
- AI 和人类共用同一份路径合法列表

---

## 4. 合法路径生成算法

> **所有移动都是沿向量的直线移动。**  
> 普通移动只检查起点和终点；跳跃只检查被跳位置 `p+v` 和落点 `p+2v`；其他中间位置不检查。

### 4.1 普通移动

```python
def step_moves(board, pos, directions):
    moves = []
    for v in directions:
        target = pos + v
        if board.is_inside(target) and board.is_empty(target):
            moves.append([pos, target])
    return moves
```

### 4.2 单跳

```python
def jump_moves(board, pos, directions):
    moves = []
    for v in directions:
        mid = pos + v
        dest = pos + 2 * v
        if (
            board.is_inside(mid)
            and board.is_occupied(mid)
            and board.is_inside(dest)
            and board.is_empty(dest)
        ):
            moves.append([pos, dest])
    return moves
```

### 4.3 连跳

```python
def chain_jumps(board, path, directions):
    results = []
    current = path[-1]
    for v in directions:
        mid = current + v
        dest = current + 2 * v
        if legal_jump(board, current, v):
            new_path = path + [dest]
            results.append(new_path)
            results.extend(chain_jumps(board, new_path, directions))
    return results
```

`hop_mode` 决定：

- `FREE_STOP`：每个中间路径都是合法动作
- `FORCE_ALL`：只有无法继续延伸的路径才是合法动作

---

## 5. 用于 AI 的合法路径列表

后端生成：

```json
{
  "player": 1,
  "current_pos": [0,0,0],
  "paths": [
    [[0,0,0], [1,0,0]],
    [[0,0,0], [2,0,0]],
    [[0,0,0], [2,0,0], [4,2,0]],
    [[0,0,0], [2,0,0], [4,2,0], [4,4,0]]
  ]
}
```

前端和 AI 都只使用这份列表。

- 前端：用于高亮可落点
- AI：用于限制行动空间，不告诉 AI 应该走哪条，只告诉它哪些是合法路径

---

## 6. 动作掩码

如果接入 RL，可以把合法路径转成离散动作掩码：

```text
action_index -> path
valid_mask[i] = 1 表示该路径合法
```

或者使用变长动作：

```text
action = [(pos_0), (pos_1), ...]
```

---

## 7. 路径合法性校验

后端在 `apply_move` 前必须重新校验：

1. 路径起点是当前玩家棋子
2. 路径每一段都符合移动/跳跃规则
3. 移动为直线移动，不逐格检查中间格
4. 跳跃段只校验被跳位置 `p+v` 和落点 `p+2v`
5. 路径满足 `hop_mode`
6. 终点满足目标区/吃子规则
7. 未发生重复落点

---

## 8. 输出给前端的渲染信息

除了路径，还需要给出：

```json
{
  "start": [0,0,0],
  "end": [4,2,0],
  "path": [[0,0,0], [2,0,0], [4,2,0]],
  "type": "JUMP_CHAIN",
  "captures": [[2,0,0]]
}
```

前端可以据此画出路径和吃子标记。
