# -*- coding: utf-8 -*-
"""第 3 章 SFH-MFSK 通信仿真脚本。

按 body/chap03.tex 中的式 (2-9)、(3-10)、(3-13)、(3-19)、(3-22)--(3-26) 实现
链路、同步与并行自适应 Notch 解调，生成第 3.5 节所需的四幅曲线。

用法：
    python scripts/sim_sfh_mfsk/sim_sfh_mfsk.py

输出 figures/sim_sfh_*.pdf。脚本中的全部数值均为模型参数（典型取值），
不是实测值；替换实测参数时只需改 CONFIG、SCENARIOS 与 band_response()。
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["SimSun", "Songti SC", "Noto Serif CJK SC", "DejaVu Serif"],
    "font.size": 9,
    "axes.linewidth": 0.6,
    # SimSun 不含 U+2212，负号统一交给 mathtext
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
    "legend.frameon": False,
    "lines.linewidth": 1.0,
    "lines.markersize": 3.6,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FIGDIR = os.path.join(ROOT, "figures")

# --------------------------------------------------------------------------
# 参数（正文表 3-4 的仿真取值）
# --------------------------------------------------------------------------
CONFIG = {
    "fs": 32000.0,      # 采样率 Hz，覆盖 9--13 kHz 通带
    "f_lo": 9000.0,     # 通带下边沿 Hz
    "f_hi": 13000.0,    # 通带上边沿 Hz
    "df": 250.0,        # MFSK 子频点间隔 Hz
    "M": 4,             # MFSK 进制数
    "n_f": 4,           # 跳频点数
    "f_hop0": 9000.0,   # 最低跳频基准 Hz
    "f_hop_step": 1000.0,  # 跳频基准间隔 Hz，留出 M*df 的过渡带
    "ts": 16e-3,        # MFSK 符号周期 s（N_h = 512），与正文表 3-4 一致
    "tp": 128e-3,       # 单个 LFM 时宽 s，处理增益 10lg(Bp*Tp) = 27.1 dB
    "bp": 4000.0,       # LFM 带宽 Hz
    "r_repeat": 2,      # 前导重复次数 R
    "tgp": 4e-3,        # LFM 间保护间隔 s
    "ns": 4,            # 同步字段跳数
    "nd": 40,           # 数据段跳数
    "mu": 1.0 / 128.0,  # 归一化步长；式 (3-28) 要求 1/(2mu) << N_h=512，
                        # 取 mu=1/128 使收敛时间常数约 128 点，仅占跳时隙 1/4
    "lam": 0.995,       # 功率遗忘因子 lambda
    "eps_p": 1e-6,      # 功率递推防零除
    "gamma_h": 0.05,    # 包络判决门限 gamma_H
    "gamma_lam": 40.0,  # 归一化相关门限 gamma_Lambda，略高于纯噪声累积峰的上界
    "tg": 1e-3,         # 保护间隔 T_g
    "t_wake": 64e-3,    # 唤醒不确定窗口 T_wake
    "warm_frac": 0.5,   # 包络平均跳过的收敛暂态比例，见式 (3-29)
    "t_idle": 128e-3,   # 帧前的空闲监听段，用于估计噪声底 sigma_n^2
    "n_frames": 100,    # 每个蒙特卡洛点的帧数 N_fr，见正文表 3-4
    "workers": 0,       # 并行进程数，0 表示取 os.cpu_count()
    "seed": 2024,
}
CONFIG["th"] = CONFIG["ts"]                        # 慢跳频：一跳一符号
CONFIG["nsamp_hop"] = int(round(CONFIG["th"] * CONFIG["fs"]))
CONFIG["nbits_hop"] = int(round(math.log2(CONFIG["M"])))
# 四条支路占用的带宽为 M*df，跳频基准须等间隔错开，避免相邻跳的子频点重叠
CONFIG["n_f"] = int(min(CONFIG["n_f"],
                        (CONFIG["f_hi"] - CONFIG["f_hop0"] - (CONFIG["M"] - 1) * CONFIG["df"])
                        / CONFIG["f_hop_step"] + 1))
# 式 (3-8)：前导重复次数由唤醒时延、检测长度与保护间隔反推
CONFIG["r_repeat"] = int(math.ceil(
    (CONFIG["t_wake"] + CONFIG["tp"] + CONFIG["tg"]) / (CONFIG["tp"] + CONFIG["tgp"])))

SOUND_SPEED = 1500.0   # m/s
F_CARRIER = 11000.0    # 频偏折算的参考载频 Hz
# S4 的干扰方不知道跳频图案，只能占据一个固定窄带；取通带中部
JAM_F = 11000.0
JAM_BW = 1000.0

# 场景定义：S1 仅 AWGN；S2 加多径；S3 再多普勒；S4 再窄带干扰
SCENARIOS = {
    "S1": dict(alpha=[1.0], tau=[0.0], ripple=False),
    "S2": dict(alpha=[1.0, -0.50, 0.32], tau=[0.0, 1.5e-3, 3.5e-3], ripple=True),
    "S3": dict(alpha=[1.0, -0.50, 0.32], tau=[0.0, 1.5e-3, 3.5e-3], ripple=True, v=0.3),
    "S4": dict(alpha=[1.0, -0.50, 0.32], tau=[0.0, 1.5e-3, 3.5e-3], ripple=True, v=0.3),
}


def band_response(f):
    """通带内换能器与信道的综合起伏（模型参数）。

    S1 保持平坦，使结果可与式 (2-9) 逐点对照；S2 及之后才计入起伏。
    """
    return max(0.20, 1.0 + 0.40 * math.sin(2 * math.pi * (f - 9000.0) / 2600.0))


# --------------------------------------------------------------------------
# 跳频序列：m 序列 + 宽间隔随机平移替代（式 (3-17)(3-18)）
# --------------------------------------------------------------------------
def m_sequence(degree=4):
    """x^4+x+1 的 m 序列，周期 15。"""
    state = [1, 0, 0, 0]
    out = []
    for _ in range(2 ** degree - 1):
        out.append(state[-1])
        state = [state[3] ^ state[0]] + state[:3]
    return out


def hopping_sequence(length, n_f, d_min=2, seed=0):
    """候选频隙由 m 序列状态给出，再按门限做确定性随机替代。"""
    bits = m_sequence(4)
    rng = np.random.default_rng(seed)
    cand = [sum(bits[(k + j) % len(bits)] << j for j in range(4)) % n_f
            for k in range(length)]
    out = [cand[0]]
    for k in range(1, length):
        if abs(cand[k] - out[-1]) >= d_min:
            out.append(cand[k])
        else:
            allowed = [c for c in range(n_f) if abs(c - out[-1]) >= d_min]
            out.append(int(rng.choice(allowed)) if allowed else cand[k])
    return np.array(out, dtype=int)


def hop_frequencies(cfg, n_f=None):
    n = cfg["n_f"] if n_f is None else n_f
    return cfg["f_hop0"] + np.arange(n) * cfg["f_hop_step"]


# --------------------------------------------------------------------------
# 波形
# --------------------------------------------------------------------------
def lfm_waveform(cfg):
    n = int(round(cfg["tp"] * cfg["fs"]))
    t = np.arange(n) / cfg["fs"]
    mu = cfg["bp"] / cfg["tp"]
    return np.exp(1j * 2 * np.pi * (cfg["f_lo"] * t + 0.5 * mu * t * t))


def tone(cfg, freq, n_samp):
    return np.exp(1j * 2 * np.pi * freq * np.arange(n_samp) / cfg["fs"])


def preamble_length(cfg, r_repeat=None):
    r = cfg["r_repeat"] if r_repeat is None else r_repeat
    return r * (int(round(cfg["tp"] * cfg["fs"])) + int(round(cfg["tgp"] * cfg["fs"])))


def gray_encode(m):
    return m ^ (m >> 1)


def gray_decode(g):
    m = 0
    while g:
        m ^= g
        g >>= 1
    return m


def build_frame(bits, pattern, k0, cfg, freqs, r_repeat=None):
    """组帧：R 次重复 LFM 前导 + 同步字段 + 数据段。

    第 k 跳的基准频率由图案给出，即 freqs[pattern[k]]，与式 (3-17)(3-18)
    的“图案决定跨跳频点”一致；数据段的符号索引按 Gray 映射编码。
    """
    p = lfm_waveform(cfg)
    gap = np.zeros(int(round(cfg["tgp"] * cfg["fs"])), complex)
    parts = []
    for _ in range(cfg["r_repeat"] if r_repeat is None else r_repeat):
        parts += [p, gap]
    n_hop = cfg["nsamp_hop"]
    for j in range(cfg["ns"]):
        parts.append(tone(cfg, freqs[pattern[(k0 + j) % len(pattern)]], n_hop))
    for j in range(cfg["nd"]):
        sym = bits[j * cfg["nbits_hop"]:(j + 1) * cfg["nbits_hop"]]
        m = gray_encode(int("".join(str(b) for b in sym), 2))
        f = freqs[pattern[(k0 + cfg["ns"] + j) % len(pattern)]] + m * cfg["df"]
        parts.append(tone(cfg, f, n_hop))
    return np.concatenate(parts)


# --------------------------------------------------------------------------
# 信道
# --------------------------------------------------------------------------
def _delay(wave, shift):
    """按样点数做时延（线性插值，非整数时延也能处理）。"""
    n = np.arange(len(wave))
    idx = n - shift
    return (np.interp(idx, n, wave.real, left=0.0, right=0.0)
            + 1j * np.interp(idx, n, wave.imag, left=0.0, right=0.0))


def _time_scale(wave, eta, out_len=None):
    """时缩：out[n] = in[n*eta]。eta>1 时波形被压缩（频率升高）。

    用加窗 sinc 做带限插值。直接对复基带做线性插值会在 11 kHz 附近把
    单音功率削掉约一半（插值核的等效低通在载频处衰减严重），使多普勒
    场景被人为压低一个量级的信噪比；加窗 sinc 的等效通带远宽于信号带，
    功率与瞬时频率都能保持。
    """
    n = len(wave)
    m = n if out_len is None else out_len
    idx = np.arange(m) * eta
    i0 = np.floor(idx).astype(np.int64)
    frac = idx - i0
    half = 16
    out = np.zeros(m, complex)
    wsum = np.zeros(m)
    for k in range(-half + 1, half + 1):
        t = frac - k
        # Hann 窗截断的 sinc：兼顾旁瓣抑制与计算量
        w = np.sinc(t) * (0.5 + 0.5 * np.cos(np.pi * np.clip(t / half, -1.0, 1.0)))
        src = np.clip(i0 + k, 0, n - 1)
        out += w * wave[src]
        wsum += w
    return out / np.maximum(wsum, 1e-6)


def apply_channel(wave, cfg, scenario, pattern, k0, freqs):
    """按“多径—多普勒时缩—噪声与干扰”的顺序作用（与 3.4 节的场景定义一致）。"""
    sym = SCENARIOS[scenario]
    out = wave
    if "v" in sym:
        # 式 (3-21)：时缩因子作用于时间轴，等效地抬高所有频率。
        # 时缩会把波形整体压缩，故先按 1/eta 补长再重采样，保持帧长不变，
        # 这样切段位置仍按标称时隙网格给出。
        eta = 1.0 + sym["v"] / SOUND_SPEED
        out = _time_scale(out, eta, out_len=int(round(len(wave) * eta)))
    # 多径：各路径独立时延与幅度（含负号表示相位反转）。
    # 幅度按路径功率和归一，使 Es/N0 的口径在 S1--S4 之间可比；否则
    # sum(a^2)=1.35 会凭空给出 +1.3 dB 增益，让 S2/S3 在低信噪比段
    # 反而优于纯噪声的 S1。
    alpha = np.asarray(sym["alpha"], float)
    alpha = alpha / math.sqrt(float(np.sum(alpha ** 2)))
    out = sum(a * _delay(out, td * cfg["fs"])
              for a, td in zip(alpha, sym["tau"]))
    if sym["ripple"]:
        # 每个驻留区间只有一个单音，带内起伏等效为逐跳复增益；
        # 前导长度之后的段才属于跳频驻留区间。
        n_hop = cfg["nsamp_hop"]
        n_pre = preamble_length(cfg)
        n_seg = len(out) - n_pre
        for k in range(n_seg // n_hop):
            idx = pattern[(k0 + k) % len(pattern)]
            f = freqs[idx] + 0.5 * (cfg["M"] - 1) * cfg["df"]
            s0 = n_pre + k * n_hop
            out[s0:s0 + n_hop] *= band_response(f)
    return out


def _band_limit(noise, cfg):
    """按图 3.2 的前置放大—滤波，把噪声限制在 9--13 kHz 通带内。

    先补零到两倍长度再滤波、取中段，避免循环卷积把帧尾绕回帧首形成
    虚假相关峰。不做功率归一：前端滤波只削减带外噪声，不改变带内 N0，
    故式 (2-9) 的 Es/N0 口径不变。
    """
    n = len(noise)
    pad = np.zeros(2 * n, complex)
    pad[n // 2:n // 2 + n] = noise
    spec = np.fft.fft(pad)
    fr = np.fft.fftfreq(2 * n, 1.0 / cfg["fs"])
    mask = (np.abs(fr) >= cfg["f_lo"]) & (np.abs(fr) <= cfg["f_hi"])
    out = np.fft.ifft(spec * mask)
    return out[n // 2:n // 2 + n]


def add_awgn(wave, cfg, esn0_db, rng):
    """按每符号能量归一并按前端通带限带，与式 (2-9) 的 Es/N0 同口径。

    带限不改变带内谱密度，故 Es/N0 的定义与式 (2-9) 一致；这同时对应
    图 3.2 前置滤波的实际作用——带外噪声被滤掉，匹配滤波因此取得
    10lg(fs/(2B)) 量级的处理增益。
    """
    var = cfg["nsamp_hop"] / (10.0 ** (esn0_db / 10.0))
    sigma = math.sqrt(var / 2.0)
    white = sigma * (rng.standard_normal(len(wave))
                     + 1j * rng.standard_normal(len(wave)))
    return wave + _band_limit(white, cfg)


def add_jammer(wave, cfg, jsr_db, pattern, k0, freqs, rng, jam_f=None, jam_bw=None):
    """S4：固定的窄带干扰，仅命中与其频带重叠的跳。

    干扰方不知道跳频图案，故只能占据一个固定频带（中心 jam_f、带宽 jam_bw）；
    哪些跳被命中取决于图案把频点落在何处——这正是跳频频率分集的作用。
    B3 取 n_f=1，全部跳都在同一频点上，若该频点落在干扰带内则每跳都被命中。
    """
    n_hop = cfg["nsamp_hop"]
    n_pre = preamble_length(cfg)
    n_seg = len(wave) - n_pre
    amp = 10.0 ** (jsr_db / 20.0)
    if jam_f is None:
        jam_f = cfg["f_lo"] + 0.5 * (cfg["f_hi"] - cfg["f_lo"])
    if jam_bw is None:
        jam_bw = cfg["M"] * cfg["df"]
    for k in range(n_seg // n_hop):
        f = freqs[pattern[(k0 + k) % len(pattern)]]
        # 干扰带覆盖该跳的子频点族时才算命中
        if abs(f + 0.5 * (cfg["M"] - 1) * cfg["df"] - jam_f) > jam_bw / 2.0:
            continue
        s0 = n_pre + k * n_hop
        wave[s0:s0 + n_hop] += amp * tone(cfg, jam_f, n_hop) \
            * np.exp(1j * rng.uniform(0, 2 * np.pi))
    return wave


# --------------------------------------------------------------------------
# 同步：匹配滤波 + 首达径判据（式 (3-10)(3-13)）
# --------------------------------------------------------------------------
def sync_detect(wave, cfg, sigma2=None, r_repeat=None):
    """归一化相关与首达径判据，式 (3-9)(3-10)(3-13)。

    rho(tau) = |Lambda(tau)|^2 / (sigma_n^2 * sum|p|^2)，sigma_n^2 由唤醒后的
    空闲监听段估计，故门限 gamma_Lambda 只由虚警概率决定，不随信号强度漂移。

    重复前导按“捕获其中任意一个峰”处理：唤醒时刻会切掉前面的重复，因此
    只用捕获点之后仍在帧内的重复做非相干累加（式 (3-8) 的结构），这既符合
    低占空比监听的实际可观测范围，也把重复发送折算成了检测增益。
    """
    p = lfm_waveform(cfg)
    corr = np.correlate(wave, p, mode="valid")
    e_p = float(np.sum(np.abs(p) ** 2))
    if sigma2 is None:
        sigma2 = float(np.mean(np.abs(wave) ** 2))
    rho = np.abs(corr) ** 2 / (max(sigma2, 1e-12) * e_p)
    period = int(round(cfg["tp"] * cfg["fs"])) + int(round(cfg["tgp"] * cfg["fs"]))
    # 重复前导做非相干累加：把 R 次重复折算成检测增益（式 (3-8)），
    # 累加后仍保留首达径的相对先后；取平均使门限与 R 无关。
    r = max(int(cfg["r_repeat"] if r_repeat is None else r_repeat), 1)
    acc = rho.copy()
    for k in range(1, r):
        d = k * period
        if d < len(rho):
            # acc[i] = rho[i] + rho[i+d] + ...：峰值落在帧内第一个前导上，
            # 直接给出帧起点，便于按前导周期反推。
            acc[:len(rho) - d] += rho[d:]
    acc /= r
    guard = int(round(cfg["tg"] * cfg["fs"]))
    cand = [i for i in range(0, len(acc) - 1)
            if acc[i] > cfg["gamma_lam"]
            and (i == 0 or acc[i] >= acc[i - 1]) and acc[i] >= acc[i + 1]]
    for i in cand:                      # 首达径：前方 T_g 内没有更强的峰
        lo = max(0, i - guard)
        if i == lo or acc[i] >= float(np.max(acc[lo:i])):
            return i
    return None


# --------------------------------------------------------------------------
# 解调：并行自适应 Notch（式 (3-22)--(3-26)）
# --------------------------------------------------------------------------
_REF_CACHE = {}


def _refs(freq, n, fs):
    """参考序列缓存：同一频点在同一 N_h 下只需算一次，避免重复三角函数。

    返回复指数序列 exp(j*2*pi*f*k/fs)，即正文中 cos/sin 两路正交参考的
    合并写法，一支路的实、虚权值分别对应这两路。
    """
    key = (round(freq, 6), n, fs)
    got = _REF_CACHE.get(key)
    if got is None:
        k = np.arange(n, dtype=float)
        got = np.exp(2j * np.pi * freq * k / fs).tolist()
        if len(_REF_CACHE) > 512:
            _REF_CACHE.clear()
        _REF_CACHE[key] = got
    return got


class NotchBank:
    """并行自适应 Notch 滤波器组，式 (3-22)--(3-26)。

    权值跨跳保持，只在跳边界重配支路频率，与正文“相邻跳的支路频率仅
    整体搬移，权值可跨跳保持并只作微调”的处理一致。

    权值取复数 w_i = u_i + j*v_i，与正文的 cos/sin 两路实权值一一对应：
    复乘 e*conj(r) 的实部更新 u_i、虚部更新 v_i，两者是同一组式 (3-25)
    的展开，故本实现与式 (3-22)--(3-26) 严格等价。若改回只取误差实部
    的实数形式，等于丢掉解析信号的一半，会白白损失约 3 dB。
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.w = None
        self.pw = None

    def run(self, seg, freqs, record=False):
        cfg = self.cfg
        n = len(seg)
        fs = cfg["fs"]
        nb = len(freqs)
        if self.w is None or nb != len(self.w):
            self.w = [0j] * nb
            self.pw = [1.0] * nb
        refs = [_refs(f, n, fs) for f in freqs]
        w, pw = self.w, self.pw
        mu, lam, eps = cfg["mu"], cfg["lam"], cfg["eps_p"]
        acc = [0.0] * nb
        tr = np.zeros((n, nb)) if record else None
        i0 = int(round(cfg["warm_frac"] * n))
        segl = seg.tolist()
        for i in range(n):
            r = [refs[b][i] for b in range(nb)]
            y = 0j
            for b in range(nb):
                y += w[b] * r[b]
            er = segl[i] - y
            for b in range(nb):
                c = r[b]
                p = lam * pw[b] + (1.0 - lam) * (c.real * c.real + c.imag * c.imag)
                pw[b] = p
                w[b] += (mu / (p + eps) * er) * c.conjugate()
            if i >= i0:
                for b in range(nb):
                    acc[b] += abs(w[b])
            if record:
                for b in range(nb):
                    tr[i, b] = abs(w[b])
        env = [a / max(n - i0, 1) for a in acc]
        return (env, tr) if record else env

    def reset_power(self):
        if self.pw is not None:
            self.pw = [1.0] * len(self.pw)


def hop_envelopes(seg, freqs, cfg, record=False):
    """单跳、冷启动的便捷接口，供单点核查使用。"""
    return NotchBank(cfg).run(seg, freqs, record=record)


def fft_envelopes(seg, freqs, cfg):
    """B1：N_h 点 FFT 在候选频点处取峰。

    候选频点落在 DFT 栅格上（df 为 1/T_s 的整数倍），故不加窗即可，
    加窗反而会把相邻支路的能量抹平。
    """
    n = len(seg)
    spec = np.abs(np.fft.fft(seg, n))
    fr = np.fft.fftfreq(n, 1.0 / cfg["fs"])
    return [float(spec[int(np.argmin(np.abs(fr - f)))]) for f in freqs]


# --------------------------------------------------------------------------
# 单帧
# --------------------------------------------------------------------------
def run_frame(esn0_db, scenario, opts, rng, r_repeat=None, n_f=None, hop0=None):
    cfg = CONFIG
    base = cfg["f_hop0"] if hop0 is None else hop0
    freqs = (base + np.arange(cfg["n_f"] if n_f is None else n_f) * cfg["f_hop_step"])
    pattern = hopping_sequence(cfg["ns"] + cfg["nd"] + 8, len(freqs), seed=cfg["seed"])
    k0 = 2 if len(pattern) >= cfg["ns"] + cfg["nd"] + 3 else 0

    n_bits = cfg["nd"] * cfg["nbits_hop"]
    tx_bits = rng.integers(0, 2, n_bits)
    tx = build_frame(tx_bits, pattern, k0, cfg, freqs, r_repeat)
    rx = apply_channel(tx, cfg, scenario, pattern, k0, freqs)
    if scenario == "S4":
        rx = add_jammer(rx, cfg, opts.get("jsr_db", 0.0), pattern, k0, freqs, rng,
                        jam_f=JAM_F, jam_bw=JAM_BW)
    # 帧前加一段空闲监听：接收机用它估计噪声底 sigma_n^2（式 (3-11)）
    n_idle = int(round(cfg["t_idle"] * cfg["fs"]))
    rx = np.concatenate([np.zeros(n_idle, complex), rx])
    rx = add_awgn(rx, cfg, esn0_db, rng)

    # 低占空比监听：唤醒前样点不可用，唤醒时刻在窗口内均匀分布
    t_wake = 0.0 if opts.get("no_wake_uncertainty") else cfg["t_wake"]
    iw = int(round(rng.uniform(0.0, t_wake) * cfg["fs"])) if t_wake > 0 else 0
    n_p = preamble_length(cfg, r_repeat)
    # 唤醒时刻晚于“最后一个前导的起点”时，帧内已无完整 LFM 可捕获
    n_tp = int(round(cfg["tp"] * cfg["fs"]))
    if iw > n_idle + n_p - n_tp:
        return False, 0, 0          # 前导被唤醒时刻切掉，无可用观测
    rx_l = rx.copy()
    rx_l[:iw] = 0.0

    # 噪声底取自唤醒后的空闲段（t_idle 中未被切掉的部分）；若整段被切掉，
    # 退回用整帧功率的下分位估计，避免把置零样点算成噪声。
    tail = rx_l[iw:n_idle]
    if len(tail) >= 64:
        sigma2 = float(np.mean(np.abs(tail) ** 2))
    else:
        win = max(int(round(cfg["tp"] * cfg["fs"] / 8)), 16)
        pwr = np.convolve(np.abs(rx_l) ** 2, np.ones(win) / win, mode="valid")
        sigma2 = max(float(np.percentile(pwr, 5)), 1e-12)

    n_hop = cfg["nsamp_hop"]
    if opts.get("ideal_sync"):
        tau_hat, k0_hat = 0, k0
    else:
        # 前导重复次数必须与建帧时一致，否则累加会把数据段的相关值
        # 叠到前导上（B2 单次前导时尤其明显），产生虚假峰位
        peak = sync_detect(rx_l, cfg, sigma2, r_repeat=r_repeat)
        if peak is None:
            return False, 0, 0            # 相关峰未过门限：无符号判决可统计
        # 由捕获到的峰反推帧起点。np.correlate(...,'valid') 的第 i 点对应
        # 参考波形末端与样点 i 对齐，故峰位 i 表示帧起点在 i-Np+1 处。
        n_tp = int(round(cfg["tp"] * cfg["fs"]))
        period = n_tp + int(round(cfg["tgp"] * cfg["fs"]))
        tau_hat = (peak - n_idle - n_tp + 1) % period
        # 式 (3-19)：窗内相位由同步字段的已知图案判决；三个候选相位共用
        # 一套支路，故各自建立滤波器组。
        # 跳频点数 N_f=1 时各候选相位对应同一组支路频率，图案相位在本场景
        # 不可观测（这正是“无频率分集”的固有性质），此时不做相位判决，
        # 直接把候选相位判为真值，避免把“不可观测”误计为同步失败。
        if len(freqs) < 2:
            k0_hat = k0
        else:
            best, k0_hat = -1.0, None
            for cand in (k0 - 1, k0, k0 + 1):
                bank = NotchBank(cfg)
                score = 0.0
                for j in range(cfg["ns"]):
                    s0 = n_idle + tau_hat + preamble_length(cfg, r_repeat) + j * n_hop
                    seg = rx_l[s0:s0 + n_hop]
                    if len(seg) < n_hop:
                        continue
                    base = freqs[pattern[(cand + j) % len(pattern)]]
                    brs = [base + m * cfg["df"] for m in range(cfg["M"])]
                    env = bank.run(seg, brs)
                    score += env[0]
                if score > best:
                    best, k0_hat = score, cand

    syn_ok = (abs(tau_hat / cfg["fs"]) <= cfg["ts"] / 2.0
              and (k0_hat % len(pattern)) == (k0 % len(pattern)))

    start = n_idle + tau_hat + preamble_length(cfg, r_repeat) + cfg["ns"] * n_hop
    rx_bits = []
    for j in range(cfg["nd"]):
        s0 = start + j * n_hop
        seg = rx_l[s0:s0 + n_hop]
        if len(seg) < n_hop:
            seg = np.concatenate([seg, np.zeros(n_hop - len(seg), complex)])
        base = freqs[pattern[(k0_hat + cfg["ns"] + j) % len(pattern)]]
        brs = [base + m * cfg["df"] for m in range(cfg["M"])]
        if opts.get("fft_demod"):
            env = fft_envelopes(seg, brs, cfg)
        else:
            # 每个跳边界按式 (3-31) 重配支路参考频率；式 (3-28) 保证权值
            # 在一个跳时隙内收敛，故各跳独立从零启动即可，无需跨跳搬运
            # 一组与新频点并不匹配的旧权值。
            env = hop_envelopes(seg, brs, cfg)
        m_hat = int(np.argmax(env))
        if max(env) <= cfg["gamma_h"]:
            m_hat = 0
        m_hat = gray_decode(m_hat)
        rx_bits += [(m_hat >> (cfg["nbits_hop"] - 1 - b)) & 1
                    for b in range(cfg["nbits_hop"])]
    rx_bits = np.array(rx_bits, dtype=int)
    err = int(np.sum(rx_bits != tx_bits))
    # 与第 3.4 节“误码率与同步成功率分处统计”一致：未同步帧只计入 P_syn，
    # 不进入 P_b 的比特分母——此时帧边界本就未知，其判决结果是随机的，
    # 掺进 P_b 会把同步失败伪装成“判决错误”。
    if not syn_ok:
        return False, err, 0
    return True, err, n_bits


def _frame_task(args):
    """蒙特卡洛单帧任务，供进程池调用。

    每帧按帧序号独立重建随机数发生器，并行与串行的结果逐位一致，
    运行帧数改变时也只需重跑受影响的点。
    """
    esn0_db, scenario, opts, fseed, kw = args
    rng = np.random.default_rng(fseed)
    return run_frame(esn0_db, scenario, opts, rng, **kw)


def _n_workers():
    want = CONFIG.get("workers") or 0
    # 留一个核给主进程做统计与绘图
    return max(1, min(want if want > 0 else os.cpu_count() or 1,
                      (os.cpu_count() or 1)))


_POOL = None


def _pool():
    """进程池惰性创建，四幅图共用，避免反复派生进程。"""
    global _POOL
    if _POOL is None:
        n = _n_workers()
        print(f"[sim] multiprocessing pool: {n} workers", flush=True)
        _POOL = mp.Pool(processes=n)
    return _POOL


def run_point(esn0_db, scenario, opts=None, n_frames=None, seed=0, **kw):
    """一点信噪比下的蒙特卡洛统计（多进程并行）。

    同步失败的帧计为 P_syn 失败，但不进入 P_b 的分母——第 3.4 节明确
    误码率与同步成功率分处统计，不能把“未同步”混同为“判错比特”。
    """
    opts = opts or {}
    n_frames = CONFIG["n_frames"] if n_frames is None else n_frames
    base = CONFIG["seed"] + 1000 * seed          # 每个 seed 一段互不重叠的流
    tasks = [(esn0_db, scenario, opts, base + i, kw) for i in range(n_frames)]
    n_syn = n_err = n_bit = n_ok = 0
    for ok, err, nb in _pool().imap(_frame_task, tasks, chunksize=4):
        n_syn += int(ok)
        if nb == 0:
            continue
        n_err += err
        n_bit += nb
        n_ok += int(ok and err == 0)
    return dict(pb=n_err / n_bit if n_bit else float("nan"), psyn=n_syn / n_frames,
                pframe=n_ok / n_frames, n_err=n_err, n_bit=n_bit)


def run_series(sweep, scenario, opts=None, seed=0, tag="", n_frames=None, **kw):
    """沿一个扫变轴逐点运行，并打印逐点进度日志。"""
    pts = [dict(esn0_db=float(x), scenario=scenario, opts=opts, seed=seed,
                n_frames=n_frames, **kw) for x in sweep]
    return run_grid(pts, tag, [f"{x:6.1f}" for x in sweep])


def run_grid(points, tag="", labels=None):
    """逐点运行一组蒙特卡洛点并打印逐点进度日志。

    points 中每项是 run_point 的关键字参数；这样同一条曲线既可以沿信噪比
    扫变，也可以沿干信比扫变（把 JSR 放进 opts）。
    """
    out = []
    n = len(points)
    t_all = time.time()
    for i, pt in enumerate(points):
        lb = labels[i] if labels else str(i + 1)
        t0 = time.time()
        r = run_point(**pt)
        out.append(r)
        print(f"[{tag}] ({i + 1}/{n}) {lb} -> Pb={r['pb']:.3e} "
              f"Psyn={r['psyn']:.3f} Pfrm={r['pframe']:.3f} "
              f"({time.time() - t0:.1f}s, cum {time.time() - t_all:.1f}s)",
              flush=True)
    return out


def theory_ser(esn0_db, M=4):
    """式 (2-9)：非相干正交 MFSK 误符号率。"""
    x = 10.0 ** (esn0_db / 10.0)
    return sum((-1) ** (m + 1) * math.comb(M - 1, m) / (m + 1)
               * math.exp(-m / (m + 1) * x) for m in range(1, M))


def pb_from_ps(ps, M=4):
    """式 (3-12)：Gray 映射下的误符号率折算。"""
    return M / (2.0 * (M - 1)) * ps


def confidence_radius(p, n, z=1.96):
    """式 (3-14) 的置信半径。"""
    p = min(max(p, 1e-12), 1 - 1e-12)
    return z * math.sqrt(p * (1 - p) / max(n, 1))



# --------------------------------------------------------------------------
# 出图
# --------------------------------------------------------------------------
def _log_axis(ax):
    ax.yaxis.set_major_locator(mticker.LogLocator(base=10.0))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: r"$10^{%d}$" % int(round(math.log10(v)))))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())


def _plot_pb(ax, x, y, **kw):
    """误码率曲线：跳过无符号判决（同步失败、未过门限）的空点。"""
    xa = np.asarray(x, float)
    ya = np.asarray(y, float)
    ok = np.isfinite(ya) & (ya > 0)
    ax.semilogy(xa[ok], ya[ok], **kw)


C_N = "#1f4e79"     # 本文方案
C_B1 = "#c0504d"    # 频谱解调
C_B2 = "#4f6228"    # 单次前导
C_B0 = "#7f7f7f"    # 理想同步


def fig_calibration():
    """图 3.7：S1 校验与 Notch 支路包络收敛。"""
    esn0 = np.arange(0, 22, 2.0)
    th = [pb_from_ps(theory_ser(x)) for x in esn0]
    s1 = run_series(esn0, "S1", seed=1, tag="3.7 校准/Notch")
    b1 = run_series(esn0, "S1", {"fft_demod": True}, seed=2, tag="3.7 校准/FFT")

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax = axes[0]
    ax.semilogy(esn0, th, "k-", linewidth=1.2, label="式 (2-9) 理论")
    _plot_pb(ax, esn0, [x["pb"] for x in s1], marker="o", ls="-", color=C_N,
             label="并行 Notch")
    _plot_pb(ax, esn0, [x["pb"] for x in b1], marker="s", ls="--", color=C_B1,
             label="FFT 取峰（B1）")
    ax.set_xlabel(r"$E_s/N_0$ / dB")
    ax.set_ylabel("误比特率 $P_b$")
    ax.set_title("(a) S1 场景的解调校验", fontsize=9)
    ax.set_ylim(1e-4, 0.8)
    ax.legend(fontsize=7.5, loc="lower left")
    _log_axis(ax)

    # (b) 正确支路与其余支路的包络收敛（式 3-26）
    ax = axes[1]
    cfg = CONFIG
    freqs = hop_frequencies(cfg)
    n_hop = cfg["nsamp_hop"]
    rng = np.random.default_rng(7)
    bits = rng.integers(0, 2, cfg["nd"] * cfg["nbits_hop"])
    pattern = hopping_sequence(cfg["ns"] + cfg["nd"] + 8, len(freqs), seed=cfg["seed"])
    k0 = 2
    tx = build_frame(bits, pattern, k0, cfg, freqs)
    start = preamble_length(cfg) + cfg["ns"] * n_hop
    base = freqs[pattern[k0]]
    brs = [base + m * cfg["df"] for m in range(cfg["M"])]
    ks = np.arange(n_hop)
    # 只画收敛段：式 (3-28) 保证 mu 下 128 点内即收敛，前段全是零值启动的
    # 暂态，画出来会把曲线压成一条贴着横轴的水平线，看不出收敛过程。
    n_show = 4 * int(round(1.0 / cfg["mu"]))
    n_show = min(n_show, n_hop)
    for esn0_db, ls, a in ((6.0, ":", 0.9), (18.0, "-", 1.0)):
        rx = add_awgn(tx, cfg, esn0_db, np.random.default_rng(11))
        _, tr = hop_envelopes(rx[start:start + n_hop], brs, cfg, record=True)
        ax.plot(ks[:n_show], tr[:n_show, 0], ls, color=C_N, linewidth=a,
                label=r"$H_1$，$E_s/N_0=%g$ dB" % esn0_db)
        for b in range(1, cfg["M"]):
            ax.plot(ks[:n_show], tr[:n_show, b], ls, color="#b0b0b0", linewidth=0.6,
                    label="其余支路" if (b == 1 and esn0_db == 18.0) else None)
    ax.set_xlabel("符号内样点序号 $k$")
    ax.set_ylabel(r"支路包络 $H_i(k)$")
    ax.set_title("(b) 权值收敛与支路分辨", fontsize=9)
    ax.set_xlim(0, n_show)
    ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(FIGDIR, "sim_sfh_calibration.pdf"))
    plt.close(fig)
    return dict(esn0=esn0.tolist(), theory=th,
                s1=[x["pb"] for x in s1], b1=[x["pb"] for x in b1],
                psyn=[x["psyn"] for x in s1])


def fig_channel():
    """图 3.8：S1/S2/S3 的误码率与频偏引起的支路泄漏。"""
    esn0 = np.arange(0, 22, 2.0)
    res = {sc: run_series(esn0, sc, seed=3, tag=f"3.8 {sc}")
           for sc in ("S1", "S2", "S3")}

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax = axes[0]
    ax.semilogy(esn0, [pb_from_ps(theory_ser(x)) for x in esn0], "k-",
                linewidth=1.2, label="式 (2-9) 理论")
    for sc, c, mk, lb in (("S1", C_N, "o", "S1 仅噪声"),
                          ("S2", C_B1, "s", "S2 加多径"),
                          ("S3", C_B2, "^", "S3 再加时缩")):
        _plot_pb(ax, esn0, [x["pb"] for x in res[sc]], marker=mk, ls="-",
                 color=c, label=lb)
    ax.set_xlabel(r"$E_s/N_0$ / dB")
    ax.set_ylabel("误比特率 $P_b$")
    ax.set_title("(a) 四级场景逐级叠加", fontsize=9)
    ax.set_ylim(1e-4, 0.8)
    ax.legend(fontsize=7.5, loc="lower left")
    _log_axis(ax)

    # (b) 残余频偏对正确支路能量占比的影响
    ax = axes[1]
    cfg = CONFIG
    freqs = hop_frequencies(cfg)
    n_hop = cfg["nsamp_hop"]
    base = freqs[2]
    brs = [base + m * cfg["df"] for m in range(cfg["M"])]
    offs = np.arange(0, 301, 10)
    leak = []
    for off in offs:
        seg = tone(cfg, base + off, n_hop)
        seg = add_awgn(seg, cfg, 30.0, np.random.default_rng(5))
        env = hop_envelopes(seg, brs, cfg)
        leak.append(env[0] / max(max(env), 1e-12))
    ax.plot(offs, leak, "o-", color=C_N, markersize=2.6)
    ax.axvline(cfg["df"] / 2.0, ls=":", color=C_B1, linewidth=1.0)
    ax.annotate(r"$\Delta f/2$", xy=(cfg["df"] / 2.0, 0.62),
                xytext=(cfg["df"] / 2.0 + 20, 0.72), fontsize=7.5,
                color=C_B1, arrowprops=dict(arrowstyle="-", color=C_B1,
                                            linewidth=0.6))
    ax.set_xlabel("残余频偏 / Hz")
    ax.set_ylabel("正确支路能量占比")
    ax.set_title("(b) 频偏引起的支路泄漏", fontsize=9)
    ax.set_ylim(0, 1.02)
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(FIGDIR, "sim_sfh_channel.pdf"))
    plt.close(fig)
    return dict(esn0=esn0.tolist(),
                pb={k: [x["pb"] for x in v] for k, v in res.items()},
                offs=offs.tolist(), leak=leak,
                psyn={k: [x["psyn"] for x in v] for k, v in res.items()})


def fig_jamming():
    """图 3.9：S4 下跳频与固定载频的抗干扰对比。

    B3 取 N_f=1，且把该唯一频点放在干扰带内（干扰方自然会挑对它最有力的
    驻留频点），这才是“无频率分集”的真实最坏情形。N_f=2 居中，用来显示
    频率分集的作用随可用频点数单调变化。
    """
    jsr = np.arange(-10, 31, 5)
    esn0_fix = 16.0
    lbl = [f"{j:4d} dB" for j in jsr]
    hop = run_grid([dict(esn0_db=esn0_fix, scenario="S4", opts={"jsr_db": float(j)},
                         seed=4) for j in jsr],
                   tag="3.9 跳频 N_f=4", labels=lbl)
    half = run_grid([dict(esn0_db=esn0_fix, scenario="S4", opts={"jsr_db": float(j)},
                          hop0=JAM_F, n_f=2, seed=7) for j in jsr],
                    tag="3.9 跳频 N_f=2", labels=lbl)
    fix = run_grid([dict(esn0_db=esn0_fix, scenario="S4",
                         opts={"jsr_db": float(j), "fixed_carrier": True},
                         hop0=JAM_F, n_f=1, seed=5) for j in jsr],
                   tag="3.9 固定载频 B3", labels=lbl)

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax = axes[0]
    _plot_pb(ax, jsr, [x["pb"] for x in hop], marker="o", ls="-", color=C_N,
             label=r"跳频 $N_f=4$")
    _plot_pb(ax, jsr, [x["pb"] for x in half], marker="^", ls="-.", color=C_B2,
             label=r"跳频 $N_f=2$")
    _plot_pb(ax, jsr, [x["pb"] for x in fix], marker="s", ls="--", color=C_B1,
             label="固定载频（B3）")
    ax.set_xlabel("干信比 JSR / dB")
    ax.set_ylabel("误比特率 $P_b$")
    ax.set_title("(a) 误比特率", fontsize=9)
    ax.legend(fontsize=7.5, loc="lower right")
    ax.set_ylim(1e-3, 1.0)
    _log_axis(ax)

    ax = axes[1]
    ax.plot(jsr, [x["pframe"] for x in hop], "o-", color=C_N, label=r"跳频 $N_f=4$")
    ax.plot(jsr, [x["pframe"] for x in half], "^-.", color=C_B2, label=r"跳频 $N_f=2$")
    ax.plot(jsr, [x["pframe"] for x in fix], "s--", color=C_B1, label="固定载频（B3）")
    ax.set_xlabel("干信比 JSR / dB")
    ax.set_ylabel(r"完整帧成功率 $P_{\mathrm{frame}}$")
    ax.set_title("(b) 完整帧成功率", fontsize=9)
    ax.set_ylim(-0.03, 1.03)
    ax.legend(fontsize=7.5, loc="upper right")
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(FIGDIR, "sim_sfh_jamming.pdf"))
    plt.close(fig)
    return dict(jsr=jsr.tolist(), esn0=esn0_fix,
                pb_hop=[x["pb"] for x in hop], pb_fix=[x["pb"] for x in fix],
                pb_half=[x["pb"] for x in half],
                pf_hop=[x["pframe"] for x in hop], pf_fix=[x["pframe"] for x in fix],
                pf_half=[x["pframe"] for x in half])


def fig_ablation():
    """图 3.10：四组对照的消融。"""
    esn0 = np.arange(0, 22, 2.0)
    base = run_series(esn0, "S3", seed=6, tag="3.10 本文方案")
    b0 = run_series(esn0, "S3", {"ideal_sync": True}, seed=7, tag="3.10 B0 理想同步")
    b1 = run_series(esn0, "S3", {"fft_demod": True}, seed=8, tag="3.10 B1 频谱解调")
    b2 = run_series(esn0, "S3", seed=9, tag="3.10 B2 单次前导", r_repeat=1)

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax = axes[0]
    _plot_pb(ax, esn0, [x["pb"] for x in base], marker="o", ls="-", color=C_N,
             label="本文方案")
    _plot_pb(ax, esn0, [x["pb"] for x in b0], marker="^", ls=":", color=C_B0,
             label="B0 理想同步")
    _plot_pb(ax, esn0, [x["pb"] for x in b1], marker="s", ls="--", color=C_B1,
             label="B1 频谱解调")
    _plot_pb(ax, esn0, [x["pb"] for x in b2], marker="d", ls="-.", color=C_B2,
             label="B2 单次前导")
    ax.set_xlabel(r"$E_s/N_0$ / dB")
    ax.set_ylabel("误比特率 $P_b$")
    ax.set_title("(a) 误比特率消融", fontsize=9)
    ax.set_ylim(1e-4, 0.8)
    ax.legend(fontsize=7, loc="lower left")
    _log_axis(ax)

    ax = axes[1]
    ax.plot(esn0, [x["psyn"] for x in base], "o-", color=C_N,
            label=r"$P_{\mathrm{syn}}$，$R=2$")
    ax.plot(esn0, [x["psyn"] for x in b2], "d--", color=C_B2,
            label=r"$P_{\mathrm{syn}}$，$R=1$（B2）")
    ax.plot(esn0, [x["pframe"] for x in base], "^:", color=C_B1,
            label=r"$P_{\mathrm{frame}}$，$R=2$")
    ax.set_xlabel(r"$E_s/N_0$ / dB")
    ax.set_ylabel("成功率")
    ax.set_title("(b) 同步与整帧成功", fontsize=9)
    ax.set_ylim(-0.03, 1.03)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(FIGDIR, "sim_sfh_ablation.pdf"))
    plt.close(fig)
    return dict(esn0=esn0.tolist(),
                pb={"S": [x["pb"] for x in base], "B0": [x["pb"] for x in b0],
                    "B1": [x["pb"] for x in b1], "B2": [x["pb"] for x in b2]},
                psyn={"S": [x["psyn"] for x in base], "B2": [x["psyn"] for x in b2]},
                pframe=[x["pframe"] for x in base])


def report(out):
    """把正文要引用的数值打印出来，便于逐条核对，不写入正文。"""
    cal = out["calibration"]
    print("\n--- 图 3.7(a) S1 校验（Pb）---")
    for x, t, s1, b1 in zip(cal["esn0"], cal["theory"], cal["s1"], cal["b1"]):
        print(f"  {x:5.1f} dB  理论={t:.4e}  Notch={s1:.4e}  FFT={b1:.4e}")
    ch = out["channel"]
    print("\n--- 图 3.8(a) S1/S2/S3（Pb）---")
    for i, x in enumerate(ch["esn0"]):
        print(f"  {x:5.1f} dB  S1={ch['pb']['S1'][i]:.4e} "
              f"S2={ch['pb']['S2'][i]:.4e} S3={ch['pb']['S3'][i]:.4e}")
    print("\n--- 图 3.8(b) 频偏泄漏 ---")
    for o, l in zip(ch["offs"][::5], ch["leak"][::5]):
        print(f"  偏 {o:4d} Hz  占比 {l:.3f}")
    jm = out["jamming"]
    print(f"\n--- 图 3.9 JSR 扫变（S4，Es/N0={jm['esn0']:g} dB）---")
    for i, j in enumerate(jm["jsr"]):
        print(f"  {j:4d} dB  Pb 跳频4={jm['pb_hop'][i]:.4e} 跳频2={jm['pb_half'][i]:.4e} "
              f"固定={jm['pb_fix'][i]:.4e}  Pframe 跳频4={jm['pf_hop'][i]:.3f} "
              f"跳频2={jm['pf_half'][i]:.3f} 固定={jm['pf_fix'][i]:.3f}")
    ab = out["ablation"]
    print("\n--- 图 3.10 消融（S3）---")
    for i, x in enumerate(ab["esn0"]):
        print(f"  {x:5.1f} dB  S={ab['pb']['S'][i]:.4e} B0={ab['pb']['B0'][i]:.4e} "
              f"B1={ab['pb']['B1'][i]:.4e} B2={ab['pb']['B2'][i]:.4e}  "
              f"Psyn S={ab['psyn']['S'][i]:.2f} B2={ab['psyn']['B2'][i]:.2f} "
              f"Pframe={ab['pframe'][i]:.2f}")


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    print(f"[sim] N_fr={CONFIG['n_frames']} 帧/点，"
          f"{_n_workers()} 进程并行", flush=True)
    out = {}
    t_all = time.time()
    for name, fn in (("calibration", fig_calibration), ("channel", fig_channel),
                     ("jamming", fig_jamming), ("ablation", fig_ablation)):
        print(f"\n[sim] ===== {name} 开始 =====", flush=True)
        t0 = time.time()
        out[name] = fn()
        print(f"[sim] ===== {name} 完成，用时 {time.time() - t0:.1f}s =====",
              flush=True)
    report(out)
    print(f"\n[sim] 全部完成，总用时 {time.time() - t_all:.1f}s", flush=True)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="第 3 章 SFH-MFSK 通信仿真")
    ap.add_argument("-j", "--workers", type=int, default=0,
                    help="并行进程数，0 表示自动取 CPU 核数")
    ap.add_argument("-n", "--frames", type=int, default=0,
                    help="每点蒙特卡洛帧数，0 表示用 CONFIG['n_frames']")
    args = ap.parse_args()
    if args.workers:
        CONFIG["workers"] = args.workers
    if args.frames:
        CONFIG["n_frames"] = args.frames
    try:
        main()
    finally:
        if _POOL is not None:
            _POOL.close()
            _POOL.join()







