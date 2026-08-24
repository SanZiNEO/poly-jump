# 配置

## 1. 配置文件

示例配置位于：

```text
configs/
```

主要配置：

```text
configs/a_2p_6dir.json
configs/a_4p_6dir.json
configs/a_capture.json
configs/b_6p_radius6.json
configs/c_6p_radius6.json
configs/directions.json
```

## 2. 顶层字段

```text
game_name
geometry
board_size
b_radius
c_radius
ep_side
players
direction_set
custom_vectors
movement
capture
goal
initial_layout
scoring
render
```

## 3. geometry

可选值：

```text
A
B
C
D
A_EXT
B_EXT
C_EXT
```

## 4. 方向配置

### 基础方向集

```text
6
8
12
14
18
20
26
```

### 自定义方向

自定义向量会展开为完整方向族：

- 全排列
- 所有非零分量的正负组合

例如：

```text
[2,1,0] -> 24 个方向
[2,2,1] -> 24 个方向
```

方向定义文件：

```text
configs/directions.json
```

后端接口：

```text
GET /api/direction-sets
```

## 5. movement

```text
allow_step
allow_jump
allow_chain
hop_mode: FREE_STOP / FORCE_ALL
two_step_hop
max_chain_length
```

## 6. capture / goal

```text
capture.mode
capture.capture_opponent_only
capture.capture_in_base
goal.objective
goal.target_region
goal.must_fill_all_cells
goal.first_to_finish_wins
```

## 7. scoring

```text
scoring.enabled
scoring.chain_jump_points
scoring.chain_temp
scoring.chain_max_scoring
scoring.capture_points
scoring.target_zone_points
scoring.first_finish_reward
scoring.survivor_piece_points
```

`chain_max_scoring` 只限制连跳**计分次数**，不限制连跳本身长度。
