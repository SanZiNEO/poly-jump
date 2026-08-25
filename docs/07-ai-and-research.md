# AI / 研究接口

PolyJump 本身是游戏，不包含 AI 训练逻辑。
但提供干净接口，方便外部程序接入自己的 AI。

## 当前 AI

游戏内置三种纯距离导向 AI（由 `ai_research` 基准评测筛选）：

- GraphDistanceAI（默认）
  - 使用真实图距离 BFS 评估到目标区的最少步数
  - 只以“把棋子送进目标区”为目标，不读取计分
- EuclideanDistanceAI
  - 使用三维欧氏距离选择靠近目标区的走法
- ChebyshevDistanceAI
  - 使用切比雪夫距离选择靠近目标区的走法

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

- MCTS / UCT
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
