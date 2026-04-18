"""Generate favicon.svg matching the .brand-mark style in styles.css.

The brand mark is a 22x22 rounded square filled with
`conic-gradient(from 210deg at 50% 50%, #ffffff, #9aa0a6, #ffffff)` and a
1px border at rgba(0, 0, 0, 0.25). SVG has no native conic gradient, so the
gradient is approximated with N pie-slice sectors clipped to the rounded
rect.
"""
import math
import os

N = 24
CX = CY = 11
R = 18  # extends beyond the 22x22 viewBox; clipped by the rounded rect


def point_on_css_angle(theta_deg):
    t = math.radians(theta_deg)
    return CX + R * math.sin(t), CY - R * math.cos(t)


def lerp(a, b, f):
    return a + (b - a) * f


def color_at(t):
    if t <= 0.5:
        f = t / 0.5
        r = lerp(255, 154, f)
        g = lerp(255, 160, f)
        b = lerp(255, 166, f)
    else:
        f = (t - 0.5) / 0.5
        r = lerp(154, 255, f)
        g = lerp(160, 255, f)
        b = lerp(166, 255, f)
    return "#%02x%02x%02x" % (round(r), round(g), round(b))


def main():
    parts = []
    for i in range(N):
        a0 = 210 + (360.0 / N) * i
        a1 = 210 + (360.0 / N) * (i + 1)
        x0, y0 = point_on_css_angle(a0)
        x1, y1 = point_on_css_angle(a1)
        col = color_at((i + 0.5) / N)
        d = (
            f"M{CX},{CY} L{x0:.3f},{y0:.3f} "
            f"A{R},{R} 0 0 1 {x1:.3f},{y1:.3f} Z"
        )
        parts.append(f'<path d="{d}" fill="{col}"/>')

    sectors = "\n    ".join(parts)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22">\n'
        "  <defs>\n"
        '    <clipPath id="r">\n'
        '      <rect x="0" y="0" width="22" height="22" rx="6" ry="6"/>\n'
        "    </clipPath>\n"
        "  </defs>\n"
        '  <g clip-path="url(#r)">\n'
        f"    {sectors}\n"
        "  </g>\n"
        '  <rect x="0.5" y="0.5" width="21" height="21" rx="5.5" ry="5.5" '
        'fill="none" stroke="#000000" stroke-opacity="0.25" stroke-width="1"/>\n'
        "</svg>\n"
    )

    out_path = os.path.join(os.path.dirname(__file__), "..", "favicon.svg")
    out_path = os.path.normpath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out_path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
