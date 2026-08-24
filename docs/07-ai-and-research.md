# AI / 研究接口

PolyJump 本身是游戏，不包含 AI 训练逻辑。
但提供干净接口，方便外部程序接入自己的 AI。

## 当前 AI

- ScoringAwareAI（默认）
  - 读取当前对局 ScoringConfig
  - 吃子分、进入目标区分、连跳计分上限都按配置计算
  - 带图距离进步与回跳惩罚
- GraphProgressAI
  - 用真实图距离（BFS）评估抽象几何下的前进收益
  - 连跳奖励
  - 吃子奖励
  - 回跳惩罚
- ProgressAI
  - 连跳奖励 + 吃子奖励 + 回跳惩罚（使用曼哈顿距离）
- GreedyAI
  - 简单贪心
- RandomAI
  - 随机选择一条合法路径

## AI 玩家模式

- 主菜单可设置哪些玩家是 AI
- 游戏内可随时切换玩家为 AI / 人类
- AI 轮到自动走
- 人类轮到自动停止
- 全部 AI 可自动对弈到结束

## 建议的外部 AI 接入

```python
from backend.game.config import PolyJumpConfig
from backend.game.env import GameEnv

config = PolyJumpConfig(...)
env = GameEnv(config)

result = env.reset()
while not result.done:
    action = my_agent.choose(result.legal_actions)
    result = env.step(action)
```

## 积分接口

`StepResult` 提供：

```text
scores
temp_scores
```

外部程序可以用积分作为 reward。

## 后续可扩展（不内置）

- GreedyAI
- MCTS
- 小神经网络
- RL / 自博弈

如果外部程序需要：

- 局面克隆
- compact observation
- reward shaping

可以后续在接口层添加，不改变游戏本体。

## 头less

```powershell
python -m backend.game.headless --config configs\a_2p_6dir.json --moves 10
```
