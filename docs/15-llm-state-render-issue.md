# LLM 状态渲染缺陷：`opponent X/20` 语义错误

> 记录日期：2026-10-02
> 涉及文件：`ai_research/llm/agent.py` 的 `render_state()`
> 状态：**已修复**（2026-10-02），回归测试 `tests/test_llm_state_render.py`

## 1. 缺陷是什么

`render_state()` 生成的状态块里有一行进度：

```python
inside = sum(1 for p in mine if p in target_set)        # 我方棋子在我方目标区
opp_inside = sum(1 for p in theirs if p in target_set)  # ← 错在这里
...
f"Progress: you {inside}/{len(target)} in target, opponent {opp_inside}/{len(target)}. "
```

`target_set` 是**我方**的目标区。所以 `opp_inside` 统计的是"**对手有多少棋子堵在我方目标区里**"，
而不是"对手有多少棋子进了它自己的目标区"。

实际渲染出来的样子（第 1 回合）：

```text
Progress: you 0/20 in target, opponent 20/20. Round 0.
```

## 2. 为什么这是错的

三个问题叠加：

**① 标签语义错误。** 两行并排写 `you X/20` 和 `opponent X/20`，读起来是"双方进度对比"，
但右边那项根本不是对手的进度。

**② 对手的真实进度完全缺失。** 对手的目标区是"我的出发区"，
这个信息在状态块里**一个字都没有**。模型只能从对方棋子的裸坐标自己推。

**③ 数值方向是反的，且开局就极吓人。** 开局时对手棋子全部摆在它的基地 = 我的目标区，
所以显示 `opponent 20/20` —— 看起来像"对手已经赢了"。随着对手把棋子搬走，
这个数字**单调下降**，又看起来像"对手在倒退"。

## 3. 实测证据（2026-10-02 正式 A 局，`runs/llm_a_official/`）

模型确实被误导了，而且持续了约 50 个回合。

**第 1 回合**（刚看到状态块）：

> "Wait, the opponent already has 20/20 in target (their target is my starting corner presumably)"
> "That means opponent already moved all pieces there? And 'opponent 20/20' means opponent has filled their target"
> **"Wait, but if opponent already has 20/20, hasn't the opponent won? Unless it's my turn and the game continues"**
> "Actually maybe the 'opponent' is just a static setup and I need to win first? But opponent already 20/20"

**第 10 回合**（把数字当成对手进度，误判局势）：

> "Current progress: me 1/20, opponent 13/20."
> **"Actually wait, opponent having 13/20 means opponent is about to win."**

（实际含义：有 13 枚敌方棋子还留在我的目标区里挡路，且这个数字在下降。
模型却读成"对手快赢了"。）

**第 25 回合**（仍在误读）：

> "Wait, opponent has 5 in target already."

**第 55 回合**（终于从裸坐标自己推出来了）：

> "which are in my start corner region — they are the opponent's pieces moving toward their target (my start corner)."

## 4. 影响

- 模型在前 ~50 个回合里**对局势的判断是错的**，包括一次"对手即将获胜"的误判
- 它需要额外消耗推理去纠正我们给的错误信息（本可以用于规划）
- 更隐蔽的后果：**我们无法区分"模型不会玩"和"我们给的信息是错的"** —— 这直接污染了这次实验的结论

## 5. 修复方案

改成对称的两行，各自统计"棋子进入**自己**目标区"的数量：

```text
Your progress: 12/20 pieces in target.
Opponent progress: 7/20 pieces in target (their target is your starting corner).
```

实现上：对手的目标区 = `sd["targets"][str(3 - player)]`（等于 `sd["bases"][str(player)]`）。

同时建议保留"敌方棋子在我方目标区内"的信息，但**换个明确的标签**，例如：

```text
Enemy pieces currently occupying your target region: 3
```

因为它确实是决策相关信息（挡路 / 可当跳板），只是不能被包装成"对手进度"。

## 6. 修复记录

**2026-10-02 已修复**，`render_state()` 现在输出：

```text
Your progress: 12/20 of your pieces are in your target region.
Opponent progress: 7/20 of their pieces are in their target region (their target is your starting corner).
Enemy pieces currently occupying YOUR target region: 3.
```

- 两个进度各自统计"棋子进入**自己**目标区"，语义对称
- 对手目标区位置用文字点明（"their target is your starting corner"），避免模型自己猜
- 敌方占位信息保留，但换成独立一行、标签明确
- 回归测试：`tests/test_llm_state_render.py`，其中
  `test_start_progress_is_zero_for_both_sides` 直接针对本缺陷 —— 旧实现在开局会输出「对手 4/4」，
  该断言会立刻失败

**正式 A 局**（`runs/llm_a_official/20261002_223539`）跑在修复前的版本上，记录**保持原样不改**。
它的价值反而在于：这是一份"接口语义缺陷如何影响 LLM 表现"的完整证据，
模型从第 1 回合就在跟错误标签搏斗，全过程都在 `llm/*.jsonl` 的思考原文里。
