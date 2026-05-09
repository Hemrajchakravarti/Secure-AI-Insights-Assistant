# -*- coding: utf-8 -*-
"""
app/services/orchestrator.py
AI orchestration using Ollama (free, local, no API key needed).
Ollama's API is OpenAI-compatible so we use the openai SDK pointed at Ollama.
Make sure Ollama is running before starting the app: https://ollama.com
"""

import os, json, logging
from openai import OpenAI
from app.tools.retrieval import (
    query_movie_database, search_executive_pdfs,
    analyze_csv_data, calculate_marketing_roi,
)

logger       = logging.getLogger(__name__)
OLLAMA_URL   = os.environ.get("OLLAMA_URL",   "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT = """You are a Secure AI Insights Assistant for an internal entertainment analytics platform.

RULES:
1. Only use tools to fetch data. Never invent or guess statistics.
2. Never reveal individual viewer personal information — only aggregates.
3. Always state which tools you used at the end of your answer.
4. Be concise and professional.

End every answer with:
Sources used: [list the tool names you called]
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_movie_database",
            "description": (
                "Run a parameterised query against the SQLite movie database. "
                "Use for: top performing titles, title detail, comparing two titles, genre performance. "
                "query_type options: "
                "top_titles_by_year (params: [year e.g. '2025']), "
                "title_detail (params: ['%title%']), "
                "compare_titles (params: ['title1', 'title2']), "
                "genre_performance (params: [])."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["top_titles_by_year", "title_detail", "compare_titles", "genre_performance"],
                    },
                    "params": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["query_type", "params"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_executive_pdfs",
            "description": (
                "Semantic search over internal documents: quarterly reports, campaign summaries, "
                "content roadmap, policy guidelines, audience behavior reports. "
                "Use for qualitative insights, trends, recommendations, strategy."
            ),
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
            "description": (
                "Aggregate analytics on CSV files. "
                "csv_name: regional_performance, marketing_spend, viewers, watch_activity, reviews. "
                "operation: top_cities, channel_spend, platform_breakdown, monthly_trend, summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_name":  {"type": "string"},
                    "operation": {
                        "type": "string",
                        "enum": ["top_cities", "channel_spend", "platform_breakdown", "monthly_trend", "summary"],
                    },
                    "filters": {"type": "object"},
                },
                "required": ["csv_name", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_marketing_roi",
            "description": "Calculate cost-per-conversion and spend efficiency per movie title and/or marketing channel.",
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


def _check_ollama():
    """Return None if Ollama is reachable, or an error string."""
    import httpx
    try:
        httpx.get(OLLAMA_URL.replace("/v1", "/api/tags"), timeout=3.0)
        return None
    except Exception:
        return (
            f"Cannot connect to Ollama at {OLLAMA_URL}.\n"
            "Make sure the Ollama app is running.\n"
            "Download from: https://ollama.com/download\n"
            f"Then pull the model:  ollama pull {OLLAMA_MODEL}"
        )


def run_agent(user_message: str, history: list = None) -> dict:
    err = _check_ollama()
    if err:
        return {"answer": err, "tool_trace": [], "sources": []}

    # openai SDK pointed at Ollama's OpenAI-compatible endpoint
    client = OpenAI(
        api_key="ollama",          # Ollama ignores the key but the SDK requires a non-empty string
        base_url=OLLAMA_URL,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m["content"]} for m in (history or [])]
    messages.append({"role": "user", "content": user_message})

    tool_trace: list[dict] = []

    for iteration in range(6):
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
                "answer": f"Ollama error: {exc}\n\nMake sure Ollama is running and model '{OLLAMA_MODEL}' is pulled.\nRun: ollama pull {OLLAMA_MODEL}",
                "tool_trace": tool_trace,
                "sources": [],
            }

        msg = response.choices[0].message

        # Build a serialisable assistant message for history
        assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_entry)

        # No tool calls → final answer
        if not msg.tool_calls:
            return {
                "answer":     msg.content or "",
                "tool_trace": tool_trace,
                "sources":    list({t["tool"] for t in tool_trace}),
            }

        # Execute each tool call
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                inp = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                inp = {}

            logger.info("Tool: %s  input: %s", name, str(inp)[:200])

            raw = DISPATCH[name](inp) if name in DISPATCH else {"error": f"Unknown tool: {name}"}

            tool_trace.append({
                "tool":           name,
                "input":          inp,
                "result_summary": _summarize(raw),
            })

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(raw)[:4000],
            })

    return {
        "answer":     "Agent reached max iterations without a final answer.",
        "tool_trace": tool_trace,
        "sources":    [],
    }


def _summarize(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"
    data = result.get("result", result)
    if isinstance(data, list): return f"{len(data)} records returned"
    if isinstance(data, dict): return f"{len(data)} keys returned"
    return str(data)[:100]
