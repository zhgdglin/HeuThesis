# -*- coding: utf-8 -*-
"""第 4 章测距仿真脚本。

按 body/chap04.tex 中式 (4-13)(4-14)(4-15)(4-16)(4-18)(4-20) 的分层正演与
二分反演实现，生成第 4 章所需的图与表数据。

用法：
    python scripts/sim_ranging/sim_ranging.py

替换实测参数：只需改 profile_*() 与 CONFIG，其余流程不变。

约定与正文一致：z 为深度（向下为正）；theta 为声线与水平方向夹角；
s 为声速；p = cos(theta)/s 为水平慢度；q_i = sin(theta_i)。
"""

from __future__ import annotations

import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["SimSun", "Songti SC", "Noto Serif CJK SC", "DejaVu Serif"],
    "font.size": 9,
    "axes.linewidth": 0.6,
    # SimSun 不含 U+2212，直接写负号会出现替代字形；刻度统一走 mathtext
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "legend.frameon": False,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})


def sci_axis(ax, axis="y"):
    """对数轴刻度改用 mathtext 的 $10^{-n}$。

    默认的 LogFormatter 以 \\mathdefault 调用正文字体，SimSun 无负号字形，
    会出现替代符号；显式写 mathtext 可绕开该回退。
    """
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(mticker.LogLocator(base=10.0))
    a.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: r"$10^{%d}$" % int(round(np.log10(v))))
    )
    a.set_minor_formatter(mticker.NullFormatter())

import matplotlib.ticker as mticker

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FIGDIR = os.path.join(ROOT, "figures")

# --------------------------------------------------------------------------
# 声速剖面（典型取值，非实测）
# --------------------------------------------------------------------------
def profile_iso(z):
    return np.full_like(np.asarray(z, float), 1500.0)


def profile_munk(z):
    """Munk 深海剖面：声道轴 1300 m 处 1500 m/s。"""
    z = np.asarray(z, float)
    zeta = 2.0 * (z - 1300.0) / 1300.0
    return 1500.0 * (1.0 + 0.00737 * (zeta - 1.0 + np.exp(-zeta)))


def profile_thermocline(z):
    """强跃层剖面：表层约 1530 m/s，300 m 处降至 1482 m/s，其下缓慢回升。"""
    z = np.asarray(z, float)
    upper = 1530.0 - 48.0 * np.tanh(z / 120.0) / np.tanh(2.5)
    lower = 1482.0 + 0.012 * (z - 300.0)
    return np.where(z <= 300.0, upper, lower)


def profile_measured(z):
    """模拟实测剖面：Munk 主轮廓叠加米级细结构（确定性扰动，可复现）。"""
    z = np.asarray(z, float)
    fine = (
        1.6 * np.sin(2 * np.pi * z / 210.0)
        + 0.9 * np.sin(2 * np.pi * z / 63.0 + 0.7)
        + 0.45 * np.sin(2 * np.pi * z / 23.0 + 1.9)
    )
    return profile_munk(z) + fine


PROFILES = {
    "iso": ("常声速", profile_iso),
    "munk": ("典型深海", profile_munk),
    "thermo": ("强跃层", profile_thermocline),
}

# --------------------------------------------------------------------------
# 分层正演：式 (4-13)(4-14)，零梯度按式 (4-15)
# --------------------------------------------------------------------------
def discretize(profile, z_top, z_bot, dz=1.0):
    d = np.arange(z_top, z_bot + 0.5 * dz, dz)
    if d[-1] < z_bot - 1e-9:
        d = np.append(d, z_bot)
    return d, profile(d)


def forward(theta0, d, s):
    """返回水平距离 H 与单程传播时间 T；theta0 支持一维数组。"""
    theta0 = np.atleast_1d(np.asarray(theta0, float))
    p = np.cos(theta0) / s[0]

    dd = np.diff(d)
    g = np.diff(s) / dd
    s_prev, s_next = s[:-1], s[1:]

    q = np.sqrt(np.maximum(1.0 - (p[:, None] * s_next[None, :]) ** 2, 0.0))
    q_prev = np.sqrt(np.maximum(1.0 - (p[:, None] * s_prev[None, :]) ** 2, 0.0))

    lin = np.abs(g) > 1e-12
    gl = np.where(lin, g, 1.0)

    with np.errstate(divide="ignore", invalid="ignore"):
        dh_lin = (q_prev - q) / (p[:, None] * gl[None, :])
        dt_lin = np.log((s_next[None, :] / s_prev[None, :]) * (1.0 + q_prev) / (1.0 + q)) / gl[None, :]

    q_prev_safe = np.where(q_prev > 1e-12, q_prev, 1.0)
    dh_zero = dd[None, :] * (p[:, None] * s_prev[None, :]) / q_prev_safe
    dt_zero = dd[None, :] / (s_prev[None, :] * q_prev_safe)

    dh = np.where(lin[None, :], dh_lin, dh_zero)
    dt = np.where(lin[None, :], dt_lin, dt_zero)
    return dh.sum(axis=1), dt.sum(axis=1)


def theta_range(d, s):
    """可搜索掠射角区间下界，式 (4-16)。"""
    theta_c = np.arccos(min(1.0, s[0] / s.max()))
    return max(theta_c, 1e-6), np.pi / 2.0 - 1e-6


def bisect(tau_target, d, s, eps_t=1e-6, jmax=80):
    """式 (4-18)：由单程时延反解初始掠射角，返回角度与残差历史。"""
    tau = np.atleast_1d(np.asarray(tau_target, float))
    tc, tu = theta_range(d, s)
    lo = np.full(tau.shape, tc)
    hi = np.full(tau.shape, tu)
    hist = []
    for _ in range(jmax):
        mid = 0.5 * (lo + hi)
        _, T = forward(mid, d, s)
        e = T - tau
        hist.append(np.abs(e).max())
        lo = np.where(e > 0, mid, lo)
        hi = np.where(e > 0, hi, mid)
        if np.all(np.abs(e) < eps_t):
            break
    mid = 0.5 * (lo + hi)
    _, T = forward(mid, d, s)
    return mid, T - tau, np.array(hist)


def invert_range(tau, za, zb, d, s, **kw):
    """式 (4-20)：由单程时延反演斜距。"""
    theta, resid, hist = bisect(tau, d, s, **kw)
    H, _ = forward(theta, d, s)
    return np.sqrt(H ** 2 + (zb - za) ** 2), theta, resid, hist


def tau_of_range(R, za, zb, d, s, n=20000):
    """给定真实斜距，反算对应的单程时延。

    先在 H 上解出精确角度（H 同样关于 theta 单调），再前推得 T，
    避免在时延网格上插值引入的不一致（插值误差可达厘米量级，
    会掩盖剖面简化本身的毫米级偏差）。
    """
    H_target = np.sqrt(R ** 2 - (zb - za) ** 2)
    tc, tu = theta_range(d, s)
    lo, hi = tc, tu
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        H, _ = forward(mid, d, s)
        if H[0] > H_target:
            lo = mid
        else:
            hi = mid
    theta = 0.5 * (lo + hi)
    _, T = forward(theta, d, s)
    return float(T[0])


def equivalent_speed(profile, za, zb, dz=0.5):
    """等效声速：c_e = Δz / ∫dz/c（沿深度的调和平均）。"""
    z = np.arange(za, zb, dz)
    integ = np.trapezoid(1.0 / profile(z), z) if hasattr(np, "trapezoid") else np.trapz(1.0 / profile(z), z)
    return (zb - za) / integ


# --------------------------------------------------------------------------
# DM-EICPS 剖面简化
# --------------------------------------------------------------------------
def dm_eicps(d, s, n_target):
    """最大距离缩减准则的等间隔控制点搜索。"""
    keep = [0, len(d) - 1]
    while len(keep) < n_target:
        idx = np.array(sorted(keep))
        dev = np.abs(s - np.interp(d, d[idx], s[idx]))
        mask = np.ones(len(d), bool)
        mask[idx] = False
        if not mask.any():
            break
        keep.append(int(np.argmax(np.where(mask, dev, -np.inf))))
    idx = np.array(sorted(set(keep)))
    return d[idx], s[idx]


# --------------------------------------------------------------------------
# 图：声速剖面与简化折线
# --------------------------------------------------------------------------
def fig_svp(z_top=0.0, z_bot=3000.0, R=3000.0):
    """剖面简化的几何形态与距离偏差，合并为双栏图 (a)(b)。"""
    d, s = discretize(profile_measured, z_top, z_bot, 1.0)
    ds, ss = dm_eicps(d, s, 20)
    ds2, ss2 = dm_eicps(d, s, 60)

    # (b) 距离偏差：在斜距上取 RMS，避免单一距离处细结构抵消造成的偶然零值
    # 注意 R 必须大于深度差 |z_b - z_a|，否则 H 无实数解
    R_lo = abs(z_bot - z_top) * 1.07
    is_list = np.array([6, 8, 10, 12, 16, 20, 30, 40, 60, 80, 120], float)
    R_probe = np.linspace(R_lo, 5200.0, 18)
    bias = []
    for Is in is_list:
        dsi, ssi = dm_eicps(d, s, int(Is))
        errs = []
        for R in R_probe:
            tau = tau_of_range(R, z_top, z_bot, d, s)
            ref = invert_range(tau, z_top, z_bot, d, s)[0][0]
            est = invert_range(tau, z_top, z_bot, dsi, ssi)[0][0]
            errs.append(est - ref)
        bias.append(float(np.sqrt(np.mean(np.square(errs)))))
    bias = np.array(bias)

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(6.4, 3.9), gridspec_kw={"width_ratios": [1.0, 1.0]}
    )

    ax.plot(s, d, "-", lw=0.8, color="0.62", label="原始（$I=3000$）")
    ax.plot(ss2, ds2, "-", lw=1.1, color="#1f6f8b", label="简化（$I_s=60$）")
    ax.plot(ss, ds, "o-", ms=1.8, lw=0.9, color="#c0392b", label="简化（$I_s=20$）")
    ax.invert_yaxis()
    ax.set_xlabel("声速 $s$ / (m·s$^{-1}$)")
    ax.set_ylabel("深度 $z$ / m")
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(loc="upper left", fontsize=6.5)
    ax.set_xlim(1490, 1532)
    ax.text(0.02, 0.02, "(a)", transform=ax.transAxes, fontsize=9, va="bottom")

    inset = ax.inset_axes([0.55, 0.42, 0.44, 0.30])
    lo, hi = 1180.0, 1330.0
    m = (d >= lo) & (d <= hi)
    inset.plot(s[m], d[m], "-", lw=0.8, color="0.62")
    m2 = (ds2 >= lo) & (ds2 <= hi)
    inset.plot(ss2[m2], ds2[m2], "-", lw=1.0, color="#1f6f8b")
    m3 = (ds >= lo) & (ds <= hi)
    inset.plot(ss[m3], ds[m3], "o-", ms=1.5, lw=0.8, color="#c0392b")
    inset.invert_yaxis()
    inset.tick_params(labelsize=5.2, length=1.6, pad=1)
    inset.grid(alpha=0.3, lw=0.3)

    ax2.plot(is_list, bias, "o-", ms=3.0, lw=1.0, color="#c0392b")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    sci_axis(ax2, "x")
    sci_axis(ax2, "y")
    ax2.set_xlabel("简化特征点数 $I_s$")
    ax2.set_ylabel("距离偏差 RMS / m")
    ax2.grid(alpha=0.25, lw=0.4, which="both")
    ax2.text(0.02, 0.92, "(b)", transform=ax2.transAxes, fontsize=9, va="top")

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "sim_svp.pdf"))
    plt.close(fig)
    return dict(zip(is_list.tolist(), np.round(bias, 4).tolist()))


# --------------------------------------------------------------------------
# 图：单调性验证
# --------------------------------------------------------------------------
def fig_monotone(za=10.0, zb=1510.0):
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.8))
    colors = {"iso": "0.55", "munk": "#c0392b", "thermo": "#1f6f8b"}
    styles = {"iso": "-", "munk": "-", "thermo": "--"}
    for key, (label, prof) in PROFILES.items():
        d, s = discretize(prof, za, zb, 2.0)
        tc, _ = theta_range(d, s)
        # theta0 -> 0 表示近垂直出射，H 发散，绘图从 3° 起
        th = np.linspace(max(tc, np.radians(3.0)), np.radians(88.0), 240)
        H, T = forward(th, d, s)
        axes[0].plot(np.degrees(th), T * 1e3, styles[key], color=colors[key], lw=1.1, label=label)
        axes[1].plot(np.degrees(th), H / 1e3, styles[key], color=colors[key], lw=1.1)
    axes[0].set_ylabel("单程传播时间 $T$ / ms")
    axes[1].set_ylabel("水平距离 $H$ / km")
    axes[0].set_ylim(0, 8000)
    axes[1].set_ylim(0, 12)
    for ax in axes:
        ax.set_xlabel("初始掠射角 $\\theta_0$ / (°)")
        ax.set_xlim(0, 90)
        ax.grid(alpha=0.25, lw=0.4)
    axes[0].legend(fontsize=7.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "sim_monotone.pdf"))
    plt.close(fig)


# --------------------------------------------------------------------------
# 图：二分收敛
# --------------------------------------------------------------------------
def fig_bisect(za=10.0, zb=1510.0, R=3000.0):
    d, s = discretize(profile_munk, za, zb, 1.0)
    tau = tau_of_range(R, za, zb, d, s)
    _, theta_opt, _, hist = invert_range(tau, za, zb, d, s)

    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    j = np.arange(1, len(hist) + 1)
    ax.semilogy(j, hist * 1e6, "o-", ms=3, lw=0.9, color="#1f6f8b")
    ax.set_xlabel("迭代次数 $j$")
    ax.set_ylabel("时间残差 $|e|$ / μs")
    sci_axis(ax, "y")
    ax.grid(alpha=0.25, lw=0.4, which="both")
    ax.set_xlim(0, len(hist) + 1)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "sim_bisect.pdf"))
    plt.close(fig)
    return len(hist), float(np.degrees(theta_opt[0]))


# --------------------------------------------------------------------------
# 基线误差
# --------------------------------------------------------------------------
CONFIG = dict(
    za=10.0,
    zb=1510.0,
    R_list=np.arange(1600.0, 5001.0, 200.0),
    n_mc=400,
    sigma_t=20e-6,
    p_late=0.06,
    seed=2024,
)


def run_baselines(cfg=CONFIG):
    rng = np.random.default_rng(cfg["seed"])
    za, zb = cfg["za"], cfg["zb"]
    d_full, s_full = discretize(profile_munk, za, zb, 1.0)
    d_simp, s_simp = dm_eicps(d_full, s_full, 20)
    c_eq = equivalent_speed(profile_munk, za, zb)
    c0 = 1500.0

    res = {k: [] for k in ("B0", "B1", "B2", "B3")}
    for R in cfg["R_list"]:
        tau = tau_of_range(R, za, zb, d_full, s_full)
        noise = rng.normal(0.0, cfg["sigma_t"], cfg["n_mc"])
        late = rng.random(cfg["n_mc"]) < cfg["p_late"]
        noise[late] += 3.0 * cfg["sigma_t"]      # 漏检首达径 → 时延偏大
        tau_m = tau + noise

        res["B0"].append(c0 * tau_m)
        res["B1"].append(c_eq * tau_m)
        res["B2"].append(invert_range(tau_m, za, zb, d_simp, s_simp)[0])
        res["B3"].append(invert_range(tau_m, za, zb, d_full, s_full)[0])

    return {k: np.array(v) for k, v in res.items()}, c_eq


def fig_baselines(res, cfg=CONFIG):
    R_list = cfg["R_list"]
    spec = [
        ("B0", "B0 常声速模型", "0.5", "-"),
        ("B1", "B1 等效声速修正", "#1f6f8b", "--"),
        ("B2", "B2 简化剖面 + 二分（本文）", "#c0392b", "-"),
        ("B3", "B3 全分层 + 二分", "0.15", ":"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.8))
    for key, lab, col, ls in spec:
        err = res[key] - R_list[:, None]
        axes[0].plot(R_list / 1e3, np.sqrt((err ** 2).mean(axis=1)), ls, color=col, lw=1.1, label=lab)
        axes[1].plot(R_list / 1e3, err.mean(axis=1), ls, color=col, lw=1.1)
    axes[0].set_ylabel("距离 RMSE / m")
    axes[1].set_ylabel("距离偏差 / m")
    for ax in axes:
        ax.set_xlabel("真实斜距 $R$ / km")
        ax.grid(alpha=0.25, lw=0.4)
    axes[0].set_ylim(bottom=0)
    axes[0].legend(fontsize=7, loc="upper left")
    axes[1].axhline(0, lw=0.6, color="0.4")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "sim_baselines.pdf"))
    plt.close(fig)

    report = {}
    for key, *_ in spec:
        err = res[key] - R_list[:, None]
        report[key] = dict(
            rmse=float(np.sqrt((err ** 2).mean())),
            bias=float(err.mean()),
            maxabs=float(np.abs(err).max()),
        )
    return report


# --------------------------------------------------------------------------
# 图：深度区间宽度
# --------------------------------------------------------------------------
def fig_depth_interval(za=10.0, zb=1510.0, R=3000.0, dz_step=1.0):
    """深度不确定度引起的区间。对单应答器测距，时延固定时斜距 R 几乎不随
    z_b 变化（声线弧长近似守恒，几何与声线弯曲相互抵消），真正敏感的是水平
    距离 H，故两种区间同图给出。每次按新的 z_b 重新离散，因为 z_b 改变会同时
    改变累加层数与最后一层的截断位置。"""
    d0, s0 = discretize(profile_munk, za, zb, dz_step)
    tau = tau_of_range(R, za, zb, d0, s0)

    dz_list = np.array([0, 1, 2, 3, 5, 8, 10, 15, 20, 30], float)
    wR, wH = [], []
    for dz in dz_list:
        vals_R, vals_H = [], []
        for z in (zb - dz, zb + dz):
            d, s = discretize(profile_munk, za, z, dz_step)
            theta = bisect(tau, d, s)[0]
            H, _ = forward(theta, d, s)
            vals_H.append(float(H[0]))
            vals_R.append(float(np.sqrt(H[0] ** 2 + (z - za) ** 2)))
        wR.append(abs(vals_R[1] - vals_R[0]))
        wH.append(abs(vals_H[1] - vals_H[0]))

    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    ax.plot(dz_list, wH, "o-", ms=3.4, lw=1.0, color="#c0392b",
            label="水平距离区间 $H_{\\max}-H_{\\min}$")
    ax.plot(dz_list, wR, "s--", ms=3.0, lw=1.0, color="#1f6f8b",
            label="斜距区间 $R_{\\max}-R_{\\min}$")
    ax.set_xlabel("深度不确定度 $\\delta z_b$ / m")
    ax.set_ylabel("区间宽度 / m")
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "sim_depth_interval.pdf"))
    plt.close(fig)
    return {
        "dz": dz_list.tolist(),
        "width_H": np.round(wH, 3).tolist(),
        "width_R": np.round(wR, 3).tolist(),
    }


# --------------------------------------------------------------------------
# 图：剖面简化的偏差与运算量
# --------------------------------------------------------------------------
def fig_svp_tradeoff(z_top=0.0, z_bot=3000.0, R=3000.0):
    """表 4.2 用的数据（与 fig_svp 的 (b) 栏同一口径）。"""
    d, s = discretize(profile_measured, z_top, z_bot, 1.0)
    R_lo = abs(z_bot - z_top) * 1.07
    R_probe = np.linspace(R_lo, 5200.0, 18)
    is_list = np.array([6, 8, 10, 12, 16, 20, 30, 40, 60, 80, 120], float)
    out = {}
    for Is in is_list:
        dsi, ssi = dm_eicps(d, s, int(Is))
        errs = []
        for Rr in R_probe:
            tau = tau_of_range(Rr, z_top, z_bot, d, s)
            ref = invert_range(tau, z_top, z_bot, d, s)[0][0]
            est = invert_range(tau, z_top, z_bot, dsi, ssi)[0][0]
            errs.append(est - ref)
        out[float(Is)] = float(np.sqrt(np.mean(np.square(errs))))
    return {k: round(v, 4) for k, v in out.items()}


# --------------------------------------------------------------------------
# R1 自检
# --------------------------------------------------------------------------
def check_r1(za=10.0, zb=1510.0, R=3000.0):
    d, s = discretize(profile_iso, za, zb, 1.0)
    tau = R / 1500.0
    R_est = invert_range(tau, za, zb, d, s)[0][0]
    return R, float(R_est), float(abs(R_est - R))


def main():
    os.makedirs(FIGDIR, exist_ok=True)

    print("[1/7] R1 self-check")
    R, R_est, err = check_r1()
    print("      R_true=%.3f  R_est=%.6f  |dR|=%.2e m" % (R, R_est, err))

    print("[2/7] svp")
    fig_svp()

    print("[3/7] monotone")
    fig_monotone()

    print("[4/7] bisect")
    n_iter, theta_opt = fig_bisect()
    print("      iterations = %d, theta* = %.3f deg" % (n_iter, theta_opt))

    print("[5/7] baselines")
    res, c_eq = run_baselines()
    print("      c_eq = %.3f m/s" % c_eq)
    report = fig_baselines(res)
    for k, v in report.items():
        print("      %s  RMSE=%.3f  bias=%+.3f  max=%.3f m" %
              (k, v["rmse"], v["bias"], v["maxabs"]))

    print("[6/7] depth interval")
    print("      ", fig_depth_interval())

    print("[7/7] svp tradeoff")
    print("      ", fig_svp_tradeoff())

    print("figures ->", FIGDIR)


if __name__ == "__main__":
    main()
