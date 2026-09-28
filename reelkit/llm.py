"""llm — one interface, four backends, identical prompts and gates.

  openai   any OpenAI-compatible server (vLLM, LM Studio, llama.cpp server, MLX, Ollama /v1)
  ollama   Ollama native /api/chat
  agent    the calling agent IS the model: the prompt is written to
           .reel/llm/<key>.prompt.md and the run stops (exit 10) until the agent
           writes .reel/llm/<key>.answer.<ext>; re-running the same command continues.
  mock     replays answers from a fixtures dir using the SAME <key>.answer.<ext> names.

Every backend records the exchange in .reel/llm/ with those names, so any real
run (local model or agent) can be replayed later as a test fixture:
    reel.py direct <proj> all --backend mock --fixtures <old-proj>/.reel/llm
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.request


class AwaitingAgent(Exception):
    def __init__(self, prompt_path, answer_path):
        self.prompt_path, self.answer_path = prompt_path, answer_path
        super().__init__("waiting for the agent: read %s and write %s, then re-run" % (prompt_path, answer_path))


class LLMError(Exception):
    pass


def _ext(kind):
    return {"json": "json", "js": "js", "md": "md"}.get(kind, "txt")


def strip_fences(text, kind):
    t = (text or "").strip()
    m = re.search(r"```(?:json|js|javascript)?\s*\n(.*?)\n```", t, re.S)
    if m:
        t = m.group(1).strip()
    if kind == "json":
        s = t.find("{")
        e = t.rfind("}")
        if s >= 0 and e > s:
            t = t[s:e + 1]
    return t


class LLM:
    def __init__(self, backend, proj, model=None, base_url=None, fixtures=None, seed=1, temperature=None):
        self.backend = backend
        self.proj = proj
        self.model = model
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.fixtures = fixtures
        self.seed = int(seed)
        self.temperature = temperature
        self.dir = os.path.join(proj, ".reel", "llm")
        os.makedirs(self.dir, exist_ok=True)
        if backend == "mock" and not (fixtures and os.path.isdir(fixtures)):
            raise LLMError("mock backend needs --fixtures <dir with *.answer.* files>")

    def ask(self, key, system, user, kind="json", temperature=0.4):
        """key: stable name for this exchange (e.g. 'treat-1', 'scene-orbit-2')."""
        key = re.sub(r"[^A-Za-z0-9_.\-]", "_", key)
        ppath = os.path.join(self.dir, key + ".prompt.md")
        apath = os.path.join(self.dir, key + ".answer." + _ext(kind))
        prompt = "<!-- system -->\n%s\n\n<!-- user -->\n%s\n" % (system, user)
        open(ppath, "w").write(prompt)
        temp = self.temperature if self.temperature is not None else temperature
        seed = (self.seed * 1000003 + int(hashlib.sha256(key.encode()).hexdigest()[:6], 16)) % (2 ** 31)
        if self.backend == "agent":
            if not os.path.exists(apath):
                open(os.path.join(self.dir, "WAITING"), "w").write("%s\n%s\n" % (ppath, apath))
                raise AwaitingAgent(ppath, apath)
            text = open(apath).read()
        elif self.backend == "mock":
            src = os.path.join(self.fixtures, key + ".answer." + _ext(kind))
            if not os.path.exists(src):
                raise LLMError("mock: no fixture for %s (looked for %s)" % (key, src))
            text = open(src).read()
            open(apath, "w").write(text)
        else:
            text = self._http(system, user, kind, temp, seed)
            open(apath, "w").write(text)
        w = os.path.join(self.dir, "WAITING")
        if os.path.exists(w):
            os.remove(w)
        json.dump({"key": key, "backend": self.backend, "model": self.model, "temperature": temp, "seed": seed,
                   "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16]},
                  open(os.path.join(self.dir, key + ".meta.json"), "w"), indent=1)
        out = strip_fences(text, kind)
        if kind == "json":
            try:
                return json.loads(out)
            except json.JSONDecodeError as e:
                raise LLMError("%s: answer is not valid JSON (%s) — see %s" % (key, e, apath))
        return out

    def _http(self, system, user, kind, temp, seed):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        if self.backend == "ollama":
            body = {"model": self.model, "messages": msgs, "stream": False, "options": {"temperature": temp, "seed": seed, "num_ctx": 32768}}
            if kind == "json":
                body["format"] = "json"
            out = self._post(self.base_url + "/api/chat", body)
            return out.get("message", {}).get("content", "")
        body = {"model": self.model, "messages": msgs, "temperature": temp, "seed": seed}
        if kind == "json":
            body["response_format"] = {"type": "json_object"}
        try:
            out = self._post(self.base_url + "/v1/chat/completions", body)
        except LLMError as e:
            if "response_format" in str(e):
                body.pop("response_format")
                out = self._post(self.base_url + "/v1/chat/completions", body)
            else:
                raise
        return out["choices"][0]["message"]["content"]

    def _post(self, url, body):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise LLMError("%s -> HTTP %d: %s" % (url, e.code, e.read().decode()[:400]))
        except urllib.error.URLError as e:
            raise LLMError("%s unreachable (%s) — is the model server running? (--base-url, --backend)" % (url, e.reason))
