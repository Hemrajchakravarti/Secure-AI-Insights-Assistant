# -*- coding: utf-8 -*-
"""
app/services/orchestrator.py
AI orchestration using Ollama (free, local, no API key needed).
Handles both proper tool_calls and text-based JSON tool calls
so it works with smaller models like llama3.2 (3B).
"""

import os, json, re, logging
from openai import OpenAI
from app.tools.retrieval import (
    query_movie_database, search_executive_pdfs,
    analyze_csv_data, calculate_marketing_roi,
)

logger       = logging.getLogger(__name__)
OLLAMA_URL   = os.environ.get("OLLAMA_URL",   "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI analytics assistant for an entertainment company.
You have tools to query databases and documents. Use them to answer questions with real data.

IMPORTANT INSTRUCTIONS:
- Always call a tool first to get data before answering.
- After getting tool results, write a clear human-readable answer.
- Never make up numbers or statistics.
- End your final answer with: Sources used: [tool names]
"""

# Explicit tool instructions appended to each user message for small models
TOOL_INSTRUCTIONS = """

You have these tools available. To use a tool, output ONLY this exact JSON format and nothing else:
{"tool": "TOOL_NAME", "input": {PARAMETERS}}

Tools:
1. query_movie_database - Query movie/viewer database
   {"tool": "query_movie_database", "input": {"query_type": "top_titles_by_year", "params": ["2025"]}}
   {"tool": "query_movie_database", "input": {"query_type": "compare_titles", "params": ["dark orbit", "last kingdom"]}}
   {"tool": "query_movie_database", "input": {"query_type": "title_detail", "params": ["%stellar run%"]}}
   {"tool": "query_movie_database", "input": {"query_type": "genre_performance", "params": []}}

2. search_executive_pdfs - Search internal reports and documents
   {"tool": "search_executive_pdfs", "input": {"query": "your search query here"}}

3. analyze_csv_data - Analyze regional, marketing, viewer data
   {"tool": "analyze_csv_data", "input": {"csv_name": "regional_performance", "operation": "top_cities"}}
   {"tool": "analyze_csv_data", "input": {"csv_name": "marketing_spend", "operation": "channel_spend"}}

4. calculate_marketing_roi - Calculate ROI metrics
   {"tool": "calculate_marketing_roi", "input": {"movie_title": "stellar run"}}

Call ONE tool at a time. After seeing tool results, write your final answer.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_movie_database",
            "description": "Query the SQLite movie database. query_type: top_titles_by_year|title_detail|compare_titles|genre_performance",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {"type": "string", "enum": ["top_titles_by_year","title_detail","compare_titles","genre_performance"]},
                    "params":     {"type": "array", "items": {"type": "string"}},
                },
                "required": ["query_type", "params"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_executive_pdfs",
            "description": "Semantic search over internal PDF documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":     {"type": "string"},
                    "n_results": {"type": "integer", "default": 4},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_csv_data",
            "description": "Aggregate analytics on CSV files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_name":  {"type": "string"},
                    "operation": {"type": "string", "enum": ["top_cities","channel_spend","platform_breakdown","monthly_trend","summary"]},
                    "filters":   {"type": "object"},
                },
                "required": ["csv_name", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_marketing_roi",
            "description": "Calculate ROI metrics per title and channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_title": {"type": "string"},
                    "channel":     {"type": "string"},
                },
            },
        },
    },
]

DISPATCH = {
    "query_movie_database":    lambda i: query_movie_database(i["query_type"], i["params"]),
    "search_executive_pdfs":   lambda i: search_executive_pdfs(i["query"], i.get("n_results", 4)),
    "analyze_csv_data":        lambda i: analyze_csv_data(i["csv_name"], i["operation"], i.get("filters")),
    "calculate_marketing_roi": lambda i: calculate_marketing_roi(i.get("movie_title"), i.get("channel")),
}


def _check_ollama() -> str | None:
    import httpx
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=3.0)
        return None
    except Exception:
        return (
            f"Cannot connect to Ollama at {OLLAMA_URL}.\n"
            "Make sure Ollama is running (open the Ollama app or run: ollama serve).\n"
            f"Also ensure the model is pulled: ollama pull {OLLAMA_MODEL}"
        )


def _extract_json_tool_call(text: str) -> dict | None:
    """
    Extract a tool call from plain text — handles small models that return
    JSON as text instead of using the proper tool_calls API field.
    """
    # Try to find {"tool": ..., "input": ...} pattern
    patterns = [
        r'\{[^{}]*"tool"\s*:[^{}]*"input"\s*:\s*\{[^{}]*\}[^{}]*\}',
        r'\{[^{}]*"tool"\s*:[^{}]*\}',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                obj = json.loads(match)
                if "tool" in obj and "input" in obj:
                    return obj
            except json.JSONDecodeError:
                continue

    # Try the whole text as JSON
    text_stripped = text.strip()
    if text_stripped.startswith("{"):
        try:
            obj = json.loads(text_stripped)
            if "tool" in obj and "input" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    # Also handle {"name": ..., "parameters": ...} format some models use
    try:
        obj = json.loads(text_stripped)
        if "name" in obj and obj["name"] in DISPATCH:
            params = obj.get("parameters", obj.get("input", obj.get("arguments", {})))
            return {"tool": obj["name"], "input": params}
    except Exception:
        pass

    return None


def _looks_like_only_tool_call(text: str) -> bool:
    """True if the text is mostly/entirely a tool call JSON with no real answer."""
    stripped = text.strip()
    if not stripped:
        return False
    # If it starts with { and we can parse a tool call, it's a tool call
    if stripped.startswith("{") and _extract_json_tool_call(stripped):
        return True
    # If "Sources used:" is right after a JSON blob with no real sentences
    if _extract_json_tool_call(stripped) and len(stripped) < 300:
        return True
    return False


def run_agent(user_message: str, history: list = None) -> dict:
    err = _check_ollama()
    if err:
        return {"answer": err, "tool_trace": [], "sources": []}

    client = OpenAI(api_key="ollama", base_url=OLLAMA_URL)

    # For small models: append explicit tool instructions to user message
    augmented_message = user_message + TOOL_INSTRUCTIONS

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in (history or []):
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": augmented_message})

    tool_trace: list[dict] = []
    collected_results: list[str] = []

    for iteration in range(8):
        logger.info("Agent iteration %d | model: %s", iteration + 1, OLLAMA_MODEL)

        try:
            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=2048,
                temperature=0.1,
            )
        except Exception as exc:
            logger.exception("Ollama request failed")
            return {
                "answer": f"Ollama error: {exc}\n\nMake sure Ollama is running and '{OLLAMA_MODEL}' is pulled.\nRun: ollama pull {OLLAMA_MODEL}",
                "tool_trace": tool_trace,
                "sources": [],
            }

        msg = response.choices[0].message
        content = msg.content or ""

        # ── Path A: model used proper tool_calls API ──────────────────────
        if msg.tool_calls:
            assistant_entry = {
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            }
            messages.append(assistant_entry)

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    inp = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    inp = {}
                raw = _run_tool(name, inp)
                tool_trace.append({"tool": name, "input": inp, "result_summary": _summarize(raw)})
                collected_results.append(f"[{name} result]\n{json.dumps(raw)[:2000]}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(raw)[:3000]})

            continue  # get next response from model

        # ── Path B: small model returned JSON tool call as plain text ─────
        if _looks_like_only_tool_call(content):
            tool_call = _extract_json_tool_call(content)
            if tool_call:
                name = tool_call.get("tool", "")
                inp  = tool_call.get("input", {})
                logger.info("Text-based tool call detected: %s | input: %s", name, str(inp)[:150])

                messages.append({"role": "assistant", "content": content})

                raw = _run_tool(name, inp)
                tool_trace.append({"tool": name, "input": inp, "result_summary": _summarize(raw)})
                result_text = json.dumps(raw)[:2000]
                collected_results.append(f"[{name} result]\n{result_text}")

                # Feed result back and ask for final answer
                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool result from {name}:\n{result_text}\n\n"
                        "Now write a clear, human-readable answer based on this data. "
                        "Do NOT output JSON. Write normal sentences and bullet points."
                    )
                })
                continue

        # ── Path C: model gave a real text answer ─────────────────────────
        # If we called tools but got no answer text, synthesise one
        if not content.strip() and collected_results:
            messages.append({
                "role": "user",
                "content": "Please summarise the tool results above in a clear answer now."
            })
            continue

        # We have a real answer — but filter out answers that are just JSON
        if _looks_like_only_tool_call(content):
            # Model is stuck in JSON mode — force a plain answer
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": "Write your answer in plain English now. No JSON."
            })
            continue

        # Good answer — return it
        sources = list({t["tool"] for t in tool_trace})
        return {
            "answer":     content,
            "tool_trace": tool_trace,
            "sources":    sources,
        }

    # Fallback: synthesise answer from collected results
    if collected_results:
        summary_messages = [
            {"role": "system", "content": "You are a helpful analytics assistant. Summarise the following data clearly."},
            {"role": "user", "content": "Here is the data collected:\n\n" + "\n\n".join(collected_results) + "\n\nProvide a clear, concise answer about: " + user_message},
        ]
        try:
            r = client.chat.completions.create(model=OLLAMA_MODEL, messages=summary_messages, max_tokens=1024, temperature=0.1)
            answer = r.choices[0].message.content or "Could not generate summary."
        except Exception:
            answer = "Data collected but could not generate final answer. Raw data: " + " | ".join(collected_results)[:500]
        return {"answer": answer, "tool_trace": tool_trace, "sources": list({t["tool"] for t in tool_trace})}

    return {"answer": "Could not generate an answer. Try rephrasing your question.", "tool_trace": tool_trace, "sources": []}


def _run_tool(name: str, inp: dict) -> dict:
    if name not in DISPATCH:
        return {"error": f"Unknown tool: {name}"}
    try:
        return DISPATCH[name](inp)
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return {"error": str(exc)}


def _summarize(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"
    data = result.get("result", result)
    if isinstance(data, list): return f"{len(data)} records returned"
    if isinstance(data, dict): return f"{len(data)} keys returned"
    return str(data)[:100]