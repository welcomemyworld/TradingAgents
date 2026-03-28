from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, Iterable, List

from langchain_core.tools import StructuredTool


_ACTIVE_TRACE: ContextVar["RunTraceRecorder | None"] = ContextVar(
    "futureinvest_active_trace",
    default=None,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _preview(value: Any, limit: int = 700) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


def get_active_trace_recorder() -> "RunTraceRecorder | None":
    return _ACTIVE_TRACE.get()


@contextmanager
def activate_run_trace(recorder: "RunTraceRecorder"):
    token = _ACTIVE_TRACE.set(recorder)
    try:
        yield recorder
    finally:
        _ACTIVE_TRACE.reset(token)


class RunTraceRecorder:
    """Append-only run trace with soft guardrails inspired by agent scratchpads."""

    def __init__(
        self,
        config: Dict[str, Any],
        ticker: str,
        trade_date: str,
        selected_analysts: Iterable[str],
        loop_mode: str,
    ):
        self.config = config
        self.ticker = str(ticker).strip().upper()
        self.trade_date = str(trade_date).strip()
        self.selected_analysts = list(selected_analysts or [])
        self.loop_mode = _clean_text(loop_mode) or "full"
        self.preview_chars = int(config.get("institution_trace_preview_chars", 700))
        self.tool_call_soft_limit = int(config.get("tool_call_soft_limit", 3))
        self.tool_repeat_soft_limit = int(config.get("tool_repeat_soft_limit", 2))
        self.tool_counts: Dict[str, int] = {}
        self.signature_counts: Dict[str, int] = {}
        self.warning_events: List[str] = []

        project_dir = Path(config.get("project_dir", "."))
        trace_dir = Path(
            config.get("institution_trace_dir", project_dir / "institution_traces")
        )
        trace_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}_{self.ticker}_{self.trade_date}_{self.loop_mode}.jsonl"
        self.path = trace_dir / filename

        self.append(
            "run_started",
            {
                "ticker": self.ticker,
                "trade_date": self.trade_date,
                "loop_mode": self.loop_mode,
                "selected_analysts": self.selected_analysts,
            },
        )

    def append(self, event: str, payload: Dict[str, Any]) -> None:
        entry = {"ts_utc": _utc_now(), "event": event, **payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True, default=_json_default))
            handle.write("\n")

    def _signature_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        payload = json.dumps(tool_args, ensure_ascii=True, sort_keys=True, default=str)
        digest = sha1(payload.encode("utf-8")).hexdigest()[:10]
        return f"{tool_name}:{digest}"

    def inspect_tool_call(self, tool_name: str, tool_args: Dict[str, Any]) -> List[str]:
        warnings: List[str] = []
        self.tool_counts[tool_name] = self.tool_counts.get(tool_name, 0) + 1
        signature_key = self._signature_key(tool_name, tool_args)
        self.signature_counts[signature_key] = self.signature_counts.get(signature_key, 0) + 1

        if self.tool_counts[tool_name] > self.tool_call_soft_limit:
            warnings.append(
                f"{tool_name} has already been called {self.tool_counts[tool_name] - 1} times in this run. Reuse existing evidence unless the next query is materially different."
            )

        if self.signature_counts[signature_key] > self.tool_repeat_soft_limit:
            warnings.append(
                f"{tool_name} is repeating a very similar query. Avoid loops and move the institutional loop forward."
            )

        for warning in warnings:
            if warning not in self.warning_events:
                self.warning_events.append(warning)

        return warnings

    def record_tool_result(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
        warnings: Iterable[str] | None = None,
    ) -> None:
        self.append(
            "tool_result",
            {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "warnings": list(warnings or []),
                "result_preview": _preview(result, self.preview_chars),
            },
        )

    def record_capability_event(
        self,
        analyst_key: str,
        stage: str,
        report: Any = "",
        status: str = "",
        detail: Dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "analyst_key": analyst_key,
            "stage": stage,
            "status": status,
            "report_preview": _preview(report, self.preview_chars),
        }
        if detail:
            payload.update(detail)
        self.append("research_capability", payload)

    def finalize(self, final_state: Dict[str, Any], decision: str) -> None:
        orchestration_state = final_state.get("orchestration_state") or {}
        portfolio_context = final_state.get("portfolio_context") or {}
        final_decision = final_state.get("final_decision") or {}
        self.append(
            "run_completed",
            {
                "decision": _clean_text(decision),
                "tool_call_counts": self.tool_counts,
                "warning_count": len(self.warning_events),
                "warnings": self.warning_events,
                "token_budget": _clean_text(orchestration_state.get("token_budget")),
                "position_importance": _clean_text(
                    orchestration_state.get("position_importance")
                ),
                "portfolio_role": _clean_text(portfolio_context.get("portfolio_role")),
                "rating": _clean_text(final_decision.get("rating")),
                "kill_criteria": _preview(
                    final_decision.get("kill_criteria"), self.preview_chars
                ),
            },
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "loop_mode": self.loop_mode,
            "tool_call_counts": dict(self.tool_counts),
            "warning_count": len(self.warning_events),
            "warnings": list(self.warning_events),
        }


def wrap_tool_with_trace(base_tool) -> StructuredTool:
    """Wrap a structured tool with trace logging and soft guardrail warnings."""

    def _runner(**kwargs):
        recorder = get_active_trace_recorder()
        warnings = recorder.inspect_tool_call(base_tool.name, kwargs) if recorder else []
        result = base_tool.invoke(kwargs)
        result_text = result if isinstance(result, str) else json.dumps(
            result, ensure_ascii=True, default=str
        )
        if warnings:
            warning_block = "\n".join(
                f"[Institutional loop warning] {warning}" for warning in warnings
            )
            result_text = f"{warning_block}\n\n{result_text}"
        if recorder:
            recorder.record_tool_result(base_tool.name, kwargs, result_text, warnings)
        return result_text

    return StructuredTool.from_function(
        func=_runner,
        name=base_tool.name,
        description=base_tool.description,
        return_direct=base_tool.return_direct,
        args_schema=base_tool.args_schema,
        infer_schema=False,
    )
