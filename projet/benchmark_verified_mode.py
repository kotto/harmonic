#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "http://" + base_url
    return base_url.rstrip("/")


def _load_dataset(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _post_generate(api_url: str, payload: Dict[str, Any], timeout_s: float) -> Tuple[Optional[Dict[str, Any]], Optional[str], float]:
    t0 = time.time()
    try:
        r = requests.post(api_url, json=payload, timeout=timeout_s)
    except Exception as e:
        return None, str(e), time.time() - t0
    dt = time.time() - t0
    if r.status_code != 200:
        return None, f"http_{r.status_code}: {r.text[:300]}", dt
    try:
        return r.json(), None, dt
    except Exception:
        return None, "non_json_response", dt


def _is_abstention(content: str) -> bool:
    c = (content or "").lower()
    return ("abstention" in c) or ("abstain" in c)


def _extract_content(data: Dict[str, Any]) -> str:
    return data.get("content") or data.get("generated_text") or ""


def _extract_response_id(data: Dict[str, Any]) -> str:
    rid = data.get("response_id")
    if isinstance(rid, str):
        return rid
    metrics = data.get("metrics")
    if isinstance(metrics, dict) and isinstance(metrics.get("response_id"), str):
        return metrics["response_id"]
    return ""


def _extract_citations(data: Dict[str, Any]) -> List[Dict[str, str]]:
    c = data.get("citations")
    if isinstance(c, list):
        out: List[Dict[str, str]] = []
        for item in c:
            if isinstance(item, dict):
                cid = item.get("id")
                src = item.get("source")
                if isinstance(cid, str) and isinstance(src, str):
                    out.append({"id": cid, "source": src})
        return out
    return []

def _supports_verified_schema(data: Dict[str, Any]) -> bool:
    return any(k in data for k in ("response_id", "verified_mode", "citations", "metrics"))


def _citations_appear_in_text(content: str, citations: List[Dict[str, str]]) -> bool:
    if not citations:
        return False
    for c in citations:
        cid = c.get("id")
        if isinstance(cid, str) and cid and (f"[{cid}]" in (content or "")):
            return True
    return False


def _evaluate_case(
    api_url: str,
    case: Dict[str, Any],
    repeats: int,
    timeout_s: float,
) -> Dict[str, Any]:
    prompt = case.get("prompt") or ""
    max_tokens = int(case.get("max_tokens") or 600)
    verified_mode = bool(case.get("verified_mode", True))
    sources = case.get("sources") or []
    if not isinstance(sources, list):
        sources = []
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "verified_mode": verified_mode,
        "sources": sources,
    }

    observations: List[Dict[str, Any]] = []
    for _ in range(max(1, repeats)):
        data, err, dt = _post_generate(api_url, payload, timeout_s=timeout_s)
        if data is None:
            observations.append({"ok": False, "error": err, "latency_s": dt})
            continue
        content = _extract_content(data)
        rid = _extract_response_id(data)
        citations = _extract_citations(data)
        metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
        observations.append(
            {
                "ok": True,
                "latency_s": dt,
                "response_id": rid,
                "content": content,
                "citations": citations,
                "metrics": metrics,
                "schema_supported": _supports_verified_schema(data),
            }
        )

    oks = [o for o in observations if o.get("ok")]
    base_content = oks[0]["content"] if oks else ""
    base_rid = oks[0]["response_id"] if oks else ""
    stable_content = bool(oks) and all(o.get("content") == base_content for o in oks)
    stable_response_id = bool(oks) and all(o.get("response_id") == base_rid for o in oks) and bool(base_rid)
    schema_supported = bool(oks) and all(o.get("schema_supported") is True for o in oks)

    expect = case.get("expect") or {}
    should_abstain = bool(expect.get("should_abstain", False))
    should_cite = bool(expect.get("should_cite", False))

    abstains = _is_abstention(base_content)
    citations = oks[0]["citations"] if oks else []
    has_citations = bool(citations)
    cites_in_text = _citations_appear_in_text(base_content, citations)

    abstention_pass = (abstains is True) if should_abstain else (abstains is False)
    citations_pass = (has_citations and cites_in_text) if should_cite else (not has_citations)

    policy = ""
    if oks:
        m = oks[0].get("metrics")
        if isinstance(m, dict) and isinstance(m.get("policy"), str):
            policy = m["policy"]

    return {
        "id": case.get("id"),
        "vertical": case.get("vertical"),
        "label": case.get("label"),
        "request": {
            "verified_mode": verified_mode,
            "max_tokens": max_tokens,
            "sources_count": len(sources),
        },
        "expect": {"should_abstain": should_abstain, "should_cite": should_cite},
        "observations_count": len(observations),
        "ok_count": len(oks),
        "stability": {
            "stable_content": stable_content,
            "stable_response_id": stable_response_id,
            "schema_supported": schema_supported,
        },
        "checks": {
            "abstention_detected": abstains,
            "abstention_pass": abstention_pass,
            "citations_count": len(citations),
            "citations_in_text": cites_in_text,
            "citations_pass": citations_pass,
            "policy": policy,
        },
        "preview": {
            "response_id": base_rid,
            "content_240": (base_content[:240] + "...") if len(base_content) > 240 else base_content,
        },
        "errors": [o.get("error") for o in observations if not o.get("ok")],
    }


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--base-url", default=os.getenv("LM_ARENA_BASE_URL", ""), help="Ex: http://__EC2_IP__:8000")
    parser.add_argument("--dataset", default="benchmark_verified_mode_dataset.json")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--out", default="verified_mode_benchmark_results.json")
    args = parser.parse_args()

    base_url = _normalize_base_url(args.base_url) or _normalize_base_url("http://localhost:8000")
    api_url = f"{base_url}/generate"
    health_url = f"{base_url}/health"

    try:
        hr = requests.get(health_url, timeout=10)
        health_ok = hr.status_code == 200
        health_json = hr.json() if health_ok else {}
    except Exception as e:
        print(f"Health check failed: {e}")
        return 2

    dataset = _load_dataset(args.dataset)
    cases = dataset.get("cases") or []
    if not isinstance(cases, list) or not cases:
        print("Dataset invalide: cases manquant")
        return 2

    results: List[Dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        res = _evaluate_case(api_url, case, repeats=max(1, args.repeats), timeout_s=args.timeout)
        results.append(res)
        print(f"{res.get('id')}: ok={res.get('ok_count')}/{res.get('observations_count')} stable_id={res['stability']['stable_response_id']} abstain_pass={res['checks']['abstention_pass']} cite_pass={res['checks']['citations_pass']} policy={res['checks']['policy']}")

    total = len(results)
    schema_supported = sum(1 for r in results if r.get("stability", {}).get("schema_supported") is True)
    stable_id = sum(1 for r in results if r.get("stability", {}).get("stable_response_id") is True)
    stable_content = sum(1 for r in results if r.get("stability", {}).get("stable_content") is True)
    abstention_pass = sum(1 for r in results if r.get("checks", {}).get("abstention_pass") is True)
    citations_pass = sum(1 for r in results if r.get("checks", {}).get("citations_pass") is True)
    ok_any = sum(1 for r in results if (r.get("ok_count") or 0) > 0)

    summary = {
        "base_url": base_url,
        "api_url": api_url,
        "dataset": {"name": dataset.get("name"), "description": dataset.get("description")},
        "health": {"ok": health_ok, "data": health_json},
        "run": {"repeats": args.repeats, "timeout_s": args.timeout, "timestamp": time.time()},
        "metrics": {
            "cases_total": total,
            "cases_with_any_ok": ok_any,
            "schema_supported_rate": (schema_supported / total) if total else 0.0,
            "stability_response_id_rate": (stable_id / total) if total else 0.0,
            "stability_content_rate": (stable_content / total) if total else 0.0,
            "abstention_pass_rate": (abstention_pass / total) if total else 0.0,
            "citations_pass_rate": (citations_pass / total) if total else 0.0,
        },
        "results": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("")
    print("RÃ©sumÃ©:")
    print(json.dumps(summary["metrics"], ensure_ascii=False, indent=2))
    print(f"RÃ©sultats: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
