"""DeepSeek 调用封装：统一返回结构 + 用量/费用记账 + 预算保护。

只依赖 openai SDK（DeepSeek 兼容 OpenAI 格式）。
密钥从环境变量 DEEPSEEK_API_KEY 读取，永不打印。
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from ..agents.base import BudgetExceeded
from .pricing import compute_cost, is_peak

# 项目根目录的 .env（已 gitignore）在这里统一加载
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_BASE_URL = "https://api.deepseek.com"


@dataclass
class LLMResponse:
    """一次 API 调用的标准化结果。"""

    content: Optional[str]
    reasoning: Optional[str]
    tool_calls: List[dict]
    finish_reason: str
    latency_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    cost_cny: float = 0.0
    peak: bool = False
    model: str = ""
    effort: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Budget:
    """跨对局共享的费用预算（元）。"""

    limit_cny: float = float("inf")
    spent_cny: float = 0.0
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    models: set = field(default_factory=set)
    efforts: set = field(default_factory=set)

    @property
    def remaining_cny(self) -> float:
        return max(0.0, self.limit_cny - self.spent_cny)

    def charge(self, resp: LLMResponse) -> None:
        self.spent_cny += resp.cost_cny
        self.calls += 1
        self.prompt_tokens += resp.prompt_tokens
        self.completion_tokens += resp.completion_tokens
        self.reasoning_tokens += resp.reasoning_tokens
        self.cache_hit_tokens += resp.cache_hit_tokens
        self.cache_miss_tokens += resp.cache_miss_tokens
        if resp.model:
            self.models.add(resp.model)
        if resp.effort:
            self.efforts.add(resp.effort)
        if self.spent_cny > self.limit_cny:
            raise BudgetExceeded(
                f"LLM 预算超限：已花费 ¥{self.spent_cny:.4f}，上限 ¥{self.limit_cny:.2f}"
            )

    def summary(self) -> dict:
        return {
            "models": sorted(self.models),
            "efforts": sorted(self.efforts),
            "limit_cny": self.limit_cny,
            "spent_cny": round(self.spent_cny, 6),
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cache_hit_tokens": self.cache_hit_tokens,
            "cache_miss_tokens": self.cache_miss_tokens,
        }


class DeepSeekClient:
    """极薄的 DeepSeek 客户端，负责记账。"""

    def __init__(
        self,
        model: str = "deepseek-flash",
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        budget: Optional[Budget] = None,
        timeout_s: float = 600.0,
        max_retries: int = 2,
    ):
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY（检查根目录 .env）")
        self.model = model
        self.budget = budget or Budget()
        self.max_retries = max_retries
        self._client = OpenAI(api_key=key, base_url=base_url, timeout=timeout_s)

    def chat(
        self,
        messages: List[dict],
        *,
        tools: Optional[List[dict]] = None,
        effort: str = "max",
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """一次对话调用。失败按 max_retries 重试（指数退避）。"""
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "reasoning_effort": effort,
        }
        if tools:
            kwargs["tools"] = tools
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                resp = self._client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - 网络/限流等一律重试
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                time.sleep(2 ** attempt * 2)
                continue

            latency = time.time() - t0
            choice = resp.choices[0]
            msg = choice.message
            usage = resp.usage
            details = getattr(usage, "completion_tokens_details", None)
            reasoning_tokens = int(getattr(details, "reasoning_tokens", 0) or 0)
            cache_hit = int(getattr(usage, "prompt_cache_hit_tokens", 0) or 0)
            cache_miss = int(getattr(usage, "prompt_cache_miss_tokens", 0) or 0)

            tool_calls = [
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in (msg.tool_calls or [])
            ]

            peak = is_peak()
            result = LLMResponse(
                content=msg.content,
                reasoning=getattr(msg, "reasoning_content", None),
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "",
                latency_s=latency,
                prompt_tokens=int(usage.prompt_tokens or 0),
                completion_tokens=int(usage.completion_tokens or 0),
                reasoning_tokens=reasoning_tokens,
                cache_hit_tokens=cache_hit,
                cache_miss_tokens=cache_miss,
                cost_cny=compute_cost(
                    self.model, cache_hit=cache_hit, cache_miss=cache_miss,
                    output=int(usage.completion_tokens or 0),
                ),
                peak=peak,
                model=self.model,
                effort=effort,
                raw=resp.model_dump(),
            )
            self.budget.charge(result)
            return result

        raise last_error if last_error else RuntimeError("调用失败")
