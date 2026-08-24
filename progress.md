# PolyJump 进度日志

## 2026-08-24

- 创建 `poly-jump` 项目目录
- 确定项目名：`poly-jump`
- 确定定位：可配置三维跳棋游戏框架，先发布游戏；小 AI 作为可选扩展
- 确定技术栈：
  - 后端 Python：fastapi + uvicorn + pydantic + numpy
  - 前端：HTML + Three.js
- 完成讨论：
  - A 模型 / B 模型几何
  - 二维跳棋规则参考
  - 三维跳棋移动向量化
  - 各类规则开关
  - 前端主菜单与游戏界面分离
- 开始编写设计文档

## 文档完成

已在 `docs/` 下编写完整设计文档：

- README.md
- 01-rules-2d-checkers.md
- 02-rules-3d-jump-chess.md
- 03-geometry-model-a.md
- 04-geometry-model-b.md
- 05-configuration.md
- 06-architecture.md
- 07-action-representation.md
- 08-frontend-ui.md
- 09-optional-ai.md
- 10-implementation-guide.md
- 11-references.md

同时更新了根目录 README.md。

## 第一版实现（后端骨架 + A 模型 + 基础移动 + 前端）

已完成：

- 后端目录按职责拆分：
  - `config.py`：PolyJumpConfig / MovementConfig / CaptureConfig / GoalConfig
  - `directions.py`：6/8/12/14/18/20/26 向 + 自定义向量展开
  - `geometry/`：Geometry 接口、GeometryA、GeometryB(TODO)
  - `board.py`：棋盘状态与初始布局
  - `moves/`：StepGenerator / JumpGenerator / MoveGenerator / MoveValidator
  - `rules/`：MoveApplier / CaptureHandler / Winner
  - `game_state.py`：单局状态管理
  - `ai.py`：RandomAI
- A 模型：
  - 正方体 / 长方体
  - 原点在角上
  - 2 人对角基地 + 三角金字塔（4 层 = 20 子）
  - 普通移动 / 单跳 / 连跳
- FastAPI：
  - `POST /api/game/new`
  - `GET /api/game/{id}`
  - `GET /api/game/{id}/legal-moves`
  - `POST /api/game/{id}/move`
  - `POST /api/game/{id}/ai-move`
  - `GET /api/config`
  - 挂载 `frontend/` 静态页面
- 前端：
  - 主菜单：几何、棋盘大小、人数、方向集、规则开关
  - Three.js 游戏页：点阵、路线、棋子、旋转/缩放、选子高亮、合法路径高亮、落子提交
- 测试：
  - `tests/test_moves.py`：普通移动、单跳、连跳、FREE_STOP / FORCE_ALL、禁跳
  - `pytest -q -p no:cacheprovider` 通过（6 passed）

## UI 第二轮反馈调整

- 主菜单改为白底黑字黑白灰 UI，排布更整齐
- 方向集改为 6 / 12 / 8 三个独立开关，自动组合并显示总方向数
- 棋子层数改为自动计算：`max(2, floor(最短边 / 2))`，后端同步加层数上限校验
- 3D 场景：白底、黑点、极淡灰/淡彩网格线；棋子改为 8 种高区分度彩色
- 网格线透明度进一步降低，方向组之间保留极淡色差方便观察

## 第三轮反馈调整

- 修正 A 模型金字塔方向：层 k = dx+dy+dz==k，金字塔尖落在正方体角上
- 新增 `tests/test_geometry.py` 验证金字塔层数 1/3/6/10 与角点方向
- 前端性能优化：
  - 所有空格点合并为单个 `THREE.Points`
  - 同方向组路线合并为 `THREE.LineSegments`
  - 缩小空白点尺寸，限制 pixelRatio，降低 H5 环境卡顿

## 第四轮反馈调整

- 相机只在首次进入对局时居中，后续回合/移动不再自动改变视角
- HUD 新增玩家列表：显示全部玩家的颜色和编号，当前行动玩家用黑色圆环高亮

## 当前状态 / 下一步

第一版验收目标已跑通：A 模型、2 人、6 向、普通移动 + 单跳 + 连跳。

待后续实现：

- B 模型（FCC 点阵）完整几何与基地
- 3/4/6/8 人局基地/目标区分配
- `two_step_hop`（空一格跳）
- 吃子模式在真实对局中的完整验证（CAPTURE / MIXED 基础代码已留）
- 前端 AI 按钮 / 对局历史
