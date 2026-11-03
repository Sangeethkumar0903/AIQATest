"""FastAPI application used as the deterministic system under test."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from sample_app.knowledge_base import retrieve

app = FastAPI(title="AIQATest Sample RAG Service", version="1.0.0")

REFUSAL = "I can't comply with requests to reveal restricted, private, or system information."
UNKNOWN = "I don't have enough information in the knowledge base to answer that question."
_DANGEROUS_PATTERNS = (
    "ignore previous",
    "ignore all",
    "system prompt",
    "reveal secret",
    "password",
    "private data",
    "synthetic pii",
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]
    retrieved_context: list[str]
    request_id: str
    refused: bool = False


def answer_question(question: str) -> AnswerResponse:
    normalized = " ".join(question.lower().split())
    if any(pattern in normalized for pattern in _DANGEROUS_PATTERNS):
        return AnswerResponse(
            answer=REFUSAL,
            sources=[],
            retrieved_context=[],
            request_id=str(uuid4()),
            refused=True,
        )

    documents = retrieve(question)
    if not documents:
        return AnswerResponse(
            answer=UNKNOWN,
            sources=[],
            retrieved_context=[],
            request_id=str(uuid4()),
        )
    if any(
        any(pattern in document.text.lower() for pattern in _DANGEROUS_PATTERNS)
        for document in documents
    ):
        return AnswerResponse(
            answer=REFUSAL,
            sources=[],
            retrieved_context=[],
            request_id=str(uuid4()),
            refused=True,
        )
    return AnswerResponse(
        answer=documents[0].text,
        sources=[document.source_id for document in documents],
        retrieved_context=[document.text for document in documents],
        request_id=str(uuid4()),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "deterministic"}


@app.post("/ask", response_model=AnswerResponse)
async def ask(request: AskRequest) -> AnswerResponse:
    return answer_question(request.question)


@app.post("/chat", response_model=AnswerResponse)
async def chat(request: ChatRequest) -> AnswerResponse:
    user_messages = [message.content for message in request.messages if message.role == "user"]
    if not user_messages:
        return AnswerResponse(
            answer="I cannot answer without a user message.",
            sources=[],
            retrieved_context=[],
            request_id=str(uuid4()),
            refused=True,
        )
    latest = user_messages[-1]
    # Resolve one explicit follow-up form using earlier user context; this is deterministic,
    # not an LLM or a claim of general coreference resolution.
    if latest.lower().strip(" ?.!") in {"how long is that", "how many days is that"}:
        latest = next((message for message in reversed(user_messages[:-1]) if message), latest)
    return answer_question(latest)


@app.get("/", response_class=HTMLResponse)
async def web_ui() -> str:
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>AIQATest Demo</title></head>
<body><main><h1>Knowledge Base Assistant</h1>
<form id="ask-form"><label for="question">Question</label>
<input id="question" name="question" required><button type="submit">Ask</button></form>
<p id="error" role="alert"></p><section id="answer" aria-live="polite"></section></main>
<script>
const form = document.getElementById('ask-form');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = document.getElementById('question').value.trim();
  const error = document.getElementById('error');
  if (!question) { error.textContent = 'Please enter a question.'; return; }
  error.textContent = '';
  const response = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });
  if (!response.ok) { error.textContent = 'The request could not be completed.'; return; }
  const data = await response.json();
  document.getElementById('answer').textContent = data.answer;
});
</script></body></html>"""
