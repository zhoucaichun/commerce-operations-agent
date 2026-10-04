# Qwen model activation and evaluation

This repository is model-provider neutral at the transport boundary. For the first real-model trial, use an approved Qwen OpenAI-compatible endpoint and a text model selected in your provider workspace. The application calls no model until the three required environment variables are present **and** you explicitly run a command with `--live`.

## Recommended MVP allocation

| Agent responsibility | Recommended first choice | Why |
|---|---|---|
| Planner and evidence-bounded answer composer | A Qwen text/instruction model | One stable model keeps routing experiments reproducible and supports structured JSON output. |
| Product/policy retrieval, order checks and ticket creation | Controlled Python tools, not a model | Source data, authorization and safety rules must stay deterministic. |
| Image understanding later | Qwen VL model through a separate approved adapter | It belongs behind the existing metadata/safety gate, not in the text planner. |
| Speech-to-text later | A dedicated ASR provider (for example Gemini or another approved ASR service) | Transcription needs different latency, consent and retention controls. |
| Offline difficult-case judge | A stronger separately approved model | It may score held-out synthetic answers; it must not decide a customer-facing action. |

Do not start with a multi-model online routing system. First establish a baseline with one text model, the 145 migrated synthetic Dify cases, deterministic tools, and a versioned report. Do not use a code-specialist model as the consumer-support primary model merely because it is available in an API gateway.

## Local configuration

Copy the template without committing your local file. The backend does not auto-load `.env`; set the values in the PowerShell session that launches the API/evaluation, or use your deployment secret manager.

```powershell
$env:COMMERCE_LLM_PROVIDER = "qwen_openai_compatible"
$env:COMMERCE_LLM_BASE_URL = "https://your-approved-provider.example"
$env:COMMERCE_LLM_API_KEY = "your-secret"
$env:COMMERCE_LLM_MODEL = "the-exact-model-id-from-your-workspace"
$env:COMMERCE_LLM_RESPONSE_MODE = "json_schema"
$env:COMMERCE_LLM_TIMEOUT_SECONDS = "8"
```

Use the exact service address and model identifier displayed by the provider account you selected; do not guess them from a screenshot. The adapter accepts either a service root (and calls `/v1/chat/completions`) or a Base URL already ending in `/v1` (and calls `/chat/completions`), so both common provider conventions work. Set `COMMERCE_LLM_CHAT_PATH` only if the provider documents a nonstandard Chat Completions route. If that endpoint rejects `json_schema`, set `COMMERCE_LLM_RESPONSE_MODE=json_object`. The adapter then still validates the returned action, intent, slots and missing fields locally. Any timeout, malformed JSON, unsupported schema response, or validation failure falls back to the deterministic route; it cannot enable a commerce write.

Keep keys out of Git, the Next.js browser environment, screenshots, Dify exports, chat transcripts, and this document. A public/free API gateway is appropriate only for synthetic development tests after you have reviewed its privacy, retention, rate-limit and availability terms; it is not a production merchant-data path.

## Evaluation sequence

First verify the dataset and command without calling a provider:

```powershell
python src/eval/run_dify_model_eval.py --report reports/dify-model-eval-dry-run.json
```

Then use a low-cost, synthetic-only trial. This sends at most 30 migrated Dify prompts; it does not send real customer, merchant, order or media data.

```powershell
python src/eval/run_dify_model_eval.py --live --limit 30 --report reports/qwen-trial-30.json
```

Only after inspecting incorrect intent/route cases should you run the complete historical suite:

```powershell
python src/eval/run_dify_model_eval.py --live --report reports/qwen-full-145.json
```

The report measures exact Dify intent alignment and only the explicit follow-up/handoff route flags. It deliberately does **not** claim that lexical keypoint comparison proves answer quality. Review recommendation evidence, safety handoffs and representative answer text manually before promoting a model configuration.

If `model_planner_used` is zero, do not treat the intent score as a model-quality score: the deterministic fallback answered every case. Check `model_diagnostics` in the same report. It contains only aggregate categories such as `http_401`, `http_404`, `http_400`, `invalid_json`, `unexpected_response_shape`, or `planner_schema_rejected`; it never writes API keys, URLs, prompt bodies, model responses, or customer data. Use this to correct the provider URL/model ID/output mode before rerunning a 10-case synthetic trial.

## Production boundary

The Qwen structured-output API supports JSON-object and JSON-schema response modes; use function/tool contracts for model-to-tool decisions and keep local validation as the final authority. The current implementation uses the OpenAI-compatible Chat Completions transport and does not activate Shopify, OIDC, production tenant data or any write operation. See [AGENT_PRODUCTION_IMPLEMENTATION.md](AGENT_PRODUCTION_IMPLEMENTATION.md) and [PRODUCTION_MERCHANT_DATA.md](PRODUCTION_MERCHANT_DATA.md).
