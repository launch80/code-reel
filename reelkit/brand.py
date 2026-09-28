"""brand — pull a site's real palette, fonts and copy into brand.json (and a style override).

  reel.py brand <proj> <url-or-file>

Reads the HTML and every linked stylesheet (same host), collects CSS custom
properties, hex colors by frequency, font-family names, <title>, meta
description and headings. Writes <proj>/brand.json and prints a suggested
"style" override (palette + closest bundled fonts). If the network is blocked,
save the page yourself and pass the file path — or fill brand.json by hand from
the site's CSS: the rest of the pipeline only reads brand.json.
"""
import collections
import json
import os
import re
import urllib.parse
import urllib.request

BUNDLED = {"sans": ["DM Sans", "Inter", "Manrope", "Archivo", "IBM Plex Sans", "Space Grotesk"],
           "mono": ["DM Mono", "IBM Plex Mono", "JetBrains Mono"],
           "serif": ["Instrument Serif", "Fraunces"],
           "disp": ["Russo One", "Archivo Black", "Fraunces", "IBM Plex Sans Condensed", "VT323", "Manrope"]}
GENERIC = {"sans-serif", "serif", "monospace", "system-ui", "inherit", "initial", "cursive", "ui-monospace", "ui-sans-serif", "-apple-system", "blinkmacsystemfont"}


def _get(src, base=None):
    if os.path.exists(src):
        return open(src, encoding="utf-8", errors="replace").read(), "file://" + os.path.abspath(src)
    url = urllib.parse.urljoin(base, src) if base else src
    if url.startswith("file://"):
        p = url[7:]
        return open(p, encoding="utf-8", errors="replace").read(), url
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 code-reel brand scan"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _sat(h):
    c = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return (max(c) - min(c)) / 255


def _norm(h):
    h = h.lower()
    if len(h) == 4:
        h = "#" + "".join(ch * 2 for ch in h[1:])
    return h[:7]


def scan(src):
    html, url = _get(src)
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    for href in re.findall(r"<link[^>]+rel=[\"']?stylesheet[^>]*>", html, re.I):
        m = re.search(r"href=[\"']([^\"']+)", href)
        if m:
            try:
                css += "\n" + _get(m.group(1), url)[0]
            except Exception as e:           # a blocked stylesheet should not kill the scan
                css += "\n/* could not load %s: %s */" % (m.group(1), e)
    text = css + html
    colors = collections.Counter(_norm(h) for h in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", text))
    props = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", css))
    fonts = collections.Counter()
    for fam in re.findall(r"font-family\s*:\s*([^;}\n]+)", text):
        for f in fam.split(","):
            f = f.strip().strip("'\"")
            if f and f.lower() not in GENERIC and not f.startswith("var("):
                fonts[f] += 1
    gf = re.findall(r"fonts\.googleapis\.com/css2?\?family=([^\"'&]+)", html)
    for g in gf:
        for f in g.split("&family="):
            fonts[urllib.parse.unquote_plus(f.split(":")[0])] += 3
    title = (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1].strip()
    desc = (re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)", html, re.I) or [None, ""])[1]
    heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S | re.I)][:8]
    return {"_css": css, "source": url, "title": title, "description": desc, "headings": heads,
            "css_vars": props, "colors": colors.most_common(16), "fonts": fonts.most_common(10)}


def _var(props, *pats):
    hits = [(k, v) for k, v in props.items() if any(re.search(pt, k.lower()) for pt in pats)]
    return _norm(sorted(hits, key=lambda kv: len(kv[0]))[0][1]) if hits else None


def suggest(b):
    cols = [c for c, _ in b["colors"]]
    if not cols:
        return {}
    props, css = b["css_vars"], b.get("_css", "")
    body_bg = re.search(r"(?:body|html|:root)[^{]*\{[^}]*background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})", css)
    body_fg = re.search(r"(?:body|html)[^{]*\{[^}]*[^-]color\s*:\s*(#[0-9a-fA-F]{3,6})", css)
    bg = _var(props, r"^--(bg|background)") or (body_bg and _norm(body_bg.group(1))) or min(cols[:6], key=_lum)
    dark = _lum(bg) < 0.5
    text = _var(props, r"^--(text|fg|foreground|ink)$") or (body_fg and _norm(body_fg.group(1))) or max(cols, key=lambda c: abs(_lum(c) - _lum(bg)))
    accent = _var(props, r"^--(accent|primary|brand)$", r"^--(accent|primary|brand)") or max(cols[:12], key=lambda c: _sat(c) * (1 if abs(_lum(c) - _lum(bg)) > 0.2 else 0.2))
    sat = [c for c in cols if c not in (bg, accent, text) and _sat(c) > 0.25]
    hot = _var(props, r"secondary|highlight|warn|rust|hot") or (sat[0] if sat else accent)
    mute = _var(props, r"mute|subtle|secondary-text") or sorted(cols, key=lambda c: abs(_lum(c) - (_lum(bg) + _lum(text)) / 2))[0]
    surf = _var(props, r"surface|canvas|card|panel|elev") or sorted([c for c in cols if c != bg], key=lambda c: abs(_lum(c) - _lum(bg)))[0]
    line = _var(props, r"border|line|rule|divider") or sorted([c for c in cols if c not in (bg, surf)], key=lambda c: abs(_lum(c) - _lum(bg) - (0.1 if dark else -0.1)))[0]
    pal = {"bg": bg, "surf": surf, "line": line, "text": text, "cream": text, "mute": mute, "accent": accent, "hot": hot}
    fonts = {}
    names = [f for f, _ in b["fonts"]]
    for role, opts in BUNDLED.items():
        hit = next((o for n in names for o in opts if o.lower() == n.lower()), None)
        if hit:
            fonts[role] = hit
    return {"palette": pal, "fonts": fonts, "fonts_seen": names[:6],
            "note": "fonts not bundled are listed in fonts_seen — pick the closest bundled role or add the woff2 to engine/fonts"}


def run(proj, src):
    b = scan(src)
    b["suggested_style"] = suggest(b)
    b.pop("_css", None)
    json.dump(b, open(os.path.join(proj, "brand.json"), "w"), indent=1)
    return b
