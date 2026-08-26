from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
ASSETS = OUT / "assets" / "figures"
TEMPLATE = Path(r"D:\admin\Documents\研一\中期\PPT模板.pptx")
LOGO = OUT / "template_media" / "image6.png"
COVER_PHOTO = OUT / "template_media" / "image2.jpeg"
PPTX = OUT / "final_presentation_cn.pptx"

BLUE = RGBColor(0, 73, 143)
BLUE_2 = RGBColor(28, 96, 158)
ORANGE = RGBColor(224, 153, 36)
TEXT = RGBColor(32, 43, 54)
MUTED = RGBColor(90, 103, 117)
TEAL = RGBColor(0, 121, 119)
GREEN = RGBColor(65, 132, 82)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(198, 208, 218)


def delete_all_slides(prs):
    sld_id_lst = prs.slides._sldIdLst
    for sld_id in list(sld_id_lst):
        r_id = sld_id.rId
        prs.part.drop_rel(r_id)
        sld_id_lst.remove(sld_id)


def font(run, size=14, bold=False, color=TEXT, name="Microsoft YaHei"):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def textbox(slide, text, x, y, w, h, size=14, bold=False, color=TEXT,
            align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.04,
            line_spacing=1.08):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        font(r, size=size, bold=bold, color=color)
    return box


def bullets(slide, items, x, y, w, h, size=14, color=TEXT):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.03)
    tf.margin_right = Inches(0.03)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.05
        p.space_after = Pt(5)
        r = p.add_run()
        r.text = "• " + item
        font(r, size=size, color=color)
    return box


def image(slide, filename, x, y, w, h, border=True):
    path = ASSETS / filename
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    left = x + int((w - pw) / 2)
    top = y + int((h - ph) / 2)
    if border:
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        bg.fill.solid()
        bg.fill.fore_color.rgb = WHITE
        bg.line.color.rgb = LINE
    return slide.shapes.add_picture(str(path), left, top, width=pw, height=ph)


def add_logo(slide, x=Inches(9.98), y=Inches(0.18), w=Inches(1.85)):
    textbox(slide, "哈尔滨工程大学", x, y, w, Inches(0.20),
            size=9.2, bold=True, color=BLUE, align=PP_ALIGN.RIGHT)
    textbox(slide, "HARBIN ENGINEERING UNIVERSITY", x, y + Inches(0.19), w, Inches(0.15),
            size=4.8, color=BLUE, align=PP_ALIGN.RIGHT)


def header(slide, title, section):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0.27), Inches(0.82), Inches(0.36))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    textbox(slide, title, Inches(0.92), Inches(0.22), Inches(8.5), Inches(0.44),
            size=18, bold=True, color=BLUE)
    add_logo(slide)
    if section:
        textbox(slide, section, Inches(9.65), Inches(0.26), Inches(0.78), Inches(0.25),
                size=8.5, color=MUTED, align=PP_ALIGN.RIGHT)


def footer(slide, n):
    textbox(slide, f"基于 SFH-MFSK 的声学释放器技术研究与实现  |  {n}",
            Inches(8.15), Inches(6.83), Inches(3.85), Inches(0.18),
            size=7.2, color=MUTED, align=PP_ALIGN.RIGHT)


def caption(slide, text, source, x, y, w):
    textbox(slide, text, x, y, w, Inches(0.20), size=7.8, color=MUTED)
    textbox(slide, "Source: " + source, x, y + Inches(0.23), w, Inches(0.18), size=7.0, color=MUTED)


def note(slide, text):
    tf = slide.notes_slide.notes_text_frame
    tf.clear()
    tf.paragraphs[0].text = text


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def section_slide(prs, part, title, icon_text):
    slide = blank(prs)
    add_logo(slide)
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(3.04), Inches(2.25), Inches(1.02), Inches(1.02))
    circ.fill.solid()
    circ.fill.fore_color.rgb = BLUE
    circ.line.fill.background()
    textbox(slide, icon_text, Inches(3.12), Inches(2.58), Inches(0.86), Inches(0.25),
            size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(slide, f"Part {part}", Inches(4.25), Inches(2.04), Inches(3.2), Inches(0.72),
            size=38, color=BLUE)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.24), Inches(2.93), Inches(3.64), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = BLUE
    line.line.fill.background()
    textbox(slide, title, Inches(4.70), Inches(3.15), Inches(3.3), Inches(0.45),
            size=23, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
    note(slide, f"进入第 {part} 部分：{title}。")
    return slide


def chip(slide, title, body, x, y, w, color):
    head = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.31))
    head.fill.solid()
    head.fill.fore_color.rgb = color
    head.line.fill.background()
    textbox(slide, title, x + Inches(0.08), y + Inches(0.04), w - Inches(0.16), Inches(0.20),
            size=10.5, bold=True, color=WHITE)
    body_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y + Inches(0.31), w, Inches(1.05))
    body_box.fill.solid()
    body_box.fill.fore_color.rgb = WHITE
    body_box.line.color.rgb = LINE
    textbox(slide, body, x + Inches(0.12), y + Inches(0.48), w - Inches(0.24), Inches(0.62),
            size=11.2, color=TEXT)


def build():
    prs = Presentation(TEMPLATE)
    delete_all_slides(prs)

    # 1 cover
    s = blank(prs)
    add_logo(s, Inches(0.35), Inches(0.24), Inches(2.35))
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.95), Inches(7.15), Inches(1.45))
    band.fill.solid()
    band.fill.fore_color.rgb = BLUE
    band.line.fill.background()
    textbox(s, "基于 SFH-MFSK 的\n声学释放器技术研究与实现",
            Inches(0.82), Inches(2.18), Inches(6.05), Inches(0.88),
            size=25, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if COVER_PHOTO.exists():
        s.shapes.add_picture(str(COVER_PHOTO), Inches(7.05), Inches(1.52), width=Inches(4.65), height=Inches(3.12))
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(3.40), Inches(7.15), Inches(0.055))
    accent.fill.solid()
    accent.fill.fore_color.rgb = ORANGE
    accent.line.fill.background()
    textbox(s, "水声工程学院  电子信息", Inches(1.00), Inches(4.84), Inches(3.1), Inches(0.25),
            size=12.5, color=BLUE)
    textbox(s, "汇报人：张冬林\n学号：S324527148\n指导教师：葛威 副教授\n2026 年 8 月",
            Inches(7.10), Inches(4.62), Inches(3.25), Inches(0.90), size=12.2, color=BLUE)
    note(s, "开场说明本汇报基于当前中期报告 PDF，主题是低功耗声学释放器、SFH-MFSK 通信和不依赖目标深度的快速声线测距。")

    # 2 contents
    s = blank(prs)
    add_logo(s)
    textbox(s, "目 录", Inches(1.12), Inches(2.52), Inches(1.45), Inches(0.55), size=30, bold=True, color=WHITE)
    poly = s.shapes.add_shape(MSO_SHAPE.TRAPEZOID, Inches(0.55), Inches(2.42), Inches(3.35), Inches(1.18))
    poly.fill.solid()
    poly.fill.fore_color.rgb = BLUE
    poly.line.fill.background()
    textbox(s, "目 录\nCONTENTS", Inches(1.22), Inches(2.48), Inches(2.05), Inches(0.86),
            size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    rows = [("1", "研究背景"), ("2", "研究进展"), ("3", "未来规划"), ("4", "汇报总结")]
    for i, (num, txt) in enumerate(rows):
        y = Inches(1.72 + i * 0.78)
        textbox(s, num, Inches(5.10), y, Inches(0.34), Inches(0.36), size=24, bold=True, color=BLUE)
        rect = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.72), y + Inches(0.03), Inches(3.95), Inches(0.40))
        rect.fill.solid()
        rect.fill.fore_color.rgb = WHITE
        rect.line.fill.background()
        textbox(s, txt, Inches(5.92), y + Inches(0.08), Inches(2.50), Inches(0.24), size=14, bold=True, color=BLUE)
    note(s, "目录页采用模板的四段式结构：研究背景、研究进展、未来规划和汇报总结。")

    section_slide(prs, 1, "研究背景", "Part1")

    # 4
    s = blank(prs)
    header(s, "水下释放器需要同时解决远程控制、低功耗和快速测距", "研究背景")
    chip(s, "应用约束", "长期值守、低能耗；低 SNR、多径和窄带干扰并存。", Inches(0.82), Inches(1.20), Inches(3.28), BLUE)
    chip(s, "技术目标", "建立通信测距一体化链路，兼顾释放控制与距离估计。", Inches(4.55), Inches(1.20), Inches(3.28), TEAL)
    chip(s, "阶段判断", "系统框架已清晰；复杂信道下的指标边界仍需验证。", Inches(8.28), Inches(1.20), Inches(3.28), ORANGE)
    textbox(s, "论文主问题：在复杂水声环境中，用低复杂度方案完成“可唤醒、可解码、可释放、可测距”。",
            Inches(1.05), Inches(4.38), Inches(10.25), Inches(0.45), size=20, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
    footer(s, 4)
    note(s, "这一页把工程约束压缩成汇报主问题，强调设备必须在长期等待和可靠动作之间取得平衡。")

    section_slide(prs, 2, "研究进展", "Part2")

    # 6
    s = blank(prs)
    header(s, "中期工作已经形成从系统到算法的完整技术链路", "研究进展")
    bullets(s, [
        "已完成声学释放器总体方案、模块划分和软硬件协同架构",
        "已完成休眠唤醒、指令解析、释放执行和应答反馈逻辑",
        "已完成 SFH-MFSK 发射端、接收端、跳频模型和抗干扰处理框架",
        "已整理 Snell 法则、分层声速模型和快速声线测距思路",
    ], Inches(0.88), Inches(1.20), Inches(5.35), Inches(2.25), size=13.2)
    bullets(s, [
        "低 SNR、多径和频偏条件下仍需优化同步与判决参数",
        "目标深度未知条件下的误差边界仍需定量给出",
        "后续要用水池、湖试或海试数据校正模型参数",
    ], Inches(6.75), Inches(1.20), Inches(4.65), Inches(1.85), size=13.2)
    image(s, "software_system.png", Inches(1.10), Inches(3.65), Inches(5.00), Inches(2.15))
    image(s, "ranging_layered_ray.png", Inches(6.90), Inches(3.50), Inches(3.80), Inches(2.45))
    footer(s, 6)
    note(s, "中期阶段的关键是链路已打通，但定量性能和外场适用边界还需要后续验证。")

    # 7
    s = blank(prs)
    header(s, "总体架构把水面控制与水下执行闭合成双向链路", "研究进展")
    image(s, "software_system.png", Inches(0.80), Inches(1.15), Inches(7.70), Inches(4.20))
    bullets(s, [
        "水面端负责人机交互、指令编码和回传解码",
        "水下端完成接收、解码、执行与反馈",
        "双向水声链路支撑状态确认和回收控制",
    ], Inches(8.85), Inches(1.45), Inches(2.85), Inches(1.80), size=12.4)
    textbox(s, "先保证闭环控制可用，再把通信可靠性和测距精度作为算法优化目标。",
            Inches(8.85), Inches(4.25), Inches(2.72), Inches(0.70), size=12.5, bold=True, color=BLUE)
    caption(s, "图 1：声学释放器硬件系统架构", "report.pdf, 图 1", Inches(0.80), Inches(5.54), Inches(7.70))
    footer(s, 7)
    note(s, "沿图中的水面端到水下端讲清楚指令下发、执行释放和状态反馈闭环。")

    # 8
    s = blank(prs)
    header(s, "休眠唤醒流程降低值守功耗，并保留同步超时回退", "研究进展")
    image(s, "sfq_logic.png", Inches(1.06), Inches(1.05), Inches(3.45), Inches(5.30))
    bullets(s, [
        "未检测到唤醒信号时维持低功耗等待",
        "唤醒后通过乒乓缓存保持采样与处理连续",
        "同步信号 5 min 内未到达则返回休眠检测",
        "释放指令触发动作，其余指令执行后发送应答",
    ], Inches(5.15), Inches(1.45), Inches(5.85), Inches(2.00), size=13.2)
    textbox(s, "控制流程的关键是“有效信号触发处理，无效等待自动回退”。",
            Inches(5.15), Inches(4.66), Inches(5.85), Inches(0.55), size=15, bold=True, color=TEAL)
    caption(s, "图 2：声学释放器软件系统架构", "report.pdf, 图 2", Inches(1.06), Inches(6.16), Inches(3.45))
    footer(s, 8)
    note(s, "重点讲乒乓缓存和 5 min 同步超时回退，避免逐框朗读流程图。")

    # 9
    s = blank(prs)
    header(s, "SFH-MFSK 承载短指令，LFM 提供同步与测距时间基准", "研究进展")
    image(s, "sfh_mfsk_transmitter.png", Inches(0.83), Inches(1.15), Inches(5.15), Inches(1.55))
    image(s, "sfh_mfsk_receiver.png", Inches(0.83), Inches(3.45), Inches(5.15), Inches(1.70))
    bullets(s, [
        "慢跳频降低频繁换频带来的同步与控制开销",
        "MFSK 支持基于能量的非相干判决",
        "LFM 同步峰用于帧同步和传播时延估计",
    ], Inches(6.62), Inches(1.45), Inches(4.85), Inches(1.65), size=13.0)
    textbox(s, "一帧信号同时服务两个任务：远程指令传输 + 到达时刻提取。",
            Inches(6.62), Inches(4.25), Inches(4.85), Inches(0.55), size=15, bold=True, color=BLUE)
    caption(s, "图 3-4：SFH-MFSK 发射端与接收端处理框图", "report.pdf, 图 3-4", Inches(0.83), Inches(5.38), Inches(5.15))
    footer(s, 9)
    note(s, "解释 SFH-MFSK 和 LFM 的分工：前者承载控制信息，后者提供同步和测距时间基准。")

    # 10
    s = blank(prs)
    header(s, "跳频与并行 Notch 滤波共同支撑窄带干扰抑制", "研究进展")
    image(s, "fh_system_model.png", Inches(0.78), Inches(1.10), Inches(6.35), Inches(1.80))
    image(s, "parallel_multichannel_notch_structure.png", Inches(0.78), Inches(3.35), Inches(4.95), Inches(2.55))
    image(s, "multichannel_notch_response.png", Inches(7.18), Inches(3.25), Inches(3.65), Inches(2.65))
    bullets(s, [
        "跳频解跳后，有用信号经带通滤波保留",
        "并行通道分别对应不同参考频点",
        "残差信号用于自适应权值更新",
    ], Inches(7.55), Inches(1.25), Inches(3.85), Inches(1.35), size=12.1)
    caption(s, "图 5 与图 8：跳频模型、并行多通道 Notch 滤波结构及响应", "report.pdf, 图 5、图 8", Inches(0.78), Inches(6.05), Inches(8.8))
    footer(s, 10)
    note(s, "这页讲干扰抑制链条：跳频先分散频域风险，再用多通道 Notch 处理候选频点。")

    # 11
    s = blank(prs)
    header(s, "仿真表明通信链路可闭合，但低 SNR 下参数仍敏感", "研究进展")
    image(s, "fh_mfsk_ber.png", Inches(0.78), Inches(1.10), Inches(5.20), Inches(3.70))
    image(s, "spectrum_chain.png", Inches(6.30), Inches(1.10), Inches(5.20), Inches(3.70))
    textbox(s, "当前仿真已覆盖时域、频谱与误码率趋势；后续需要补充多径、频偏、窄带干扰强度等对照组，定量确定门限和跳频参数。",
            Inches(1.05), Inches(5.10), Inches(10.20), Inches(0.48), size=12.8, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
    caption(s, "图 9-10：误码率与频谱链路仿真结果", "report.pdf, 图 9-10", Inches(0.78), Inches(5.82), Inches(7.5))
    footer(s, 11)
    note(s, "谨慎表述为链路闭合和趋势观察，不夸大为最终外场性能结论。")

    # 12
    s = blank(prs)
    header(s, "测距模型用 Snell 常数连接声速剖面、传播时间和水平距离", "研究进展")
    image(s, "ranging_snell_law.png", Inches(0.78), Inches(1.07), Inches(3.25), Inches(2.55))
    image(s, "ranging_layered_ray.png", Inches(4.25), Inches(1.07), Inches(3.25), Inches(2.55))
    image(s, "fangzhen.png", Inches(0.78), Inches(4.03), Inches(6.80), Inches(1.85))
    bullets(s, [
        "实际传播路径受声速剖面影响，并非理想直线",
        "分层常声速模型保留声线弯曲修正能力",
        "已知传播时延时，可反求路径参数并修正距离",
    ], Inches(8.02), Inches(1.38), Inches(3.25), Inches(1.55), size=12.0)
    textbox(s, "本报告只研究声线跟踪法，不展开其他声速修正方法。",
            Inches(8.02), Inches(4.80), Inches(3.10), Inches(0.48), size=12.0, bold=True, color=ORANGE)
    caption(s, "图 12-14：Snell 法则、分层声线跟踪和测距算法仿真结果", "report.pdf, 图 12-14", Inches(0.78), Inches(6.05), Inches(7.2))
    footer(s, 12)
    note(s, "呼应正文限定：本报告只研究声线跟踪法。讲清楚 Snell 常数、分层模型和传播时延约束之间的关系。")

    # 13
    s = blank(prs)
    header(s, "当前创新集中在通信测距一体化与深度未知测距修正", "研究进展")
    chip(s, "创新点 1", "不依赖目标深度先验信息的快速声线测距方法。", Inches(0.95), Inches(1.30), Inches(4.55), BLUE)
    chip(s, "创新点 2", "面向低功耗释放器的通信测距一体化帧组织。", Inches(6.28), Inches(1.30), Inches(4.55), TEAL)
    bullets(s, [
        "以传播时延估计和声速剖面修正为基础",
        "降低常规声线跟踪对目标深度输入的依赖",
        "一次声学交互兼顾通信控制与距离估计",
    ], Inches(1.18), Inches(3.38), Inches(4.95), Inches(1.10), size=12.8)
    bullets(s, [
        "已形成总体方案、收发框图和基础仿真",
        "已整理跳频抗干扰和声线跟踪测距模型",
        "下一步需用实测数据支撑指标闭环",
    ], Inches(6.50), Inches(3.38), Inches(4.85), Inches(1.10), size=12.8)
    footer(s, 13)
    note(s, "创新点仍按阶段成果表达，不把尚未完成的外场验证包装成最终结论。")

    section_slide(prs, 3, "未来规划", "Part3")

    # 15
    s = blank(prs)
    header(s, "后续工作应优先把复杂信道下的误差边界定量化", "未来规划")
    chip(s, "系统完善", "细化指令生成、采样、判决与反馈时序；完成换能器、接收通道和释放机构联调。", Inches(0.82), Inches(1.14), Inches(3.35), BLUE)
    chip(s, "算法优化", "优化跳频频点间隔、驻留时间和判决门限；推导深度未知条件下的距离解算流程。", Inches(4.55), Inches(1.14), Inches(3.35), TEAL)
    chip(s, "实验验证", "补充 SNR、多径、干扰强度和声速剖面对照；开展水池、湖试或海试验证。", Inches(8.28), Inches(1.14), Inches(3.35), ORANGE)
    textbox(s, "主要不确定性", Inches(0.98), Inches(3.45), Inches(2.00), Inches(0.32), size=15, bold=True, color=TEXT)
    bullets(s, [
        "同步峰展宽、偏移或多峰会影响通信判决和时延估计",
        "目标深度未知可能造成声线测距多解或误差放大",
        "通信可靠性、测距精度、实时性和功耗之间存在参数权衡",
        "外场环境不可重复，需要完整记录环境声速和布放距离",
    ], Inches(0.98), Inches(3.95), Inches(8.8), Inches(1.55), size=12.4)
    textbox(s, "收束逻辑：用更多可控仿真和水池/外场数据，把“可行链路”推进到“可验证指标”。",
            Inches(0.98), Inches(6.07), Inches(10.4), Inches(0.30), size=13.8, bold=True, color=BLUE)
    footer(s, 15)
    note(s, "把后续计划与风险对应起来：同步鲁棒性、测距误差边界、低功耗参数折中和外场数据可信度。")

    section_slide(prs, 4, "汇报总结", "Part4")

    # 17 summary
    s = blank(prs)
    header(s, "汇报总结：系统链路已打通，关键指标待实验闭环", "汇报总结")
    chip(s, "已完成", "总体架构、休眠唤醒、SFH-MFSK 收发链路、跳频抗干扰和声线跟踪模型已形成。", Inches(0.92), Inches(1.25), Inches(3.35), BLUE)
    chip(s, "已验证", "基础仿真覆盖时域、频谱、误码率和测距趋势，证明处理链路具备闭合基础。", Inches(4.62), Inches(1.25), Inches(3.35), TEAL)
    chip(s, "待突破", "复杂信道下同步鲁棒性、深度未知测距误差边界和外场可迁移性仍需定量验证。", Inches(8.32), Inches(1.25), Inches(3.35), ORANGE)
    textbox(s, "下一阶段主线", Inches(1.05), Inches(3.65), Inches(2.0), Inches(0.32), size=15, bold=True, color=TEXT)
    bullets(s, [
        "补充多径、频偏、窄带干扰强度和声速剖面对照仿真",
        "建立同步时延误差、声速剖面误差与测距误差之间的传播关系",
        "通过水池和外场数据完成参数标定与模型修正",
    ], Inches(1.05), Inches(4.15), Inches(8.60), Inches(1.25), size=12.8)
    textbox(s, "汇报结论：当前工作已从方案设计推进到算法链路验证，后续重点是把“可行”转化为“有边界、有指标、可复现”。",
            Inches(0.92), Inches(6.02), Inches(10.95), Inches(0.35), size=13.2, bold=True, color=BLUE)
    footer(s, 17)
    note(s, "总结页用于收束全篇：已经完成的是方案和链路，后续要证明的是复杂水声环境下的指标边界。")

    # 18 thanks
    s = blank(prs)
    add_logo(s, Inches(0.55), Inches(0.28), Inches(2.35))
    textbox(s, "THANKS", Inches(0.62), Inches(2.20), Inches(4.80), Inches(0.85),
            size=45, bold=True, color=BLUE)
    line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(3.42), Inches(7.65), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = BLUE
    line.line.fill.background()
    textbox(s, "感谢聆听！", Inches(4.70), Inches(3.58), Inches(3.0), Inches(0.50),
            size=22, bold=True, color=BLUE)
    textbox(s, "基于 SFH-MFSK 的声学释放器技术研究与实现\n张冬林  S324527148",
            Inches(4.70), Inches(4.35), Inches(4.0), Inches(0.55), size=12.0, color=MUTED)
    note(s, "结束页。可在此接受老师提问。")

    prs.save(PPTX)
    print(f"saved {PPTX} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    build()
