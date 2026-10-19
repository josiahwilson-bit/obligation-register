# Obligation Register — local edition

A local-first contract obligation extractor built with open-weight models.
Reads a short business agreement and extracts every obligation — who owes
what, how much, by when — each pinned to a **verbatim source quote** from
the document. No cloud API. The document never leaves the machine.

Built for the DEV Hacktoberfest Open-Source AI Challenge, Week 2
("Side Hustle"). It is the extraction engine for a fixed-price Contract
Obligation Register service ($150, one agreement up to 10 pages, delivered
with source quotations and unclear items flagged, no legal advice).

## How it works

- [Ollama](https://ollama.com) serves an open-weight model locally.
- `extract.py` (Python standard library only, no dependencies) prompts
  the model to return a JSON array of obligation packets: obligated
  party, obligation, amount, deadline, verbatim source quote.
- Extractions are scored against a human-authored ground truth
  (`ground-truth.json`); a quote only counts if it appears verbatim in
  the document. The model proposes — the evidence decides, a human
  approves.

## Run it

```bash
ollama serve &                 # local model server
ollama pull qwen3:4b           # or qwen2.5:0.5b
python3 extract.py sample-agreement.md --model qwen3:4b
```

## Demo results (fictional agreement, 6 planted obligations)

`sample-agreement.md` is an invented agreement (Juniper Table LLC +
Cove Supply Co., zero client data) with 6 planted obligations.

| Model | Captured | Time | Notes |
|---|---|---|---|
| Qwen 2.5 0.5B | 5 / 6 | ~29 s | Missed the confidentiality prohibition |
| Qwen 3 4B | 6 / 6 | ~4 min | Complete, including the prohibition |

Raw outputs: `obligations-qwen2.5_0.5b.json`, `obligations-qwen3_4b.json`.

The 0.5B miss is the interesting result: small models skip prohibitions —
duties phrased as "shall not." That is why the product wraps the model in
a human-review gate instead of pretending extraction is the deliverable.

## License

MIT
