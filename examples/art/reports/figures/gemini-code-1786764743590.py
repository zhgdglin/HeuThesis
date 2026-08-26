from pathlib import Path


SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <title>Layered ray tracing diagram</title>
  <desc>Editable SVG. Axes, layer lines, ray path, normals, arrows, and labels are independent objects.</desc>

  <style>
    .line { fill: none; stroke: #000000; stroke-width: 2; }
    .thin { fill: none; stroke: #000000; stroke-width: 1.5; }
    .dash { fill: none; stroke: #000000; stroke-width: 1.5; stroke-dasharray: 8 7; }
    .arrow { fill: #000000; stroke: none; }
    .label { fill: #000000; font-family: "Times New Roman", SimSun, serif; font-size: 28px; }
    .sub { font-size: 17px; baseline-shift: sub; }
  </style>

  <line id="axis-y" class="line" x1="105" y1="520" x2="700" y2="520"/>
  <polygon id="axis-y-arrowhead" class="arrow" points="700,520 677,510 677,530"/>
  <line id="axis-z" class="line" x1="105" y1="520" x2="105" y2="70"/>
  <polygon id="axis-z-arrowhead" class="arrow" points="105,70 95,93 115,93"/>

  <line id="layer-ci-minus-1-boundary" class="dash" x1="105" y1="400" x2="700" y2="400"/>
  <line id="layer-ci-boundary" class="dash" x1="105" y1="280" x2="700" y2="280"/>
  <line id="layer-ci-plus-1-boundary" class="dash" x1="105" y1="160" x2="700" y2="160"/>

  <line id="ray-path" class="line" x1="180" y1="520" x2="555" y2="80"/>

  <line id="normal-at-ci-minus-1" class="dash" x1="230" y1="440" x2="230" y2="360"/>
  <line id="normal-at-ci" class="dash" x1="325" y1="320" x2="325" y2="240"/>
  <line id="normal-at-ci-plus-1" class="dash" x1="425" y1="200" x2="425" y2="120"/>

  <path id="theta-i-arc" class="thin" d="M 325 280 A 45 45 0 0 1 354 246"/>
  <path id="theta-i-plus-1-arc" class="thin" d="M 230 400 A 42 42 0 0 0 259 368"/>

  <line id="delta-zi-line" class="thin" x1="520" y1="400" x2="520" y2="280"/>
  <polygon id="delta-zi-top-arrowhead" class="arrow" points="520,280 512,298 528,298"/>
  <polygon id="delta-zi-bottom-arrowhead" class="arrow" points="520,400 512,382 528,382"/>

  <text id="z-axis-label" class="label" x="65" y="95">Z</text>
  <text id="y-axis-label" class="label" x="690" y="490">y</text>

  <text id="theta-i-label" class="label" x="360" y="258">&#952;<tspan class="sub">i</tspan></text>
  <text id="theta-i-plus-1-label" class="label" x="255" y="385">&#952;<tspan class="sub">i+1</tspan></text>

  <text id="c-i-minus-1-label" class="label" x="610" y="455">C<tspan class="sub">i-1</tspan></text>
  <text id="c-i-label" class="label" x="645" y="335">C<tspan class="sub">i</tspan></text>
  <text id="c-i-plus-1-label" class="label" x="660" y="215">C<tspan class="sub">i+1</tspan></text>
  <text id="delta-zi-label" class="label" x="540" y="350">&#916;Z<tspan class="sub">i</tspan></text>
</svg>
"""


def main() -> None:
    Path("refraction_layers.svg").write_text(SVG, encoding="utf-8")


if __name__ == "__main__":
    main()
