# PolyJump 项目计划

## 目标

构建一个可配置的三维跳棋框架：`poly-jump`。

- 后端：Python 规则引擎 + FastAPI
- 前端：HTML + Three.js（点阵/路线/交互）
- 核心：一个框架，两种几何模型（A / B），一套规则开关
- 定位：可发布的三维跳棋游戏框架；AI 仅保留小规模可选扩展（随机 / 贪心 / MCTS）

## 当前阶段

阶段 0：设计文档编写 —— complete

## 阶段列表

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 编写设计文档（几何、规则、配置、架构、前端、实现指南） | complete |
| 1 | 搭建 Python 后端骨架（配置类、规则引擎、API） | complete |
| 2 | 搭建前端骨架（主菜单、游戏界面、Three.js 点阵渲染） | complete |
| 3 | 实现 A 模型几何（正方体 / 长方体） | complete |
| 4 | 实现 B 模型几何（FCC / 菱形十二面体点阵） | pending |
| 5 | 实现移动规则 / 跳跃 / 连跳 / 吃子模式 | in_progress |
| 6 | 实现多玩家配置与胜负判定 | in_progress |
| 7 | 前端交互：画点、画路线、旋转、选子、高亮合法路径、落子 | complete |
| 8 | 简单 AI（随机 / 贪心，可选 MCTS） | in_progress |
| 9 | 棋谱记录、回放、导出 | pending |
| 10 | 发布准备：README、截图、B 站/Hugging Face 部署 | pending |

## 约束与决策记录

- Python 版本：3.11+
- 核心依赖：fastapi、uvicorn[standard]、pydantic、numpy、pytest
- 训练依赖（可选，后续）：torch、pettingzoo、gymnasium、ray[rllib]、tensorboard
- 前端：Three.js，CDN 引入，不做复杂构建
- 主菜单和游戏界面分开：主菜单生成配置，游戏界面使用配置渲染
- 后端返回“合法路径列表”给前端；前端只负责展示和选择，最终移动由后端校验
- A 模型坐标原点在角上；B 模型坐标原点在几何中心
- 所有规则写成开关，同一个框架支撑多规则实例

## 下一步

- 完成所有设计文档
- 更新 README 指向 docs/
- 开始后端骨架
