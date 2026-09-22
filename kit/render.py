"""All India CME brand renderer, 1080x1080 single squares.

Rebuilt 22 Sep 2026 after the sandbox wipe. Measured against published posts 07 (navy),
09 (ivory) and 25 (gold): Bricolage Grotesque 800 headlines, Instrument Sans body
(30 px, 44 px leading), 80 px left margin. The lockup is taken from the published
launch images so it is pixel-identical to the brand artwork.

    render(post, path) -> {"overflow": bool, "lines": int, "size": float}
post needs: theme (navy|ivory|gold), eyebrow, headline, sub.
"""
import io, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
RAW = "https://raw.githubusercontent.com/abhigawande-star/allindiacme-social/main/"
GF = "https://github.com/google/fonts/raw/main/ofl/"
FONTS = {
    "brico": GF + "bricolagegrotesque/BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf",
    "instr": GF + "instrumentsans/InstrumentSans%5Bwdth,wght%5D.ttf",
}
NAVY, GOLD, IVORY, INK = (18, 43, 74), (201, 163, 101), (251, 248, 241), (11, 23, 39)
THEMES = {
    "navy":  dict(bg=NAVY, eyebrow=(214, 184, 134), head=(252, 251, 247), rule=GOLD,
                  body=(207, 217, 227), tag=(212, 182, 133), ven=(102, 123, 156), centre=540),
    "ivory": dict(bg=IVORY, eyebrow=(134, 127, 111), head=INK, rule=GOLD,
                  body=(68, 64, 62), tag=(154, 119, 66), ven=(163, 154, 141), centre=545),
    "gold":  dict(bg=GOLD, eyebrow=(16, 31, 54), head=INK, rule=NAVY,
                  body=(16, 31, 54), tag=(24, 46, 76), ven=(85, 77, 64), centre=565),
}
# lockup source: (launch image, crop box) - pasted back at the same box
LOCKUP = {"navy": ("07", (60, 70, 330, 160)), "ivory": ("09", (60, 88, 330, 170)),
          "gold": ("25", (0, 0, 1080, 120))}
X, MAXW, BODYW = 80, 900, 800


def _get(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def _font(key, size, axes):
    f = ImageFont.truetype(_get(FONTS[key], os.path.join(FONT_DIR, key + ".ttf")), size)
    f.set_variation_by_axes(axes)
    return f


def _lockup(theme):
    n, box = LOCKUP[theme]
    p = _get(RAW + "AllIndiaCME_awareness_%s.jpg" % n, os.path.join(FONT_DIR, "launch_%s.jpg" % n))
    return Image.open(p).convert("RGB").crop(box), box


def _wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def _balanced(text, f, maxw):
    """Greedy wrap, then narrow the measure while the line count holds, for even lines."""
    lines = _wrap(text, f, maxw)
    w = maxw
    while w > 400:
        t = _wrap(text, f, w - 20)
        if len(t) != len(lines):
            break
        lines, w = t, w - 20
    return lines


def _tracked(d, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + track


def render(post, path):
    th = THEMES[post["theme"]]
    im = Image.new("RGB", (1080, 1080), th["bg"])
    d = ImageDraw.Draw(im)
    if post["theme"] == "navy":
        d.rectangle((0, 0, 13, 1079), fill=GOLD)
    if post["theme"] == "ivory":
        d.rectangle((0, 0, 1079, 11), fill=NAVY)
    lk, box = _lockup(post["theme"])
    im.paste(lk, box[:2])

    # headline: largest size (78 -> 52) that fits in <= 3 lines
    overflow = False
    for size in [78, 74, 70, 66, 62, 58, 55, 52]:
        fh = _font("brico", size, [96, 800, 100])
        hl = _balanced(post["headline"], fh, MAXW)
        if len(hl) <= 3 and max(fh.getlength(l) for l in hl) <= MAXW:
            break
    else:
        overflow = True
    hpitch = round(size * 1.06)
    fb = _font("instr", 30, [100, 400])
    body = _wrap(post["sub"], fb, BODYW)
    if len(body) > 4:
        overflow = True
    fe = _font("instr", 23, [100, 600])

    eyebrow_h, gap1, gap2, gap3, rule_h = 22, 24, 42, 35, 6
    block = eyebrow_h + gap1 + hpitch * len(hl) + gap2 + rule_h + gap3 + 44 * len(body)
    y = th["centre"] - block // 2
    _tracked(d, (X, y), post["eyebrow"].upper(), fe, th["eyebrow"], 2.2)
    y += eyebrow_h + gap1
    for l in hl:
        d.text((X, y), l, font=fh, fill=th["head"]); y += hpitch
    y += gap2
    d.rectangle((X, y, X + 109, y + rule_h - 1), fill=th["rule"]); y += rule_h + gap3
    for l in body:
        d.text((X, y), l, font=fb, fill=th["body"]); y += 44
    if y > 900:
        overflow = True

    fy = 946 if post["theme"] == "gold" else 938
    d.text((X, fy), "Uniform Excellence in Clinical Practice",
           font=_font("instr", 23, [100, 600]), fill=th["tag"])
    d.text((X, fy + 34), "A venture of Covelis Health Tech LLP.",
           font=_font("instr", 19, [100, 400]), fill=th["ven"])
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path, "JPEG", quality=92, subsampling=0)
    return {"overflow": overflow, "lines": len(hl), "size": size}
