# 第 4 章测距仿真

生成 `body/chap04.tex` 所用仿真图。脚本按论文中式 (4-13)(4-14)(4-15)(4-16)(4-18)(4-20)
实现分层声线正演与二分反演，不依赖除 numpy/matplotlib 以外的库。

## 运行

```bash
python scripts/sim_ranging/sim_ranging.py
```

输出到 `figures/sim_*.pdf`：

| 文件 | 用于 | 说明 |
|---|---|---|
| `sim_svp_simplify.pdf` | 图 4.6 | 原始剖面与两组 DM-EICPS 简化折线，含细结构放大插图 |
| `sim_svp_bias.pdf` | 图 4.7 | 简化引起的距离偏差随特征点数变化 |
| `sim_monotone.pdf` | 图 4.2 | 传播时间与水平距离随初始掠射角的单调关系 |
| `sim_bisect.pdf` | 图 4.3 | 二分残差收敛过程 |
| `sim_depth_interval.pdf` | 图 4.5 | 深度不确定度引起的水平距离与斜距区间宽度 |
| `sim_baselines.pdf` | 图 4.8 | 四组基线的距离误差随真实斜距变化 |
| `sim_svp_tradeoff.pdf` | — | 双面板版（偏差 + 运算次数），正文用小图替代 |

## 参数与假设

- **声速剖面为典型取值，不是实测值**。`profile_munk` 为 Munk 深海剖面，
  `profile_measured` 在其上叠加确定性细结构，`profile_thermocline` 为强跃层剖面。
- 几何：$z_a=10\,\mathrm{m}$，$z_b=1510\,\mathrm{m}$，斜距 $1.6$–$5\,\mathrm{km}$。
- 时延误差：$\sigma_t=20\,\mu\mathrm{s}$ 高斯抖动 + 6% 概率的 $60\,\mu\mathrm{s}$
  单边偏移，用于模拟首达径漏检；这是对检测误差的简化近似，不是多径信道的完整建模。
- 蒙特卡洛每点 400 次，随机种子固定为 2024，结果可复现。

## 替换为实测参数

1. 把 `profile_munk` 换成读取实测剖面的函数（返回 `(s, d)` 插值结果即可）；
2. 改 `CONFIG` 中的 `za`、`zb`、`R_list`、`sigma_t`、`p_late`；
3. 重跑脚本，图与正文数值需同步更新——正文中的绝对值均以当前脚本输出为准，
   不可直接沿用。
