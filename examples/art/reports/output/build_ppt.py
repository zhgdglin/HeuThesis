from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
ASSETS = OUT / "assets" / "figures"
PPTX = OUT / "final_presentation_cn.pptx"


W, H = Inches(13.333), Inches(7.5)
M = Inches(0.46)
TITLE_Y = Inches(0.28)
TITLE_H = Inches(0.55)
FOOT_Y = Inches(7.12)

COLORS = {
    "ink": RGBColor(32, 43, 54),
    "muted": RGBColor(95, 105, 116),
    "light": RGBColor(246, 248, 250),
    "line": RGBColor(210, 216, 222),
    "blue": RGBColor(36, 92, 146),
    "teal": RGBColor(0, 121, 119),
    "orange": RGBColor(190, 103, 46),
    "green": RGBColor(70, 135, 95),
}


def set_run_font(run, size=14, bold=False, color="ink"):
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = COLORS[color]


def add_textbox(slide, text, x, y, w, h, size=14, bold=False, color="ink",
                align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, line_spacing=1.08):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.word_wrap = True
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for i, line in enumerate(text.split("\n")):
        if i:
            p = tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        set_run_font(run, size=size, bold=bold, color=color)
    return box


def add_title(slide, title, kicker=None):
    add_textbox(slide, title, M, TITLE_Y, Inches(9.8), TITLE_H,
                size=26, bold=True, color="ink")
    if kicker:
        add_textbox(slide, kicker, Inches(10.35), Inches(0.34),
                    Inches(2.5), Inches(0.32), size=8.5, color="muted",
                    align=PP_ALIGN.RIGHT)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, M, Inches(0.98),
                                  Inches(12.42), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = COLORS["line"]
    line.line.fill.background()


def add_footer(slide, idx):
    add_textbox(slide, f"基于 SFH-MFSK 的声学释放器技术研究与实现  |  {idx}",
                M, FOOT_Y, Inches(12.42), Inches(0.22), size=7.5,
                color="muted", align=PP_ALIGN.RIGHT)


def add_bullets(slide, bullets, x, y, w, h, size=13.5, color="ink"):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ""
        p.level = 0
        p.line_spacing = 1.08
        p.space_after = Pt(5)
        run = p.add_run()
        run.text = "• " + b
        set_run_font(run, size=size, color=color)
    return box


def add_chip(slide, label, value, x, y, w, accent):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, Inches(0.78))
    rect.fill.solid()
    rect.fill.fore_color.rgb = RGBColor(255, 255, 255)
    rect.line.color.rgb = COLORS["line"]
    add_textbox(slide, label, x + Inches(0.12), y + Inches(0.10), w - Inches(0.24),
                Inches(0.22), size=8.5, color="muted")
    add_textbox(slide, value, x + Inches(0.12), y + Inches(0.36), w - Inches(0.24),
                Inches(0.28), size=14, bold=True, color=accent)


def add_caption(slide, text, x, y, w):
    add_textbox(slide, text, x, y, w, Inches(0.26), size=8.5, color="muted")


def add_note(slide, note):
    notes = slide.notes_slide.notes_text_frame
    notes.clear()
    p = notes.paragraphs[0]
    p.text = note


def image_box(slide, name, x, y, w, h, line=True):
    path = ASSETS / name
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    left = x + int((w - pw) / 2)
    top = y + int((h - ph) / 2)
    if line:
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(255, 255, 255)
        bg.line.color.rgb = COLORS["line"]
    pic = slide.shapes.add_picture(str(path), left, top, width=pw, height=ph)
    return pic


def add_source(slide, source, x, y, w):
    add_textbox(slide, "Source: " + source, x, y, w, Inches(0.20),
                size=7.5, color="muted")


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_section_label(slide, text, x, y, color="blue"):
    add_textbox(slide, text, x, y, Inches(1.3), Inches(0.24),
                size=9, bold=True, color=color)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    slides = []

    # 1
    s = blank(prs)
    add_textbox(s, "基于 SFH-MFSK 的\n声学释放器技术研究与实现",
                Inches(0.72), Inches(1.05), Inches(8.9), Inches(1.4),
                size=30, bold=True)
    add_textbox(s, "中期汇报 | 水声工程学院 | 电子信息",
                Inches(0.75), Inches(2.72), Inches(6.5), Inches(0.35),
                size=13, color="muted")
    add_textbox(s, "张冬林  S324527148\n指导教师：葛威 副教授\n2026 年 8 月",
                Inches(0.75), Inches(3.28), Inches(4.6), Inches(0.86),
                size=13.5, color="ink")
    image_box(s, "software_system.png", Inches(5.9), Inches(3.08),
              Inches(6.7), Inches(3.2))
    add_caption(s, "系统主线：远程指令下发、声学接收判决、释放执行与应答反馈闭环",
                Inches(5.9), Inches(6.38), Inches(6.7))
    add_note(s, "开场先说明本报告来自中期 PDF，主题是面向水下观测设备布放与回收的低功耗声学释放器。核心不是单一算法，而是通信、测距和释放控制闭环的工程化组合。")
    slides.append(s)

    # 2
    s = blank(prs)
    add_title(s, "水下释放器需要同时解决远程控制、低功耗和快速测距", "研究背景")
    add_textbox(s, "应用约束", Inches(0.72), Inches(1.22), Inches(2.1), Inches(0.35),
                size=15, bold=True, color="blue")
    add_bullets(s, [
        "水下端长期值守，能耗预算有限",
        "水声信道存在低 SNR、多径和窄带干扰",
        "回收前需要可靠释放并获得距离估计",
    ], Inches(0.72), Inches(1.72), Inches(4.0), Inches(1.65), size=14)
    add_textbox(s, "技术目标", Inches(5.05), Inches(1.22), Inches(2.1), Inches(0.35),
                size=15, bold=True, color="teal")
    add_bullets(s, [
        "建立通信与测距一体化信号链路",
        "保证释放指令识别与状态反馈闭环",
        "在目标深度未知时进行快速距离修正",
    ], Inches(5.05), Inches(1.72), Inches(4.2), Inches(1.65), size=14)
    add_textbox(s, "阶段判断", Inches(9.55), Inches(1.22), Inches(2.1), Inches(0.35),
                size=15, bold=True, color="orange")
    add_bullets(s, [
        "系统框架已清晰",
        "算法链路已初步仿真",
        "外场边界仍需验证",
    ], Inches(9.55), Inches(1.72), Inches(3.1), Inches(1.65), size=14)
    add_textbox(s, "论文主问题：在复杂水声环境中，用低复杂度方案完成“可唤醒、可解码、可释放、可测距”。",
                Inches(0.72), Inches(4.52), Inches(11.9), Inches(0.72),
                size=20, bold=True, color="ink")
    add_footer(s, 2)
    add_note(s, "这一页用于把工程约束压缩成一句话：设备必须长期等待，但一旦收到有效声学信号，就要可靠判决、执行释放，并尽量给出距离信息。")
    slides.append(s)

    # 3
    s = blank(prs)
    add_title(s, "中期工作已经形成从系统到算法的完整技术链路", "完成情况")
    add_chip(s, "系统方案", "总体架构与控制流程", Inches(0.72), Inches(1.24), Inches(3.7), "blue")
    add_chip(s, "通信体制", "SFH-MFSK + LFM", Inches(4.82), Inches(1.24), Inches(3.7), "teal")
    add_chip(s, "测距方法", "声线跟踪修正", Inches(8.92), Inches(1.24), Inches(3.7), "orange")
    add_textbox(s, "已完成", Inches(0.72), Inches(2.45), Inches(1.3), Inches(0.28),
                size=12, bold=True, color="green")
    add_bullets(s, [
        "声学释放器总体方案、模块划分和软硬件协同架构",
        "休眠唤醒、指令解析、释放执行和应答反馈逻辑",
        "发射端、接收端、跳频模型和抗窄带干扰处理框架",
        "基于传播时延和分层声速剖面的测距理论整理",
    ], Inches(0.72), Inches(2.86), Inches(6.1), Inches(2.1), size=13.5)
    add_textbox(s, "待推进", Inches(7.25), Inches(2.45), Inches(1.3), Inches(0.28),
                size=12, bold=True, color="orange")
    add_bullets(s, [
        "低 SNR、多径、频偏条件下的参数优化",
        "同步峰提取和 MFSK 判决门限稳定性分析",
        "目标深度未知条件下的误差边界与适用范围",
        "水池、湖试或海试数据对模型参数的修正",
    ], Inches(7.25), Inches(2.86), Inches(5.35), Inches(2.1), size=13.5)
    add_footer(s, 3)
    add_note(s, "这里强调中期阶段的边界：系统和算法主线已经打通，但性能的定量边界还需要后续实验和复杂信道仿真补齐。")
    slides.append(s)

    # 4
    s = blank(prs)
    add_title(s, "总体架构把水面控制与水下执行闭合成双向链路", "系统方案")
    image_box(s, "software_system.png", Inches(0.78), Inches(1.20),
              Inches(8.1), Inches(4.75))
    add_bullets(s, [
        "水面端负责人机交互、指令编码和回传解码",
        "水下端完成声信号接收、解码、执行与反馈",
        "双向水声链路支撑状态确认和回收控制",
    ], Inches(9.25), Inches(1.58), Inches(3.25), Inches(2.05), size=13)
    add_textbox(s, "汇报重点：先保证闭环控制可用，再把通信可靠性和测距精度作为算法优化目标。",
                Inches(9.25), Inches(4.55), Inches(3.25), Inches(0.86),
                size=13.5, bold=True, color="blue")
    add_caption(s, "图 1：声学释放器硬件系统架构", Inches(0.78), Inches(6.08), Inches(8.1))
    add_source(s, "report.pdf, 图 1", Inches(0.78), Inches(6.38), Inches(8.1))
    add_footer(s, 4)
    add_note(s, "讲图时沿水面端到水下端的箭头走：指令编码、声学发送、接收解码、执行释放，再通过反馈链路回到水面。")
    slides.append(s)

    # 5
    s = blank(prs)
    add_title(s, "休眠唤醒流程降低值守功耗，并保留同步超时回退", "控制逻辑")
    image_box(s, "sfq_logic.png", Inches(1.05), Inches(1.14),
              Inches(4.0), Inches(5.65))
    add_bullets(s, [
        "未检测到唤醒信号时维持低功耗等待",
        "唤醒后通过乒乓缓存保持采样与处理连续",
        "同步信号 5 min 内未到达则返回休眠检测",
        "释放指令触发动作，其余指令执行后发送应答",
    ], Inches(5.75), Inches(1.54), Inches(6.1), Inches(2.35), size=14)
    add_textbox(s, "控制流程的关键是“有效信号触发处理，无效等待自动回退”，这与低功耗释放器的长期布放需求一致。",
                Inches(5.75), Inches(4.82), Inches(6.1), Inches(0.82),
                size=15, bold=True, color="teal")
    add_caption(s, "图 2：声学释放器软件系统架构", Inches(1.05), Inches(6.88), Inches(4.0))
    add_source(s, "report.pdf, 图 2", Inches(5.75), Inches(6.42), Inches(6.1))
    add_footer(s, 5)
    add_note(s, "这一页不要逐框解释，重点讲两个机制：乒乓缓存保证采样与解码衔接，5 分钟同步超时保证系统不会被无效唤醒长期拖住。")
    slides.append(s)

    # 6
    s = blank(prs)
    add_title(s, "SFH-MFSK 承载短指令，LFM 提供同步与测距时间基准", "通信体制")
    image_box(s, "sfh_mfsk_transmitter.png", Inches(0.72), Inches(1.28),
              Inches(5.75), Inches(1.75))
    image_box(s, "sfh_mfsk_receiver.png", Inches(0.72), Inches(3.78),
              Inches(5.75), Inches(1.85))
    add_caption(s, "图 3-4：SFH-MFSK 发射端与接收端处理框图", Inches(0.72), Inches(5.86), Inches(5.75))
    add_bullets(s, [
        "慢跳频降低频繁换频带来的同步与控制开销",
        "MFSK 支持基于能量的非相干判决",
        "LFM 同步峰用于帧同步和传播时延估计",
    ], Inches(7.02), Inches(1.52), Inches(5.45), Inches(1.85), size=14)
    add_textbox(s, "一帧信号同时服务两个任务：远程指令传输 + 到达时刻提取。",
                Inches(7.02), Inches(4.45), Inches(5.45), Inches(0.72),
                size=18, bold=True, color="blue")
    add_source(s, "report.pdf, 图 3-4", Inches(0.72), Inches(6.22), Inches(5.75))
    add_footer(s, 6)
    add_note(s, "这里把 SFH-MFSK 和 LFM 的分工说清楚：前者承载控制信息，后者提供稳定同步和测距时间基准。")
    slides.append(s)

    # 7
    s = blank(prs)
    add_title(s, "跳频模型把窄带干扰搬移到可滤除频带之外", "跳频原理")
    image_box(s, "fh_system_model.png", Inches(0.74), Inches(1.34),
              Inches(11.85), Inches(3.25))
    add_bullets(s, [
        "接收信号包含有用信号、多径/多用户干扰、环境噪声和人为窄带干扰",
        "收发双方共享跳频图案，接收端利用本地跳频信号完成解跳",
        "解跳后的有用信号经带通滤波保留，干扰被抑制",
    ], Inches(0.82), Inches(5.10), Inches(8.55), Inches(1.05), size=12.8)
    add_textbox(s, "关键参数：频点间隔、驻留时间、处理增益与抗多径条件共同决定可靠性。",
                Inches(9.70), Inches(5.05), Inches(2.75), Inches(0.86),
                size=12.5, bold=True, color="orange")
    add_caption(s, "图 5：跳频系统的数学模型", Inches(0.74), Inches(4.76), Inches(11.85))
    add_source(s, "report.pdf, 图 5", Inches(0.74), Inches(6.35), Inches(11.85))
    add_footer(s, 7)
    add_note(s, "按模型式 R(t)=S(t)+干扰+噪声 来解释就够了。报告中后续参数优化会围绕频点间隔、驻留时间和判决门限展开。")
    slides.append(s)

    # 8
    s = blank(prs)
    add_title(s, "并行多通道 Notch 滤波用于抑制多个候选频点干扰", "抗干扰处理")
    image_box(s, "parallel_multichannel_notch_structure.png", Inches(0.78), Inches(1.22),
              Inches(7.15), Inches(4.80))
    image_box(s, "multichannel_notch_response.png", Inches(8.25), Inches(1.62),
              Inches(3.75), Inches(3.30))
    add_bullets(s, [
        "各通道对应不同参考频点",
        "总输出由多通道估计量叠加得到",
        "残差信号用于自适应权值更新",
    ], Inches(8.25), Inches(5.15), Inches(3.75), Inches(0.95), size=12.8)
    add_caption(s, "图 8：并行多通道 Notch 滤波器结构及多频点响应", Inches(0.78), Inches(6.13), Inches(7.15))
    add_source(s, "report.pdf, 图 8", Inches(0.78), Inches(6.43), Inches(7.15))
    add_footer(s, 8)
    add_note(s, "这页主要讲为什么从单通道扩展到多通道：SFH-MFSK 解跳后会面对多个候选频点，单个陷波器不足以覆盖并行判决的需求。")
    slides.append(s)

    # 9
    s = blank(prs)
    add_title(s, "仿真表明通信链路可闭合，但低 SNR 下参数仍敏感", "通信仿真")
    image_box(s, "fh_mfsk_ber.png", Inches(0.70), Inches(1.15),
              Inches(5.2), Inches(3.95))
    image_box(s, "spectrum_chain.png", Inches(6.18), Inches(1.15),
              Inches(6.25), Inches(3.95))
    add_textbox(s, "当前仿真已覆盖时域、频谱与误码率趋势；后续需要补充多径、频偏、窄带干扰强度等对照组，定量确定门限和跳频参数。",
                Inches(0.90), Inches(5.34), Inches(11.30), Inches(0.58),
                size=13.5, bold=True, color="blue")
    add_caption(s, "图 9-10：误码率与频谱链路仿真结果（时域链路见讲稿说明）", Inches(0.70), Inches(6.12), Inches(11.7))
    add_source(s, "report.pdf, 图 9-10", Inches(0.70), Inches(6.42), Inches(11.7))
    add_footer(s, 9)
    add_note(s, "这里谨慎表述：不夸大为最终性能结论，只说链路闭合和趋势观察。正文中的时域链路图显示同步信号、跳频调制、加噪和接收处理之间的对应关系；低信噪比、多径、频偏下仍需参数优化。")
    slides.append(s)

    # 10
    s = blank(prs)
    add_title(s, "测距模型用 Snell 常数连接声速剖面、传播时间和水平距离", "测距理论")
    image_box(s, "ranging_snell_law.png", Inches(0.78), Inches(1.22),
              Inches(4.05), Inches(3.40))
    image_box(s, "ranging_layered_ray.png", Inches(5.15), Inches(1.22),
              Inches(4.05), Inches(3.40))
    add_bullets(s, [
        "实际传播路径受声速剖面影响，并非理想直线",
        "分层常声速模型保留声线弯曲修正能力",
        "已知传播时延时，可反求路径参数并修正距离",
    ], Inches(9.55), Inches(1.62), Inches(2.85), Inches(1.85), size=12.5)
    add_textbox(s, "本报告只研究声线跟踪法，不展开其他声速修正方法。",
                Inches(9.55), Inches(4.48), Inches(2.85), Inches(0.66),
                size=12.5, bold=True, color="orange")
    add_caption(s, "图 12-13：Snell 法则与分层常声速声线跟踪", Inches(0.78), Inches(4.86), Inches(8.42))
    add_source(s, "report.pdf, 图 12-13", Inches(0.78), Inches(6.32), Inches(8.42))
    add_footer(s, 10)
    add_note(s, "这一页呼应用户正文中的限定：只研究声线跟踪法。讲公式时强调 Snell 常数 p 在分层模型中的作用，以及传播时延约束如何进入水平距离求解。")
    slides.append(s)

    # 11
    s = blank(prs)
    add_title(s, "测距仿真用于检查时延估计、声速修正和距离解算衔接", "测距仿真")
    image_box(s, "fangzhen.png", Inches(0.78), Inches(1.25),
              Inches(11.25), Inches(3.78))
    add_bullets(s, [
        "左：声速剖面为声线修正提供环境输入",
        "中：分层声线跟踪描述折线路径变化",
        "右：测距误差随距离变化的趋势用于后续对照",
    ], Inches(0.86), Inches(5.46), Inches(8.6), Inches(0.82), size=12.8)
    add_textbox(s, "下一步需在噪声、多径和声速梯度变化下给出误差边界。",
                Inches(9.72), Inches(5.35), Inches(2.6), Inches(0.72),
                size=12.5, bold=True, color="teal")
    add_caption(s, "图 14：测距算法仿真结果", Inches(0.78), Inches(5.10), Inches(11.25))
    add_source(s, "report.pdf, 图 14", Inches(0.78), Inches(6.42), Inches(11.25))
    add_footer(s, 11)
    add_note(s, "这一页只给阶段性判断：图展示了模型链路可以跑通，但还不是外场精度结论。后续重点是噪声、多径、声速剖面和深度未知带来的误差边界。")
    slides.append(s)

    # 12
    s = blank(prs)
    add_title(s, "当前创新集中在“通信测距一体化”和“深度未知测距修正”", "创新点")
    add_section_label(s, "创新点 1", Inches(0.82), Inches(1.40), "blue")
    add_textbox(s, "不依赖目标深度先验信息的快速声线测距方法",
                Inches(0.82), Inches(1.78), Inches(5.35), Inches(0.56),
                size=17, bold=True)
    add_bullets(s, [
        "以传播时延估计和声速剖面修正为基础",
        "降低常规声线跟踪对目标深度输入的依赖",
        "面向释放器回收前快速定位需求",
    ], Inches(0.82), Inches(2.58), Inches(5.30), Inches(1.35), size=13)
    add_section_label(s, "创新点 2", Inches(6.95), Inches(1.40), "teal")
    add_textbox(s, "面向低功耗释放器的通信测距一体化帧组织",
                Inches(6.95), Inches(1.78), Inches(5.35), Inches(0.56),
                size=17, bold=True)
    add_bullets(s, [
        "SFH-MFSK 承载短控制指令",
        "LFM 支撑帧同步和到达时刻提取",
        "一次声学交互兼顾通信控制与距离估计",
    ], Inches(6.95), Inches(2.58), Inches(5.30), Inches(1.35), size=13)
    add_textbox(s, "阶段成果：系统方案、收发处理框图、跳频抗干扰模型、声线跟踪测距模型与基础仿真均已形成。",
                Inches(1.08), Inches(5.45), Inches(11.05), Inches(0.62),
                size=16, bold=True, color="green", align=PP_ALIGN.CENTER)
    add_footer(s, 12)
    add_note(s, "这一页用于论文贡献归纳。建议口头强调：创新点还需要后续实验支撑，因此表述为技术思路和阶段成果，不夸大为已经完成的工程指标。")
    slides.append(s)

    # 13
    s = blank(prs)
    add_title(s, "后续工作应优先把复杂信道下的误差边界定量化", "计划与风险")
    add_textbox(s, "系统完善", Inches(0.82), Inches(1.30), Inches(2.4), Inches(0.28),
                size=13, bold=True, color="blue")
    add_bullets(s, [
        "细化指令生成、采样、判决与反馈时序",
        "完成换能器驱动、接收通道和释放机构联调",
    ], Inches(0.82), Inches(1.72), Inches(3.55), Inches(0.95), size=12.5)
    add_textbox(s, "算法优化", Inches(4.88), Inches(1.30), Inches(2.4), Inches(0.28),
                size=13, bold=True, color="teal")
    add_bullets(s, [
        "优化跳频频点间隔、驻留时间和判决门限",
        "推导目标深度未知条件下的距离解算流程",
    ], Inches(4.88), Inches(1.72), Inches(3.55), Inches(0.95), size=12.5)
    add_textbox(s, "实验验证", Inches(8.95), Inches(1.30), Inches(2.4), Inches(0.28),
                size=13, bold=True, color="orange")
    add_bullets(s, [
        "补充 SNR、多径、干扰强度和声速剖面对照",
        "开展水池、湖试或海试数据采集与模型修正",
    ], Inches(8.95), Inches(1.72), Inches(3.55), Inches(0.95), size=12.5)
    add_textbox(s, "主要不确定性", Inches(0.82), Inches(3.62), Inches(2.2), Inches(0.28),
                size=14, bold=True)
    add_bullets(s, [
        "同步峰展宽、偏移或多峰会影响通信判决和时延估计",
        "目标深度未知可能造成声线测距多解或误差放大",
        "通信可靠性、测距精度、实时性和功耗之间存在参数权衡",
        "外场环境不可重复，需要完整记录环境声速和布放距离",
    ], Inches(0.82), Inches(4.05), Inches(11.35), Inches(1.55), size=13.2)
    add_textbox(s, "收束逻辑：用更多可控仿真和水池/外场数据，把“可行链路”推进到“可验证指标”。",
                Inches(0.82), Inches(6.05), Inches(11.35), Inches(0.44),
                size=15.5, bold=True, color="blue")
    add_footer(s, 13)
    add_note(s, "结尾不要泛泛而谈，要把后续计划和风险对应起来：同步鲁棒性、测距误差边界、低功耗参数折中、外场数据可信度。")
    slides.append(s)

    prs.save(PPTX)
    return PPTX, len(slides)


if __name__ == "__main__":
    path, count = build()
    print(f"saved {path} ({count} slides)")
