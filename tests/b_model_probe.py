"""B 模型探索脚本：先验证 FCC 点集与外部金字塔形状。

这不是正式测试，也不是正式几何实现。
运行：
    python tests/b_model_probe.py
"""

from __future__ import annotations

from collections import Counter
from itertools import product
from typing import Iterable, List, Tuple

Point = Tuple[int, int, int]

FCC12 = [
    (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
    (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
    (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1),
]


def interior_parity_points(k: int, parity: int = 0) -> List[Point]:
    """内部正方体 [-k,k]^3 中满足 x+y+z 奇偶性的点。"""
    return [
        (x, y, z)
        for x in range(-k, k + 1)
        for y in range(-k, k + 1)
        for z in range(-k, k + 1)
        if (x + y + z) % 2 == parity
    ]


def square_pyramid_face(k: int, axis: int, sign: int, parity: int | None = None) -> List[Point]:
    """生成一个外部四棱锥候选。

    以 k=2（5x5x5）为例，+x 侧按：
      x=3: 4×4
      x=4: 3×3
      x=5: 2×2
      x=6: 1×1
    的方式向外衰减。
    parity=None 表示保留全部整数点；parity=0/1 表示只保留 FCC 子晶格。
    """
    points: List[Point] = []
    # 从紧贴立方体面外侧开始，层大小从 (2k) 衰减到 1
    for layer in range(1, 2 * k + 1):
        side = 2 * k + 1 - layer
        half = side // 2
        # 让每层关于 0 对称
        start = -half
        end = half
        # 非对称偏移：+轴时从 -k 开始也可以，这里先试“居中”版本
        if layer == 1 and k == 2:
            # 4×4 居中于 -2..1 或 -1..2，先取 -2..1 看看效果
            start = -k
            end = k - 1
        else:
            # 后续层向中心收缩
            start = -((side - 1) // 2)
            end = (side - 1) // 2
            if side % 2 == 0:
                end += 1

        other_axes = [i for i in range(3) if i != axis]
        for a in range(start, end + 1):
            for b in range(start, end + 1):
                coord = [0, 0, 0]
                coord[axis] = sign * (k + layer)
                coord[other_axes[0]] = a
                coord[other_axes[1]] = b
                p = tuple(coord)
                if parity is None or sum(p) % 2 == parity:
                    points.append(p)
    return points


def six_pyramids(k: int, parity: int | None) -> List[Point]:
    points: List[Point] = []
    for axis in range(3):
        for sign in (1, -1):
            points.extend(square_pyramid_face(k, axis, sign, parity))
    return points


def summary(name: str, points: Iterable[Point]) -> None:
    pts = list(points)
    print(f"\n=== {name} ===")
    print(f"点数: {len(pts)}")
    for axis_name, idx in [("x", 0), ("y", 1), ("z", 2)]:
        by_abs = Counter(abs(p[idx]) for p in pts)
        print(f"  按 |{axis_name}| 分层: {dict(sorted(by_abs.items()))}")
    # 打印 +x 方向的层分布作为代表
    x_pos = [p for p in pts if p[0] > 2]
    by_x = Counter(p[0] for p in x_pos)
    print(f"  +x 外部层: {dict(sorted(by_x.items()))}")
    if x_pos:
        for x in sorted(by_x):
            layer = [p for p in x_pos if p[0] == x]
            ys = sorted({p[1] for p in layer})
            zs = sorted({p[2] for p in layer})
            print(f"    x={x}: 数量 {len(layer)}, y范围 {ys[:1]}..{ys[-1:]}, z范围 {zs[:1]}..{zs[-1:]}")


def main() -> None:
    k = 2
    print("B 模型探索：k =", k, " => 5×5×5")

    interior_even = interior_parity_points(k, 0)
    interior_odd = interior_parity_points(k, 1)
    summary("内部偶子晶格 FCC", interior_even)
    summary("内部奇子晶格", interior_odd)

    full_pyr = six_pyramids(k, None)
    summary("六个外部四棱锥（全整数点）", full_pyr)

    even_pyr = six_pyramids(k, 0)
    summary("六个外部四棱锥（仅偶子晶格）", even_pyr)

    # 只保留偶子晶格的完整棋盘 = 内部偶 + 外部偶
    combined_even = interior_even + even_pyr
    summary("内部偶 + 外部偶（单一 FCC 子晶格）", combined_even)

    # 展示 +x 第一个外接层的坐标样本
    print("\n+x 外部层坐标样本（全整数点）：")
    samples = sorted(
        p for p in six_pyramids(k, None) if p[0] == 3
    )[:24]
    for p in samples:
        print("  ", p)


if __name__ == "__main__":
    main()
