"""compile — the single source of truth between a project and the renderer.

project/
  timeline.json      scenes, durations, params, style choice, seed
  claims.json        every number/claim shown on screen: value + source   (optional but enforced in --final)
  scenes/*.js        scene code written for THIS video (defineScene + /* @meta */)
  assets/            images/SVGs referenced by timeline "assets"

compile() expands the style pack, resolves claim references, validates every
scene against its contract, derives ALL timed events (cuts, transitions,
impacts, typing, ticks, bell) once, and writes .reel/ :
  timeline.resolved.json   read by audio / qc / novelty (Python)
  timeline.js              the same object for the browser (window.__TIMELINE__)
  index.html               player + preview (open it directly, no server needed)
  engine/                  pinned copy of the engine this build used
"""
import hashlib
import json
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ENGINE = os.path.join(SKILL, "engine")

TRANSITIONS = {"cut": (True, None), "glitch": (True, "glitch"), "flash": (True, "flash"),
               "dissolve": (False, None), "push": (False, None), "whip": (False, None), "wipe": (False, None),
               "zoom": (False, None), "iris": (False, None), "shutter": (False, None), "slide": (False, None)}
DIRS = ["left", "right", "up", "down"]
LAYOUT_KEYS = {"fmt", "viz", "seed", "dir", "align", "type", "font", "shape", "icon", "color", "col", "style",
               "anchor", "ease", "mode", "layout", "kind", "side", "variant", "pose", "id", "ref", "src", "asset"}
CLAIM_REF = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*(?::\s*([a-z0-9]+))?\s*\}\}")
META_RE = re.compile(r"/\*\s*@meta\s*(\{.*?\})\s*\*/", re.S)
DEFINE_RE = re.compile(r"defineScene\(\s*['\"]([a-z][a-z0-9_]*)['\"]")


class CompileError(Exception):
    pass


def _load(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise CompileError("missing file: %s" % path)
    try:
        return json.load(open(path))
    except json.JSONDecodeError as e:
        raise CompileError("%s is not valid JSON: %s" % (path, e))


def styles():
    return {k: v for k, v in _load(os.path.join(ENGINE, "styles.json")).items() if not k.startswith("_")}


def blueprint_meta():
    return {k: v for k, v in _load(os.path.join(ENGINE, "scenes.json")).items() if not k.startswith("_")}


def rng(seed):
    """Same LCG as the engine's rng(), so Python and JS agree when they need to."""
    s = [(int(seed) & 0xFFFFFFFF) or 1]

    def f():
        s[0] = (s[0] * 1664525 + 1013904223) & 0xFFFFFFFF
        return s[0] / 4294967296
    return f


# ------------------------------------------------------------------ custom scenes
def scene_files(proj):
    """All project JS in load order: scenes/_*.js (shared helpers) first, then scenes/*.js, then legacy files."""
    files = []
    sd = os.path.join(proj, "scenes")
    if os.path.isdir(sd):
        js = [f for f in os.listdir(sd) if f.endswith(".js")]
        files += [os.path.join(sd, f) for f in sorted(js, key=lambda f: (not f.startswith("_"), f))]
    for legacy in ("scene_custom.js", "scenes_custom.js"):
        if os.path.exists(os.path.join(proj, legacy)):
            files.append(os.path.join(proj, legacy))
    return files


def custom_scenes(proj):
    """{name: {file, meta}} for every defineScene in project scenes/*.js (+ legacy scene_custom.js)."""
    out = {}
    files = []
    sd = os.path.join(proj, "scenes")
    if os.path.isdir(sd):
        files += sorted(os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".js"))
    for legacy in ("scene_custom.js", "scenes_custom.js"):
        if os.path.exists(os.path.join(proj, legacy)):
            files.append(os.path.join(proj, legacy))
    for f in files:
        src = open(f).read()
        metas = {}
        for m in META_RE.finditer(src):
            try:
                mj = json.loads(m.group(1))
                if mj.get("name"):
                    metas[mj["name"]] = mj
            except json.JSONDecodeError as e:
                raise CompileError("%s: bad @meta JSON: %s" % (os.path.basename(f), e))
        for name in DEFINE_RE.findall(src):
            out[name] = {"file": f, "meta": metas.get(name, {})}
    return out


def node_check(path):
    try:
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return None if r.returncode == 0 else (r.stderr or r.stdout).strip()[:600]


# ------------------------------------------------------------------ style
def expand_style(tl, errs):
    packs = styles()
    st = tl.get("style", "signal")
    over = {}
    if isinstance(st, dict):
        over = dict(st)
        st = over.pop("pack", "signal")
    if st not in packs:
        errs.append("style pack '%s' does not exist (have: %s)" % (st, ", ".join(sorted(packs))))
        st = "signal"
    out = json.loads(json.dumps(packs[st]))
    out["pack"] = st
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    theme = tl.get("theme") or {}          # legacy v1 "theme" -> palette overrides
    for k, v in theme.items():
        out["palette"][k] = v
    for k in ("bg", "surf", "line", "text", "mute", "accent", "hot", "cream"):
        v = out["palette"].get(k)
        if not (isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v)):
            errs.append("palette.%s must be a #rrggbb hex (got %r)" % (k, v))
    return out


# ------------------------------------------------------------------ claims
def resolve_claims(obj, claims, uses, path, errs):
    """Replace "@id" values and {{id}} / {{id:fmt}} inside strings. Returns new obj."""
    if isinstance(obj, dict):
        return {k: resolve_claims(v, claims, uses, path + [k], errs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_claims(v, claims, uses, path + [i], errs) for i, v in enumerate(obj)]
    if isinstance(obj, str):
        if obj.startswith("@") and re.fullmatch(r"@[A-Za-z0-9_.\-]+", obj):
            cid = obj[1:]
            if cid not in claims:
                errs.append("%s: unknown claim '%s' (add it to claims.json)" % (_p(path), cid))
                return obj
            uses.append({"path": _p(path), "claim": cid, "kind": "value"})
            return claims[cid]["value"]

        def sub(m):
            cid, f = m.group(1), m.group(2)
            if cid not in claims:
                errs.append("%s: unknown claim '%s' in text (add it to claims.json)" % (_p(path), cid))
                return m.group(0)
            out = claim_text(claims[cid], f)
            uses.append({"path": _p(path), "claim": cid, "kind": "text", "text": out})
            return out
        return CLAIM_REF.sub(sub, obj)
    return obj


def claim_text(c, f=None):
    if f is None and c.get("display"):
        return str(c["display"])
    v = c.get("value")
    if isinstance(v, (int, float)):
        if f == "comma" or (f is None and abs(v) >= 1000):
            return "{:,}".format(round(v)) if float(v).is_integer() or f == "comma" else "{:,}".format(v)
        if f == "x":
            return ("%.1f" % v) + "×"
        if f == "k":
            return "%dK" % round(v)
        if f == "d":
            return "$" + "{:,}".format(round(v))
        if f == "pct":
            return "%d%%" % round(v)
        if f == "int":
            return str(int(round(v)))
        return ("%g" % v)
    return str(v)


def _p(path):
    return ".".join(str(x) for x in path)


def onscreen_strings(p, keys=None, path=()):
    """Yield (path, string) for every visible string in params (skips layout keys/colors)."""
    if isinstance(p, dict):
        for k, v in p.items():
            if k in LAYOUT_KEYS or k.startswith("_"):
                continue
            if keys is not None and not path and k not in keys:
                continue
            yield from onscreen_strings(v, None, path + (k,))
    elif isinstance(p, list):
        for i, v in enumerate(p):
            yield from onscreen_strings(v, None, path + (i,))
    elif isinstance(p, str):
        s = p.strip()
        if s and not re.fullmatch(r"#[0-9a-fA-F]{3,8}|ACCENT|rgba?\(.*\)", s):
            yield path, s


def numeric_data(p, path=()):
    """Yield (path, number) for numbers that are DATA shown on screen: counter targets, series."""
    if isinstance(p, dict):
        for k, v in p.items():
            if k in ("to", "from", "value", "grow", "values", "series", "data") and not k.startswith("_"):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if not (k == "from" and v == 0):
                        yield path + (k,), v
                elif isinstance(v, list):
                    for i, x in enumerate(v):
                        if isinstance(x, (int, float)) and not isinstance(x, bool) and x != 0:
                            yield path + (k, i), x
            else:
                yield from numeric_data(v, path + (k,))
    elif isinstance(p, list):
        for i, v in enumerate(p):
            yield from numeric_data(v, path + (i,))


# ------------------------------------------------------------------ time expressions
def tval(expr, d, p, default=None):
    """number = seconds; 'Xd' = fraction of d; 'key[+-N]' = param key (seconds) plus offset."""
    if expr is None:
        return default
    if isinstance(expr, (int, float)):
        return float(expr)
    s = str(expr).strip()
    m = re.fullmatch(r"(-?[\d.]+)d", s)
    if m:
        return float(m.group(1)) * d
    m = re.fullmatch(r"([a-zA-Z_]+)\s*([+-]\s*[\d.]+)?", s)
    if m:
        base = p.get(m.group(1))
        if base is None:
            return default
        return float(base) + (float(m.group(2).replace(" ", "")) if m.group(2) else 0.0)
    return float(s)


# ------------------------------------------------------------------ main
def compile_project(proj, final=False, write=True, engine_sync=True):
    proj = os.path.abspath(proj)
    errs, warns = [], []
    tl = _load(os.path.join(proj, "timeline.json"))
    claims = _load(os.path.join(proj, "claims.json"), {})
    claims = {k: v for k, v in claims.items() if not k.startswith("_")}
    for cid, c in claims.items():
        if "value" not in c:
            errs.append("claims.json: '%s' has no value" % cid)
        if final and not (c.get("source") or c.get("url")):
            errs.append("claims.json: '%s' has no source/url (required for --final)" % cid)
        elif not (c.get("source") or c.get("url")):
            warns.append("claims.json: '%s' has no source yet" % cid)
        if str(c.get("status", "")).lower() in ("placeholder", "illustrative", "todo"):
            (errs if final else warns).append("claims.json: '%s' is marked %s — replace it with a measured value before --final" % (cid, c["status"]))

    style = expand_style(tl, errs)
    W, H = int(tl.get("w", 1920)), int(tl.get("h", 1080))
    fps = int(tl.get("fps", 60))
    bpm = float(tl.get("bpm", style.get("bpm", 120)))
    beat = 60.0 / bpm
    if abs(beat * fps - round(beat * fps)) > 1e-6:
        errs.append("bpm %g gives a beat of %.4f frames at %dfps — pick a bpm that divides %d (e.g. 90, 100, 120, 144, 150)" % (bpm, beat * fps, fps, 60 * fps))
    seed = tl.get("seed")
    if seed is None:
        warns.append("no 'seed' in timeline.json — using 1 (set one: every unpinned creative choice derives from it)")
        seed = 1
    policy = {"beatGrid": True, "strictClaims": final, "minCustomShare": 0.5 if final else 0.0}
    policy.update(tl.get("policy") or {})
    if final:
        policy["strictClaims"] = True

    bp = blueprint_meta()
    custom = custom_scenes(proj)
    for name, c in custom.items():
        if name in bp:
            errs.append("%s defines '%s', which is a built-in blueprint name — rename it" % (os.path.basename(c["file"]), name))
        bad = node_check(c["file"])
        if bad:
            errs.append("%s: JavaScript syntax error:\n%s" % (os.path.basename(c["file"]), bad))
    for f in scene_files(proj):
        if f not in {c["file"] for c in custom.values()}:
            bad = node_check(f)
            if bad:
                errs.append("%s: JavaScript syntax error:\n%s" % (os.path.basename(f), bad))
    STR_RE = re.compile(r"'([^'\\\n]{2,80})'|\"([^\"\\\n]{2,80})\"")
    for f in scene_files(proj):
        for ln, line_ in enumerate(open(f), 1):
            if line_.strip().startswith("//"):
                continue
            for m in STR_RE.finditer(line_):
                sv = m.group(1) or m.group(2)
                if re.search(r"\d", sv) and re.search(r"[A-Za-z$%€£]", sv) and (" " in sv.strip() or re.search(r"[$%€£]", sv)) and not re.search(r"\d+(px|ms|deg)|rgba?\(|#[0-9a-f]{3}|@meta|\$\{", sv):
                    (errs if final else warns).append("%s:%d hard-codes on-screen text with a number: %r — pass it in as a param so compile can check it" % (os.path.basename(f), ln, sv))
    metas = dict(bp)
    for name, c in custom.items():
        metas.setdefault(name, c["meta"])

    literals = set(str(x) for x in tl.get("literals", []))
    hud = tl.get("hud") or {}
    if isinstance(hud, dict):
        for k in ("brand", "brand2"):
            if hud.get(k):
                literals.add(str(hud[k]))
        if hud.get("brand") and hud.get("brand2"):
            literals.add(str(hud["brand"]) + str(hud["brand2"]))
    for k in (tl.get("sources") or {}):          # legacy v1 sources map: exact strings that are verified
        literals.add(str(k))

    scenes_in = tl.get("timeline") or []
    if not scenes_in:
        errs.append("timeline is empty")
    uses = []
    scenes = []
    t = 0.0
    for i, s in enumerate(scenes_in):
        typ = s.get("scene")
        tag = "scene[%d] %s" % (i, typ)
        d = s.get("dur")
        if d is None and isinstance(s.get("beats"), (int, float)):
            d = s["beats"] * beat          # durations in beats survive a bpm/style change
        if typ not in metas:
            errs.append("%s: unknown scene type — not a blueprint (%s) and not defined in scenes/*.js" % (tag, ", ".join(sorted(bp))))
        if not isinstance(d, (int, float)) or d <= 0:
            errs.append("%s: missing/invalid dur" % tag)
            d = 1.0
        d = float(d)
        p = resolve_claims(s.get("p", {}), claims, uses, ["timeline", i, "p"], errs)
        for u in uses:
            u.setdefault("scene", i)
        meta = metas.get(typ, {})
        for k in meta.get("required", []):
            if k not in p:
                errs.append("%s: missing required param p.%s" % (tag, k))
        if policy["beatGrid"] and t > 0 and abs(t / beat - round(t / beat)) > 1e-4:
            errs.append("%s: starts at %.3fs — off the %.3fs beat grid (bpm %g)" % (tag, t, beat, bpm))
        if abs(t * fps - round(t * fps)) > 1e-3:
            errs.append("%s: starts at %.4fs — not a whole frame at %dfps" % (tag, t, fps))
        for sl in s.get("slams", []) or []:
            if not (0 <= float(sl) < d):
                errs.append("%s: slam %s outside [0, dur)" % (tag, sl))
        look = s.get("look") or {}
        scenes.append({"i": i, "scene": typ, "name": (s.get("name") or typ or "?").upper(), "t0": round(t, 6),
                       "t1": round(t + d, 6), "dur": d, "p": p, "look": look, "slams": s.get("slams") or [],
                       "transition_in": s.get("transition"), "custom": typ in custom and typ not in bp})
        # per-type sanity (blueprints)
        if typ == "kinetic":
            for w in p.get("words", []):
                if not (isinstance(w, list) and len(w) >= 2 and isinstance(w[1], (int, float))):
                    errs.append("%s: word entry must be [text, offset, ...]" % tag)
                elif not (0 <= w[1] < d):
                    errs.append("%s: word '%s' offset %s outside scene" % (tag, w[0], w[1]))
        if typ == "chart" and p.get("months") and len(p["months"]) != len(p.get("grow", [])):
            errs.append("%s: months (%d) != grow (%d)" % (tag, len(p["months"]), len(p.get("grow", []))))
        if typ in ("chart",) and p.get("impact") is not None and not (0 <= float(p["impact"]) < d):
            errs.append("%s: impact %s outside scene" % (tag, p["impact"]))
        if typ in ("cards", "counter"):
            for c in ([p] if typ == "counter" else p.get("cards", [])):
                if "big" in c and not (isinstance(c["big"], dict) and "to" in c["big"]):
                    errs.append("%s: big must be {from,to,fmt}" % tag)
        t += d
    dur = round(t, 6)
    if abs(dur * fps - round(dur * fps)) > 1e-3:
        errs.append("total duration %.4fs is not a whole number of frames" % dur)

    # ---- claims policy: every on-screen number must come from claims.json (or be a declared literal)
    unsourced = []
    for s in scenes:
        keys = metas.get(s["scene"], {}).get("text")
        claim_strs = [u["text"] for u in uses if u.get("scene") == s["i"] and "text" in u]
        for path, st in onscreen_strings(s["p"], keys):
            rest = st
            for cs in sorted(claim_strs, key=len, reverse=True):
                rest = rest.replace(cs, "")
            for lit in sorted(literals, key=len, reverse=True):
                rest = rest.replace(lit, "")
            if re.search(r"\d", rest):
                unsourced.append("%s p.%s: %r" % (s["name"], _p(path), st))
        used_paths = {u["path"] for u in uses if u["kind"] == "value"}
        for path, v in numeric_data(s["p"]):
            full = "timeline.%d.p.%s" % (s["i"], _p(path))
            if not any(full == up or full.startswith(up + ".") for up in used_paths) and str(v) not in literals:
                unsourced.append("%s p.%s = %s" % (s["name"], _p(path), v))
    for u in unsourced:
        (errs if policy["strictClaims"] else warns).append("unsourced number on screen — %s (use a claim: \"@id\" or {{id}}; or list it in \"literals\")" % u)

    # ---- transitions + events (THE event derivation; JS and audio both read this)
    r = rng(seed)
    pool = style.get("transitions") or ["cut"]
    cuts, transitions = [], []
    for k in range(1, len(scenes)):
        s, prev = scenes[k], scenes[k - 1]
        c = s["t0"]
        cuts.append(c)
        spec = s["transition_in"]
        pick = pool[int(r() * len(pool)) % len(pool)]
        for _ in range(4):
            if not transitions or pick != transitions[-1]["type"] or len(set(pool)) == 1:
                break
            pick = pool[int(r() * len(pool)) % len(pool)]
        if spec is None:
            spec = {"type": pick}
        elif isinstance(spec, str):
            spec = {"type": spec}
        typ = spec.get("type", pick)
        if typ not in TRANSITIONS:
            errs.append("scene[%d]: unknown transition '%s' (have: %s)" % (k, typ, ", ".join(TRANSITIONS)))
            typ = "cut"
        self_, fx = TRANSITIONS[typ]
        tdur = 0.0 if self_ else float(spec.get("dur", style.get("transitionDur", 0.5)))
        if not self_ and tdur / 2 > 0.45 * min(prev["dur"], s["dur"]):
            errs.append("scene[%d]: transition %s dur %.2fs too long for the adjacent scenes (max %.2fs)" %
                        (k, typ, tdur, 0.9 * min(prev["dur"], s["dur"])))
        opts = {kk: vv for kk, vv in spec.items() if kk not in ("type", "dur")}
        if typ in ("push", "whip", "wipe", "slide") and "dir" not in opts:
            opts["dir"] = DIRS[int(r() * 4) % 4] if typ != "wipe" else ("right" if r() < 0.5 else "left")
        transitions.append({"t": c, "type": typ, "dur": tdur, "self": self_, "fx": fx, "opts": opts,
                            "from": prev["name"], "to": s["name"]})

    slams, typing, ticks = [], [], []
    for s in scenes:
        meta = metas.get(s["scene"], {})
        d, p, t0 = s["dur"], s["p"], s["t0"]
        for sl in s["slams"]:
            slams.append({"t": round(t0 + float(sl), 6), "scene": s["name"], "cause": "slam"})
        for rule in meta.get("slams", []):
            if isinstance(rule, str):
                rule = {"key": rule}
            if "list" in rule and "key_at" in rule:
                for w in p.get(rule["list"], []) or []:
                    if isinstance(w, dict) and w.get(rule["key_at"]) is not None:
                        slams.append({"t": round(t0 + float(w[rule["key_at"]]), 6), "scene": s["name"], "cause": "click"})
            elif "list" in rule:
                for w in p.get(rule["list"], []) or []:
                    if isinstance(w, list) and len(w) > rule["index"]:
                        slams.append({"t": round(t0 + float(w[rule["index"]]), 6), "scene": s["name"], "cause": "'%s' lands" % w[0]})
            else:
                tv = tval(p.get(rule["key"], rule.get("default")), d, p)
                if tv is not None:
                    slams.append({"t": round(t0 + tv, 6), "scene": s["name"], "cause": rule["key"]})
        for rule in meta.get("typing", []):
            txt = p.get(rule["key"])
            if txt:
                a, b = tval(rule["a"], d, p), tval(rule["b"], d, p)
                n = sum(len(str(x)) for x in txt) if isinstance(txt, list) else len(str(txt))
                typing.append({"t": round(t0 + a, 6), "dur": round(b - a, 6), "n": min(n, int((b - a) * 24)), "scene": s["name"]})
        for rule in meta.get("ticks", []):
            a, b = tval(rule["a"], d, p), tval(rule["b"], d, p, default=0.6 * d)
            if b is None:
                b = tval(meta.get("slams", [{}])[0].get("default"), d, p, 0.6 * d) - 0.1
            if b > a:
                ticks.append({"a": round(t0 + a, 6), "b": round(t0 + b, 6), "scene": s["name"]})
    bell = None
    if scenes and "bell" in metas.get(scenes[-1]["scene"], {}):
        bell = round(scenes[-1]["t0"] + float(metas[scenes[-1]["scene"]]["bell"]), 6)
    impacts = sorted({x["t"] for x in slams} | {tr["t"] for tr in transitions if tr["self"] and tr["type"] != "cut"})
    for sl in slams:
        if not (0 <= sl["t"] < dur):
            errs.append("slam at %.3fs outside the reel" % sl["t"])

    # ---- uniqueness policy (final): custom scenes must carry the reel
    custom_time = sum(s["dur"] for s in scenes if s["custom"])
    share = custom_time / dur if dur else 0
    if share + 1e-9 < float(policy.get("minCustomShare", 0)):
        errs.append("only %.0f%% of the runtime is scene code written for this video (policy minCustomShare %.0f%%) — "
                    "write more scenes in scenes/*.js; blueprints are references, not the reel" % (share * 100, policy["minCustomShare"] * 100))
    counts = {}
    for s in scenes:
        counts[s["scene"]] = counts.get(s["scene"], 0) + 1
    for k, n in counts.items():
        if n > 2 and k in bp:
            (errs if final else warns).append("blueprint '%s' used %d times — repeated layouts read as a template" % (k, n))

    # ---- assets
    assets = {}
    for k, v in (tl.get("assets") or {}).items():
        ap = os.path.join(proj, v)
        if not os.path.exists(ap):
            errs.append("asset '%s' not found: %s" % (k, v))
        assets[k] = "../" + v.replace(os.sep, "/")

    audio = dict(tl.get("audio") or {})
    if audio.get("track") and not os.path.exists(os.path.join(proj, audio["track"])):
        errs.append("audio track not found: %s" % audio["track"])
    if audio.get("preset"):
        from . import audio as _au
        if audio["preset"] not in _au.PRESETS:
            errs.append("audio preset '%s' unknown (have: %s)" % (audio["preset"], ", ".join(_au.PRESETS)))

    engine_hash = _hash_dir(ENGINE)
    out = {
        "version": 2, "name": tl.get("name", ""), "w": W, "h": H, "fps": fps, "bpm": bpm, "seed": seed,
        "duration": dur, "style": style, "hud": tl.get("hud", {}), "assets": assets, "policy": policy, "audio": audio,
        "scenes": [{k: v for k, v in s.items() if k != "transition_in"} for s in scenes],
        "events": {"cuts": cuts, "impacts": impacts, "transitions": transitions, "slams": sorted(slams, key=lambda x: x["t"]),
                   "typing": typing, "ticks": ticks, "bell": bell,
                   "beats": _beats(bpm, cuts, dur)},
        "claims": claims, "claim_uses": uses, "custom_share": round(share, 4),
        "scripts": ["../" + os.path.relpath(f, proj).replace(os.sep, "/") for f in scene_files(proj)],
        "engine": engine_hash, "warnings": warns, "errors": errs,
    }
    if write:
        rd = os.path.join(proj, ".reel")
        os.makedirs(rd, exist_ok=True)
        json.dump(out, open(os.path.join(rd, "timeline.resolved.json"), "w"), indent=1)
        open(os.path.join(rd, "timeline.js"), "w").write("window.__TIMELINE__=" + json.dumps(out) + ";\n")
        if engine_sync:
            sync_engine(rd, engine_hash)
        write_index(rd, out)
    return out


def _beats(bpm, cuts, dur):
    beat = 60.0 / bpm
    if not cuts:
        return []
    n0 = int(round(cuts[0] / beat))
    n1 = int((cuts[-1] + 1e-6) / beat)
    return [round(k * beat, 6) for k in range(n0, n1 + 1)]


def _hash_dir(d):
    h = hashlib.sha256()
    for root, _, files in sorted(os.walk(d)):
        for f in sorted(files):
            if f.endswith((".js", ".json", ".css", ".html")):
                h.update(f.encode())
                h.update(open(os.path.join(root, f), "rb").read())
    return h.hexdigest()[:16]


def sync_engine(rd, engine_hash):
    dst = os.path.join(rd, "engine")
    stamp = os.path.join(dst, ".hash")
    if os.path.exists(stamp) and open(stamp).read().strip() == engine_hash:
        return
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(ENGINE, dst)
    open(stamp, "w").write(engine_hash)


def write_index(rd, tl):
    scripts = "\n".join('<script src="%s"></script>' % s for s in tl["scripts"])
    bg = tl["style"]["palette"]["bg"]
    html = """<!doctype html>
<html><head><meta charset="utf-8"><title>%s — code-reel</title>
<link rel="stylesheet" href="engine/fonts/fonts.css">
<style>
html,body{margin:0;background:%s}canvas{display:block}
body.preview{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;gap:12px;font:14px monospace;color:#9b9b9b;background:#111}
body.preview canvas{width:min(96vw,calc((100vh - 90px)*%f));height:auto;border:1px solid #333}
#ui{display:flex;gap:12px;align-items:center;width:min(96vw,calc((100vh - 90px)*%f))}
#ui button{background:var(--accent,#e85d04);color:#000;border:0;padding:6px 14px;font:inherit;cursor:pointer;border-radius:4px}
#ui input[type=range]{flex:1}
#err{position:fixed;inset:0;display:none;place-items:center;color:#ff8a3d;background:rgba(0,0,0,.85);font:500 18px monospace;padding:40px;white-space:pre-wrap;text-align:left}
</style></head>
<body><canvas id="c" width="%d" height="%d"></canvas><div id="err"></div>
<script src="engine/core.js"></script>
<script src="engine/looks.js"></script>
<script src="engine/scenes.js"></script>
<script src="engine/illustrate.js"></script>
<script src="engine/scenes_plus.js"></script>
%s
<script src="timeline.js"></script>
<script src="engine/player.js"></script>
</body></html>
""" % (tl["name"], bg, tl["w"] / tl["h"], tl["w"] / tl["h"], tl["w"], tl["h"], scripts)
    open(os.path.join(rd, "index.html"), "w").write(html)


def report(out):
    lines = []
    for w in out["warnings"]:
        lines.append("WARN: " + w)
    for e in out["errors"]:
        lines.append("ERROR: " + e)
    lines.append("%s: %d scenes, %.2fs, %dfps, %gbpm, style=%s, seed=%s, custom=%.0f%%, transitions=%s" % (
        "FAILED" if out["errors"] else "OK", len(out["scenes"]), out["duration"], out["fps"], out["bpm"],
        out["style"]["pack"], out["seed"], out["custom_share"] * 100,
        ",".join(t["type"] for t in out["events"]["transitions"]) or "-"))
    return "\n".join(lines)
