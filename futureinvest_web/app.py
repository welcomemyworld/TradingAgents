from __future__ import annotations

import argparse
import json
import traceback
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from tradingagents.agents.utils.agent_utils import (
    ANALYST_CAPABILITY_SUMMARIES,
    ANALYST_DISPLAY_NAMES,
    ANALYST_ORDER,
    normalize_selected_analysts,
)
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import FutureInvestGraph

from cli.utils import (
    POSITION_IMPORTANCE_LABELS,
    RESEARCH_DEPTH_LABELS,
    RUN_MODE_CONTROL_PRESETS,
    RUN_MODE_PRESETS,
    TOKEN_BUDGET_LABELS,
)
from .serializer import build_web_sections


PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"

PROVIDER_PRESETS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "backend_url": "https://api.openai.com/v1",
        "quick_models": ["gpt-5-mini", "gpt-5-nano", "gpt-5.4", "gpt-4.1"],
        "deep_models": ["gpt-5.4", "gpt-5.2", "gpt-5-mini", "gpt-5.4-pro"],
        "setting_field": "openai_reasoning_effort",
        "setting_label": "Reasoning Effort",
        "setting_options": ["medium", "high", "low"],
    },
    "google": {
        "label": "Google",
        "backend_url": "https://generativelanguage.googleapis.com/v1",
        "quick_models": ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-3.1-flash-lite-preview"],
        "deep_models": ["gemini-3.1-pro-preview", "gemini-2.5-pro", "gemini-3-flash-preview"],
        "setting_field": "google_thinking_level",
        "setting_label": "Thinking Level",
        "setting_options": ["high", "medium", "minimal"],
    },
    "anthropic": {
        "label": "Anthropic",
        "backend_url": "https://api.anthropic.com/",
        "quick_models": ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-sonnet-4-5"],
        "deep_models": ["claude-opus-4-6", "claude-opus-4-5", "claude-sonnet-4-6"],
        "setting_field": "anthropic_effort",
        "setting_label": "Effort Level",
        "setting_options": ["high", "medium", "low"],
    },
    "xai": {
        "label": "xAI",
        "backend_url": "https://api.x.ai/v1",
        "quick_models": ["grok-4-1-fast-non-reasoning", "grok-4-fast-non-reasoning"],
        "deep_models": ["grok-4-0709", "grok-4-1-fast-reasoning", "grok-4-fast-reasoning"],
        "setting_field": None,
        "setting_label": None,
        "setting_options": [],
    },
    "openrouter": {
        "label": "OpenRouter",
        "backend_url": "https://openrouter.ai/api/v1",
        "quick_models": ["nvidia/nemotron-3-nano-30b-a3b:free", "z-ai/glm-4.5-air:free"],
        "deep_models": ["z-ai/glm-4.5-air:free", "nvidia/nemotron-3-nano-30b-a3b:free"],
        "setting_field": None,
        "setting_label": None,
        "setting_options": [],
    },
    "ollama": {
        "label": "Ollama",
        "backend_url": "http://localhost:11434/v1",
        "quick_models": ["qwen3:latest", "gpt-oss:latest", "glm-4.7-flash:latest"],
        "deep_models": ["glm-4.7-flash:latest", "gpt-oss:latest", "qwen3:latest"],
        "setting_field": None,
        "setting_label": None,
        "setting_options": [],
    },
}


def build_metadata() -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "today": today,
        "run_modes": [
            {
                "key": key,
                "label": preset["label"],
                "description": preset["description"],
                "suggested_depth": preset["suggested_depth"],
                "recommended_position_importance": RUN_MODE_CONTROL_PRESETS[key]["position_importance"],
                "recommended_token_budget": RUN_MODE_CONTROL_PRESETS[key]["token_budget"],
            }
            for key, preset in RUN_MODE_PRESETS.items()
        ],
        "position_importance": [
            {"key": key, "label": label} for key, label in POSITION_IMPORTANCE_LABELS.items()
        ],
        "token_budget": [
            {"key": key, "label": label} for key, label in TOKEN_BUDGET_LABELS.items()
        ],
        "research_depth": [
            {"value": value, "label": label} for value, label in RESEARCH_DEPTH_LABELS.items()
        ],
        "capabilities": [
            {
                "key": key,
                "label": ANALYST_DISPLAY_NAMES[key],
                "summary": ANALYST_CAPABILITY_SUMMARIES[key],
            }
            for key in ANALYST_ORDER
        ],
        "providers": PROVIDER_PRESETS,
        "defaults": {
            "ticker": "SPY",
            "analysis_date": today,
            "run_mode": "committee",
            "position_importance": "critical",
            "token_budget": "expansive",
            "research_depth": 5,
            "selected_analysts": ANALYST_ORDER,
            "llm_provider": DEFAULT_CONFIG["llm_provider"],
            "backend_url": DEFAULT_CONFIG["backend_url"],
            "quick_think_llm": DEFAULT_CONFIG["quick_think_llm"],
            "deep_think_llm": DEFAULT_CONFIG["deep_think_llm"],
            "openai_reasoning_effort": DEFAULT_CONFIG.get("openai_reasoning_effort") or "medium",
            "google_thinking_level": DEFAULT_CONFIG.get("google_thinking_level") or "high",
            "anthropic_effort": DEFAULT_CONFIG.get("anthropic_effort") or "high",
        },
    }


def build_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = int(payload.get("research_depth", 1))
    config["max_risk_discuss_rounds"] = int(payload.get("research_depth", 1))
    config["quick_think_llm"] = payload.get("quick_think_llm") or DEFAULT_CONFIG["quick_think_llm"]
    config["deep_think_llm"] = payload.get("deep_think_llm") or DEFAULT_CONFIG["deep_think_llm"]
    config["backend_url"] = payload.get("backend_url") or DEFAULT_CONFIG["backend_url"]
    config["llm_provider"] = str(payload.get("llm_provider") or DEFAULT_CONFIG["llm_provider"]).lower()
    config["orchestrator_position_importance"] = payload.get("position_importance") or DEFAULT_CONFIG["orchestrator_position_importance"]
    config["orchestrator_token_budget"] = payload.get("token_budget") or DEFAULT_CONFIG["orchestrator_token_budget"]
    config["google_thinking_level"] = payload.get("google_thinking_level")
    config["openai_reasoning_effort"] = payload.get("openai_reasoning_effort")
    config["anthropic_effort"] = payload.get("anthropic_effort")
    return config


def run_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(payload.get("ticker", "SPY")).strip().upper()
    analysis_date = str(payload.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))).strip()
    selected_analysts = normalize_selected_analysts(payload.get("selected_analysts") or ANALYST_ORDER)
    config = build_config(payload)

    started_at = datetime.now()
    graph = FutureInvestGraph(selected_analysts, config=config, debug=False)
    final_state, decision = graph.propagate(ticker, analysis_date)
    elapsed_seconds = (datetime.now() - started_at).total_seconds()

    return {
        "success": True,
        "ticker": ticker,
        "analysis_date": analysis_date,
        "selected_analysts": selected_analysts,
        "decision": decision,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "sections": build_web_sections(final_state),
        "final_state": {
            "portfolio_context": final_state.get("portfolio_context", {}),
            "temporal_context": final_state.get("temporal_context", {}),
            "institution_memory_snapshot": final_state.get("institution_memory_snapshot", {}),
            "final_decision": final_state.get("final_decision", {}),
        },
    }


class FutureInvestRequestHandler(BaseHTTPRequestHandler):
    server_version = "FutureInvestWeb/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._serve_static("index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self._serve_static("styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._serve_static("app.js", "application/javascript; charset=utf-8")
            return
        if parsed.path == "/cci-monogram.svg":
            self._serve_static("cci-monogram.svg", "image/svg+xml")
            return
        if parsed.path == "/api/meta":
            self._send_json(build_metadata())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"success": False, "error": "Invalid JSON payload."}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            response = run_analysis(payload)
            self._send_json(response)
        except Exception as exc:
            self._send_json(
                {
                    "success": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _serve_static(self, filename: str, content_type: str) -> None:
        path = STATIC_DIR / filename
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Static asset not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Future Invest web interface.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind. Default: 8000")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), FutureInvestRequestHandler)
    print(f"Future Invest web interface running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
