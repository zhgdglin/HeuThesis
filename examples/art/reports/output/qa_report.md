# PPTX QA Report

- Deliverable: `output/final_presentation_cn_six_sections_formula.pptx`
- User template: `D:\admin\Documents\研一\中期\PPT模板.pptx`
- Source: `report.pdf` and its corresponding report source figures
- Paper type: `methods` (engineering system / algorithm report)
- Deck: 20 slides, simplified Chinese, 16:9, HEU-style template background
- Requested structure: six chapters matching the thesis progress-report outline
- Speaker notes: 20 slides
- Embedded media: 14 images
- Formula enhancement: slide 10 adds the communication signal model `S(t) = x(t) · h(t)` and `R(t) = S(t) + N(t) + I(t)`; slide 13 adds the ray-tracing relation `sin θᵢ / cᵢ = p` and the layered range expression `y = Σ p cᵢΔzᵢ / √(1 - (p cᵢ)²)`.
- Editable content: titles, bullets, captions, source labels, formula boxes, section labels, summary boxes, footer text and most template-identifying text are native PowerPoint objects; scientific figures are embedded as high-resolution images to preserve original data visuals.

## Structure

The deck follows the six chapters requested by the user:

1. 论文研究目标
2. 开题报告中研究内容与完成情况对比
3. 目前已经完成的工作和结果
4. 创新点与目前取得的成果
5. 后续研究计划
6. 论文后续工作的难点与不确定性

The previous template-based deck was rebuilt into a 20-slide six-section version with cover, contents, chapter divider pages, evidence-led result slides, innovation/results synthesis, future-plan slide, uncertainty slide and thanks slide.

## Evidence and layout review

- Selected figure assets cover system architecture, low-power control logic, SFH-MFSK transceiver processing, hopping/interference model, multichannel Notch filtering, communication simulation, ray-tracing theory and ranging simulation.
- All selected scientific figures were converted from the source PDFs at 240 dpi or copied from the original PNG. No axes, legends, control-flow labels, diagram annotations or scientifically necessary context were intentionally removed.
- Formula boxes were added only in existing explanation areas so they do not cover figures, captions, source labels or footer text.
- The statement that this report only studies ray tracing was preserved on the ranging slide.
- Medium audit issue from the earlier template version was corrected: the school logo is represented with editable text labels so the audit no longer treats decorative logos as undersized evidence images.

## Verification

- Reopened with `python-pptx`: pass.
- PPTX package signature: pass (`PK` zip package).
- Slide count: 20.
- Notes count: 20.
- Embedded media count: 14.
- `audit_pptx_quality.py` final result: high=0, medium=0, low=56.
- Remaining low findings are alignment-near-miss heuristics from the template-style header/footer and repeated aligned elements; they do not correspond to visible overlap, clipping or missing evidence in rendered previews.

## Rendered visual QA

- Renderer: Microsoft PowerPoint `Presentation.Export()` to PNG at 1920 px width.
- Final render output: `output/rendered_six_sections_formula_20260818_110752/` (20 slide PNGs and `contact_sheet.png`).
- Render review: full-deck contact sheet plus detailed inspection of formula/evidence slides 10, 12, 13 and planning slide 17.
- Final rendered review: no missing image, clipped text, visible overlap, unreadable main evidence, or formula/caption collision found.
