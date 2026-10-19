#!/usr/bin/env python3
"""Local obligation extractor — Hacktoberfest Side Hustle demo build.
Runs an open-weight model via a LOCAL Ollama server (no cloud calls, no
per-document API cost) over a fictional sample agreement and emits
packet-shaped obligations with verbatim source quotes, then scores the
output against a human-authored ground truth.

Usage: python3 extract.py [model]   (default qwen2.5:0.5b)
Output: obligations-<model>.json + a scored summary on stdout.
"""
import json, re, sys, urllib.request, os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:0.5b"
OLLAMA = "http://127.0.0.1:11434/api/chat"

SYSTEM = (
    "You extract obligations from a contract. Reply with ONLY a JSON array. "
    "Each element: {\"obligated_party\": string, \"obligation\": string, "
    "\"amount\": string or null, \"deadline\": string or null, "
    "\"source_quote\": exact verbatim quote from the text}. "
    "Include every duty, payment, deadline, prohibition and termination "
    "right. Never invent facts that are not in the text."
)

def call_model(model, text):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "CONTRACT TEXT:\n" + text},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["message"]["content"]

def parse_json_array(raw):
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def norm(s):
    return re.sub(r"[^a-z0-9$.,]", " ", (s or "").lower())

def score(found, truth):
    results = []
    used = set()
    for t in truth:
        best, best_key = None, -1
        t_amt = re.sub(r"[^0-9]", "", t.get("amount") or "")
        t_keys = set(w for w in norm(t["obligation"]).split() if len(w) > 3)
        for i, f in enumerate(found):
            if i in used:
                continue
            f_amt = re.sub(r"[^0-9]", "", f.get("amount") or "")
            f_keys = set(w for w in norm(f.get("obligation", "")).split() if len(w) > 3)
            overlap = len(t_keys & f_keys)
            amt_bonus = 3 if (t_amt and t_amt == f_amt) else 0
            quote_ok = (f.get("source_quote") or "")[:40].lower() in \
                open(os.path.join(HERE, "sample-agreement.md")).read().lower() \
                if f.get("source_quote") else False
            key = overlap + amt_bonus + (2 if quote_ok else 0)
            if key > best_key:
                best, best_key = f, key
        matched = best is not None and best_key >= 4
        if matched:
            used.add(found.index(best))
        results.append((t["id"], matched, best))
    return results

def main():
    text = open(os.path.join(HERE, "sample-agreement.md")).read()
    truth = json.load(open(os.path.join(HERE, "ground-truth.json")))
    raw = call_model(MODEL, text)
    found = parse_json_array(raw)
    out = os.path.join(HERE, f"obligations-{MODEL.replace(':', '_')}.json")
    with open(out, "w") as fh:
        json.dump({"model": MODEL, "raw": raw, "parsed": found}, fh, indent=1)
    print(f"model={MODEL}  output -> {out}")
    if found is None:
        print("PARSE FAILED — model did not return a JSON array. Raw kept in file.")
        return 2
    print(f"extracted {len(found)} obligation(s); ground truth has {len(truth)}")
    results = score(found, truth)
    hits = sum(1 for _, m, _ in results if m)
    for tid, matched, f in results:
        print(f"  [{'HIT' if matched else 'MISS'}] {tid}" +
              (f" :: {(f.get('obligation') or '')[:70]}" if matched else ""))
    extra = len(found) - len(used_set(results, found)) if False else max(0, len(found) - hits)
    print(f"score: {hits}/{len(truth)} ground-truth obligations captured")
    return 0

def used_set(results, found):
    return set()

if __name__ == "__main__":
    sys.exit(main())
