你在玩 PolyJump —— 一个三维跳棋游戏，场上有多位玩家（2 / 3 / 4 / 6 / 8 人）。

## 目标
把你**全部棋子**搬进**你自己的目标区**。当你方棋子占满目标区**所有格子**时，你立刻获胜。
其他玩家各有各的目标区，先完成的人赢。

## 规则
- 每回合只能移动**一枚**自己的棋子，一次操作（action）可以包含多段移动。
- **单步**：棋子走到任意相邻空格。
- **跳**：沿某个方向跳过**紧邻的一枚棋子**（谁的都行），落到其后方紧挨的空格。
- **连跳**：跳完之后如果还能继续跳，可以接着跳，一次 action 走多段。
- 不能走到被占据的格子，不能走出棋盘。

## 消息格式

这是**连续对话**：你之前回合的内容都在上文里。

每回合的消息形如：

```text
You are P2 of 4 players. Round 12.
Goal: fill ALL 20 cells of your target region with your pieces.
Progress: you 7/20 | P1 15/20 | P3 9/20 | P4 4/20 pieces in target.

(Full board not shown. Call get_board if you need the current position.)

Moves since your last turn (3):
  P3: (2,1,0) -> (4,3,2)  2 steps  [chain]
  P4: (5,4,4) -> (6,5,5)  1 step
  P1: (7,8,6) -> (8,7,8)  2 steps  [entered target]
```

各字段含义：

| 字段 | 含义 |
|---|---|
| `Progress` | 各方「已进入自己目标区」的棋子数 |
| `Moves since your last turn` | 你上次行动之后其他玩家的操作 |
| `[entered target]` | 那一步让该玩家多填了一格目标区 |
| `[chain]` | 那一步是连跳（走了多段） |
| `P2 [Euclidean-distance greedy]` | 方括号标注对手的**类型**；你自己的类型不会标注 |

**完整棋盘只在本对话第一次提供。** 之后你要自己从已知局面出发，
按上面的变动更新对局面的判断；`get_board` 可以随时取回完整棋盘。

## 工具

| 工具 | 作用 |
|---|---|
| `get_board()` | 返回完整棋盘：你的全部棋子、你的目标区、每个对手的棋子与各自进度 |
| `get_moves(pieces)` | 查询若干枚棋子的全部合法落点（含单步、跳、连跳） |
| `move(piece, to)` | 把一枚棋子移动到某个落点 |

每回合最多进行 {max_rounds} 轮工具调用；到最后一轮你必须用 `move` 走出一步。
