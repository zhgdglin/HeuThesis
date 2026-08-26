from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

import build_ppt_template as base

OUT_PPTX = base.OUT / "final_presentation_cn_six_sections_formula.pptx"


CHAPTERS = [
    "论文研究目标",
    "开题报告中研究内容与完成情况对比",
    "目前已经完成的工作和结果",
    "创新点与目前取得的成果",
    "后续研究计划",
    "论文后续工作的难点与不确定性",
]


def chapter_slide(prs, number, title):
    slide = base.blank(prs)
    base.add_logo(slide)
    circ = slide.shapes.add_shape(
        base.MSO_SHAPE.OVAL, Inches(2.88), Inches(2.28), Inches(1.10), Inches(1.10)
    )
    circ.fill.solid()
    circ.fill.fore_color.rgb = base.BLUE
    circ.line.fill.background()
    base.textbox(
        slide,
        f"第{number}章",
        Inches(2.97),
        Inches(2.65),
        Inches(0.92),
        Inches(0.24),
        size=10,
        bold=True,
        color=base.WHITE,
        align=PP_ALIGN.CENTER,
    )
    base.textbox(
        slide,
        f"Chapter {number}",
        Inches(4.20),
        Inches(2.04),
        Inches(3.10),
        Inches(0.62),
        size=32,
        color=base.BLUE,
    )
    line = slide.shapes.add_shape(
        base.MSO_SHAPE.RECTANGLE, Inches(4.16), Inches(2.88), Inches(4.40), Inches(0.015)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = base.BLUE
    line.line.fill.background()
    base.textbox(
        slide,
        title,
        Inches(4.20),
        Inches(3.13),
        Inches(5.55),
        Inches(0.52),
        size=21,
        bold=True,
        color=base.BLUE,
        align=PP_ALIGN.LEFT,
    )
    base.note(slide, f"进入第{number}章：{title}。")
    return slide


def formula_box(slide, text, x, y, w, h, size=12.2, color=base.BLUE):
    box = slide.shapes.add_shape(base.MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = base.WHITE
    box.line.color.rgb = base.LINE
    tb = base.textbox(slide, text, x + Inches(0.08), y + Inches(0.04), w - Inches(0.16), h - Inches(0.08),
                      size=size, color=color, align=PP_ALIGN.CENTER, valign=base.MSO_ANCHOR.MIDDLE, margin=0.02)
    for p in tb.text_frame.paragraphs:
        for r in p.runs:
            r.font.name = "Cambria Math"
    return box


def build():
    prs = base.Presentation(base.TEMPLATE)
    base.delete_all_slides(prs)

    # 1 cover
    s = base.blank(prs)
    base.add_logo(s, Inches(0.35), Inches(0.24), Inches(2.35))
    band = s.shapes.add_shape(base.MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.95), Inches(7.15), Inches(1.45))
    band.fill.solid()
    band.fill.fore_color.rgb = base.BLUE
    band.line.fill.background()
    base.textbox(
        s,
        "基于 SFH-MFSK 的\n声学释放器技术研究与实现",
        Inches(0.82),
        Inches(2.18),
        Inches(6.05),
        Inches(0.88),
        size=25,
        bold=True,
        color=base.WHITE,
        align=PP_ALIGN.CENTER,
    )
    if base.COVER_PHOTO.exists():
        s.shapes.add_picture(str(base.COVER_PHOTO), Inches(7.05), Inches(1.52), width=Inches(4.65), height=Inches(3.12))
    accent = s.shapes.add_shape(base.MSO_SHAPE.RECTANGLE, Inches(0), Inches(3.40), Inches(7.15), Inches(0.055))
    accent.fill.solid()
    accent.fill.fore_color.rgb = base.ORANGE
    accent.line.fill.background()
    base.textbox(s, "水声工程学院  电子信息", Inches(1.00), Inches(4.84), Inches(3.1), Inches(0.25), size=12.5, color=base.BLUE)
    base.textbox(
        s,
        "汇报人：张冬林\n学号：S324527148\n指导教师：葛威 副教授\n2026 年 8 月",
        Inches(7.10),
        Inches(4.62),
        Inches(3.25),
        Inches(0.90),
        size=12.2,
        color=base.BLUE,
    )
    base.note(s, "开场说明汇报按报告正文六个章节展开，主题是声学释放器、SFH-MFSK 通信和快速声线测距。")

    # 2 contents
    s = base.blank(prs)
    base.add_logo(s)
    poly = s.shapes.add_shape(base.MSO_SHAPE.TRAPEZOID, Inches(0.48), Inches(2.35), Inches(3.10), Inches(1.15))
    poly.fill.solid()
    poly.fill.fore_color.rgb = base.BLUE
    poly.line.fill.background()
    base.textbox(s, "目 录\nCONTENTS", Inches(1.02), Inches(2.42), Inches(2.05), Inches(0.82), size=20, bold=True, color=base.WHITE, align=PP_ALIGN.CENTER)
    for i, title in enumerate(CHAPTERS, 1):
        col = 0 if i <= 3 else 1
        row = i - 1 if i <= 3 else i - 4
        x_num = Inches(4.20 + col * 3.70)
        x_rect = Inches(4.75 + col * 3.70)
        y = Inches(1.45 + row * 0.88)
        base.textbox(s, str(i), x_num, y, Inches(0.32), Inches(0.34), size=21, bold=True, color=base.BLUE)
        rect = s.shapes.add_shape(base.MSO_SHAPE.RECTANGLE, x_rect, y + Inches(0.04), Inches(3.25), Inches(0.45))
        rect.fill.solid()
        rect.fill.fore_color.rgb = base.WHITE
        rect.line.fill.background()
        base.textbox(s, title, x_rect + Inches(0.14), y + Inches(0.11), Inches(3.02), Inches(0.24), size=10.8, bold=True, color=base.BLUE)
    base.note(s, "目录页改为与报告正文一致的六章结构。")

    # Chapter 1
    chapter_slide(prs, 1, CHAPTERS[0])
    s = base.blank(prs)
    base.header(s, "研究目标：形成通信、测距与释放控制闭环", CHAPTERS[0])
    base.chip(s, "总体目标", "面向水下观测设备布放与回收，设计低功耗水下声学释放器。", Inches(0.78), Inches(1.15), Inches(3.32), base.BLUE)
    base.chip(s, "通信目标", "具备 SFH-MFSK 声学通信能力，在低 SNR 与窄带干扰下可靠接收远程指令。", Inches(4.50), Inches(1.15), Inches(3.32), base.TEAL)
    base.chip(s, "测距目标", "建立不依赖目标深度的快速声线测距能力，实现精度可接受的距离估计。", Inches(8.22), Inches(1.15), Inches(3.32), base.ORANGE)
    base.textbox(
        s,
        "技术链路：遥控指令生成 → 声学信号收发 → 指令判决 → 释放执行 → 距离估计。",
        Inches(1.00),
        Inches(4.46),
        Inches(10.40),
        Inches(0.42),
        size=18,
        bold=True,
        color=base.BLUE,
        align=PP_ALIGN.CENTER,
    )
    base.footer(s, 4)
    base.note(s, "第一章只讲研究目标，强调目标是系统闭环，不是单一算法。")

    # Chapter 2
    chapter_slide(prs, 2, CHAPTERS[1])
    s = base.blank(prs)
    base.header(s, "开题任务已从方案设计推进到算法建模与初步验证", CHAPTERS[1])
    base.chip(s, "软硬件方案设计", "已完成总体方案、功能模块划分和软硬件协同架构设计。", Inches(0.82), Inches(1.10), Inches(5.00), base.BLUE)
    base.chip(s, "SFH-MFSK 通信体制", "已完成帧结构、跳频频点组织、符号映射、同步检测和非相干判决流程研究。", Inches(6.25), Inches(1.10), Inches(5.00), base.TEAL)
    base.chip(s, "测距方法研究", "已形成传播时延估计、声速剖面影响、声线折射修正和快速距离解算的基础流程。", Inches(0.82), Inches(3.05), Inches(5.00), base.ORANGE)
    base.chip(s, "湖试海试验证", "已完成设备联调、水池测试前期工作和基础数据采集，后续继续扩展外场验证。", Inches(6.25), Inches(3.05), Inches(5.00), base.BLUE_2)
    base.textbox(s, "对比判断：开题中的四项任务均已启动，其中系统方案和算法框架完成度较高，外场定量验证仍是后续重点。",
                 Inches(1.05), Inches(5.82), Inches(10.20), Inches(0.35), size=13.4, bold=True, color=base.BLUE, align=PP_ALIGN.CENTER)
    base.footer(s, 6)
    base.note(s, "第二章对应报告中的开题内容与完成情况对比，按四项任务分别说明完成状态。")

    # Chapter 3
    chapter_slide(prs, 3, CHAPTERS[2])
    s = base.blank(prs)
    base.header(s, "硬件系统架构支撑水面端与水下端双向闭环", CHAPTERS[2])
    base.image(s, "software_system.png", Inches(0.80), Inches(1.15), Inches(7.70), Inches(4.20))
    base.bullets(s, ["水面端负责指令编码、人机交互和回传解码", "水下端完成声信号接收、解码、执行与反馈", "双向水声链路支撑状态确认和回收控制"], Inches(8.85), Inches(1.45), Inches(2.90), Inches(1.75), size=12.2)
    base.textbox(s, "系统设计已经形成“指令下发、动作执行、状态反馈”的闭环结构。", Inches(8.85), Inches(4.25), Inches(2.82), Inches(0.68), size=12.4, bold=True, color=base.BLUE)
    base.caption(s, "图 1：声学释放器硬件系统架构", "report.pdf, 图 1", Inches(0.80), Inches(5.54), Inches(7.70))
    base.footer(s, 8)
    base.note(s, "从水面端到水下端讲系统闭环。")

    s = base.blank(prs)
    base.header(s, "软件控制流程围绕低功耗值守与可靠释放展开", CHAPTERS[2])
    base.image(s, "sfq_logic.png", Inches(1.05), Inches(1.04), Inches(3.45), Inches(5.30))
    base.bullets(s, ["未检测到唤醒信号时保持低功耗等待", "唤醒后通过乒乓缓存保证采样与处理连续", "同步信号 5 min 未到达则返回休眠检测", "释放指令触发动作，其他指令执行后发送应答"], Inches(5.15), Inches(1.44), Inches(5.95), Inches(2.05), size=13.0)
    base.textbox(s, "控制逻辑的关键是“有效信号触发处理，无效等待自动回退”。", Inches(5.15), Inches(4.72), Inches(5.85), Inches(0.48), size=14.4, bold=True, color=base.TEAL)
    base.caption(s, "图 2：声学释放器软件系统架构", "report.pdf, 图 2", Inches(1.05), Inches(6.16), Inches(3.45))
    base.footer(s, 9)
    base.note(s, "强调休眠唤醒、乒乓缓存和同步超时回退。")

    s = base.blank(prs)
    base.header(s, "SFH-MFSK 与 LFM 共同构成通信测距一体化帧", CHAPTERS[2])
    base.image(s, "sfh_mfsk_transmitter.png", Inches(0.83), Inches(1.15), Inches(5.15), Inches(1.55))
    base.image(s, "sfh_mfsk_receiver.png", Inches(0.83), Inches(3.45), Inches(5.15), Inches(1.70))
    base.bullets(s, ["慢跳频降低频繁换频带来的同步与控制开销", "MFSK 适合基于能量的非相干判决", "LFM 同步峰用于帧同步与传播时延估计"], Inches(6.62), Inches(1.45), Inches(4.85), Inches(1.65), size=13.0)
    base.textbox(s, "一帧信号同时服务两个任务：远程指令传输 + 到达时刻提取。", Inches(6.62), Inches(4.25), Inches(4.85), Inches(0.55), size=15, bold=True, color=base.BLUE)
    formula_box(s, "S(t) = x(t) · h(t)\nR(t) = S(t) + N(t) + I(t)", Inches(6.66), Inches(3.70), Inches(4.75), Inches(0.48), size=10.8)
    base.caption(s, "图 3-4：SFH-MFSK 发射端与接收端处理框图", "report.pdf, 图 3-4", Inches(0.83), Inches(5.38), Inches(5.15))
    base.footer(s, 10)
    base.note(s, "讲清 SFH-MFSK 和 LFM 的分工。")

    s = base.blank(prs)
    base.header(s, "跳频与并行 Notch 滤波支撑窄带干扰抑制", CHAPTERS[2])
    base.image(s, "fh_system_model.png", Inches(0.78), Inches(1.10), Inches(6.35), Inches(1.80))
    base.image(s, "parallel_multichannel_notch_structure.png", Inches(0.78), Inches(3.35), Inches(4.95), Inches(2.55))
    base.image(s, "multichannel_notch_response.png", Inches(7.18), Inches(3.25), Inches(3.65), Inches(2.65))
    base.bullets(s, ["跳频解跳后，有用信号经带通滤波保留", "并行通道分别对应不同参考频点", "残差信号用于自适应权值更新"], Inches(7.55), Inches(1.25), Inches(3.85), Inches(1.35), size=12.1)
    base.caption(s, "图 5 与图 8：跳频模型、并行多通道 Notch 滤波结构及响应", "report.pdf, 图 5、图 8", Inches(0.78), Inches(6.05), Inches(8.8))
    base.footer(s, 11)
    base.note(s, "说明通信抗干扰处理的当前结果。")

    s = base.blank(prs)
    base.header(s, "仿真结果初步验证通信链路闭合和参数敏感性", CHAPTERS[2])
    base.image(s, "fh_mfsk_ber.png", Inches(0.78), Inches(1.10), Inches(5.20), Inches(3.70))
    base.image(s, "spectrum_chain.png", Inches(6.30), Inches(1.10), Inches(5.20), Inches(3.70))
    base.textbox(s, "当前仿真已覆盖时域、频谱与误码率趋势；后续需补充多径、频偏、窄带干扰强度等对照组。", Inches(1.05), Inches(5.10), Inches(10.20), Inches(0.48), size=12.8, bold=True, color=base.BLUE, align=PP_ALIGN.CENTER)
    base.caption(s, "图 9-10：误码率与频谱链路仿真结果", "report.pdf, 图 9-10", Inches(0.78), Inches(5.82), Inches(7.5))
    base.footer(s, 12)
    base.note(s, "谨慎说明只是基础仿真和趋势观察。")

    s = base.blank(prs)
    base.header(s, "测距工作已建立声线跟踪理论与初步仿真链路", CHAPTERS[2])
    base.image(s, "ranging_snell_law.png", Inches(0.78), Inches(1.07), Inches(3.25), Inches(2.55))
    base.image(s, "ranging_layered_ray.png", Inches(4.25), Inches(1.07), Inches(3.25), Inches(2.55))
    base.image(s, "fangzhen.png", Inches(0.78), Inches(4.03), Inches(6.80), Inches(1.85))
    base.bullets(s, ["实际声线路径受声速剖面影响，并非理想直线", "分层常声速模型保留声线弯曲修正能力", "已知传播时延时，可反求路径参数并修正距离"], Inches(8.02), Inches(1.38), Inches(3.25), Inches(1.55), size=12.0)
    formula_box(s, "sin θᵢ / cᵢ = p\ny = Σ p cᵢΔzᵢ / √(1 - (p cᵢ)²)", Inches(8.02), Inches(3.00), Inches(3.15), Inches(0.82), size=10.0, color=base.ORANGE)
    base.textbox(s, "本报告只研究声线跟踪法，不展开其他声速修正方法。", Inches(8.02), Inches(4.80), Inches(3.10), Inches(0.48), size=12.0, bold=True, color=base.ORANGE)
    base.caption(s, "图 12-14：Snell 法则、分层声线跟踪和测距算法仿真结果", "report.pdf, 图 12-14", Inches(0.78), Inches(6.05), Inches(7.2))
    base.footer(s, 13)
    base.note(s, "第三章最后用测距理论和仿真收束当前完成结果。")

    # Chapter 4
    chapter_slide(prs, 4, CHAPTERS[3])
    s = base.blank(prs)
    base.header(s, "创新点集中在深度未知测距修正与通信测距一体化", CHAPTERS[3])
    base.chip(s, "创新点 1", "不依赖目标深度先验信息的快速声线测距方法。", Inches(0.95), Inches(1.18), Inches(4.55), base.BLUE)
    base.chip(s, "创新点 2", "面向低功耗释放器的通信测距一体化帧组织。", Inches(6.28), Inches(1.18), Inches(4.55), base.TEAL)
    base.bullets(s, ["以传播时延估计和声速剖面修正为基础", "降低常规声线跟踪对目标深度输入的依赖", "一次声学交互兼顾通信控制与距离估计"], Inches(1.18), Inches(3.22), Inches(4.95), Inches(1.10), size=12.8)
    base.bullets(s, ["已完成总体方案与控制流程设计", "已完成 SFH-MFSK 通信体制与帧结构初步设计", "已搭建通信仿真框架并整理快速声线测距模型"], Inches(6.50), Inches(3.22), Inches(4.85), Inches(1.30), size=12.8)
    base.textbox(s, "阶段成果：系统方案、收发处理、抗干扰模型、测距理论和基础仿真均已形成。", Inches(1.05), Inches(5.82), Inches(10.2), Inches(0.33), size=13.5, bold=True, color=base.BLUE, align=PP_ALIGN.CENTER)
    base.footer(s, 15)
    base.note(s, "第四章对应创新点与成果，既讲两个创新点，也讲已经取得的四类成果。")

    # Chapter 5
    chapter_slide(prs, 5, CHAPTERS[4])
    s = base.blank(prs)
    base.header(s, "后续研究计划围绕系统完善、算法优化和实验验证推进", CHAPTERS[4])
    base.chip(s, "系统完善", "细化指令生成、声学发送、接收采样、同步检测、指令判决、释放执行和应答反馈时序。", Inches(0.82), Inches(1.08), Inches(3.35), base.BLUE)
    base.chip(s, "算法优化", "优化跳频频点间隔、驻留时间、MFSK 符号长度、判决门限和同步检测门限。", Inches(4.55), Inches(1.08), Inches(3.35), base.TEAL)
    base.chip(s, "测距完善", "推导目标深度未知条件下的距离解算流程，并与已知深度声线跟踪结果对比。", Inches(8.28), Inches(1.08), Inches(3.35), base.ORANGE)
    base.chip(s, "实验验证", "补充不同 SNR、多径、传播距离、干扰强度和声速剖面条件下的对照实验。", Inches(0.82), Inches(3.32), Inches(3.35), base.BLUE_2)
    base.chip(s, "外场数据", "开展水池、湖试或海试数据采集，记录环境声速、布放距离和系统响应状态。", Inches(4.55), Inches(3.32), Inches(3.35), base.GREEN)
    base.chip(s, "论文写作", "同步整理系统设计、算法原理、仿真验证、试验分析和结论展望。", Inches(8.28), Inches(3.32), Inches(3.35), base.ORANGE)
    base.textbox(s, "计划主线：把基础链路验证推进到多场景参数优化和实测数据闭环。", Inches(1.05), Inches(6.03), Inches(10.2), Inches(0.32), size=13.8, bold=True, color=base.BLUE, align=PP_ALIGN.CENTER)
    base.footer(s, 17)
    base.note(s, "第五章按系统完善、算法优化、实验验证和论文写作四类计划展开。")

    # Chapter 6
    chapter_slide(prs, 6, CHAPTERS[5])
    s = base.blank(prs)
    base.header(s, "后续难点主要来自复杂信道、深度未知和外场不可重复", CHAPTERS[5])
    base.chip(s, "同步与指令判决", "低 SNR、多径扩展、频率选择性衰落和窄带干扰会影响 LFM 同步峰与 MFSK 能量统计。", Inches(0.82), Inches(1.08), Inches(3.35), base.BLUE)
    base.chip(s, "深度未知测距", "目标深度缺失可能导致声线路径多解或误差放大，需明确近似条件和适用范围。", Inches(4.55), Inches(1.08), Inches(3.35), base.TEAL)
    base.chip(s, "参数权衡", "通信可靠性、测距精度、实时性和功耗之间需要综合优化。", Inches(8.28), Inches(1.08), Inches(3.35), base.ORANGE)
    base.textbox(s, "不确定性", Inches(1.00), Inches(3.70), Inches(1.50), Inches(0.32), size=15, bold=True, color=base.TEXT)
    base.bullets(s, [
        "仿真模型仍简化了真实水声信道，最优参数未必能直接迁移到湖试或海试",
        "声速剖面变化剧烈、传播距离较远或同步峰不稳定时，测距误差可能增大",
        "发射延迟、接收通道延迟、采样时钟误差和换能器响应差异需要统一标定",
        "外场环境噪声、平台姿态、换能器指向性和实际距离测量误差会影响验证结果",
    ], Inches(1.00), Inches(4.16), Inches(10.35), Inches(1.42), size=12.3)
    base.textbox(s, "应对思路：通过多场景仿真、水池标定和外场重复试验，给出方法适用条件与误差边界。", Inches(1.00), Inches(6.05), Inches(10.35), Inches(0.32), size=13.2, bold=True, color=base.BLUE)
    base.footer(s, 19)
    base.note(s, "第六章讲主要难点与不确定性，以及后续如何降低风险。")

    # thanks
    s = base.blank(prs)
    base.add_logo(s, Inches(0.55), Inches(0.28), Inches(2.35))
    base.textbox(s, "THANKS", Inches(0.62), Inches(2.20), Inches(4.80), Inches(0.85), size=45, bold=True, color=base.BLUE)
    line = s.shapes.add_shape(base.MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(3.42), Inches(7.65), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = base.BLUE
    line.line.fill.background()
    base.textbox(s, "感谢聆听！", Inches(4.70), Inches(3.58), Inches(3.0), Inches(0.50), size=22, bold=True, color=base.BLUE)
    base.textbox(s, "基于 SFH-MFSK 的声学释放器技术研究与实现\n张冬林  S324527148", Inches(4.70), Inches(4.35), Inches(4.0), Inches(0.55), size=12.0, color=base.MUTED)
    base.note(s, "结束页。可在此接受老师提问。")

    prs.save(OUT_PPTX)
    print(f"saved {OUT_PPTX} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    build()
