# 可选小 AI 实现

本文档是可选内容，不是项目主线。  
项目主线是“可玩的三维跳棋游戏框架”。  
如果暂时不想要 AI，可以完全跳过本文档。

---

## 1. 目标

提供几个小规模 AI，方便：

- 人机对战
- 演示
- 测试规则引擎

不讨论超出小 AI 范围的选题。

---

## 2. 简单 AI

### 2.1 RandomAI

随机从合法路径中选一条：

```python
class RandomAI:
    def select_move(self, legal_paths):
        return random.choice(legal_paths)
```

### 2.2 GreedyAI

选择“让自己棋子更快接近目标区”的路径：

```python
class GreedyAI:
    def select_move(self, board, player, legal_paths):
        return max(
            legal_paths,
            key=lambda path: progress_gain(board, player, path)
        )
```

`progress_gain` 可以定义为：

```text
移动前所有棋子到目标距离之和 - 移动后距离之和
```

### 2.3 MCTSAI

用小规模 MCTS 搜索：

- 适合小棋盘
- 连跳路径比较多时需要控制节点数
- 不用神经网络也能有一定的棋力

---

## 3. AI 接口

所有 AI 都只接收：

```text
board 状态
当前玩家
合法路径列表
```

不接收“哪条路最好”的提示。

```python
class AI:
    def select_move(self, board, player, legal_paths):
        ...
```

---

## 4. 可选：小规模强化学习

如果以后想试，可以做一个很小的 RL 实验：

- 棋盘：5×5×5
- 人数：2
- 方向：6 向
- 算法：PPO
- 网络：小 MLP

RTX 4060 可以跑这种小规模实验，但不是优先项。

---

## 5. 建议实现顺序

```text
1. RandomAI
2. GreedyAI
3. MCTSAI（小棋盘）
4. （可选）小型 PPO / 自博弈
```

AI 不是发布必需部分，游戏框架本身优先。
