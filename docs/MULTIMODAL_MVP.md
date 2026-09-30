# Multimodal MVP and production path

## Delivered first phase

`/chat-demo?from=store` contains synthetic photo and voice demo controls. The browser sends only bounded metadata (`kind`, file name, MIME type, byte count, demo scenario). It never uploads a local file, invokes a vision/STT provider, or persists media bytes. The backend normalizes metadata, applies a safety gate, and then invokes the same controlled Agent tools.

## Production prerequisites

1. Approved vision/STT providers behind a replaceable adapter, timeouts, and fallback.
2. Per-tenant encrypted object storage, short-lived signed URLs, retention/deletion policies, and no media bytes in logs, traces, prompts, or checkpoints.
3. MIME signature validation, size/duration limits, malware scanning, EXIF stripping, OCR prompt-injection handling, and consent notices.
4. Confidence thresholds and a user-correction UI; low-confidence extraction must ask a follow-up.
5. Multimodal badcase evaluation: blurry images, accents, misleading OCR, battery damage, medical/electrical safety, and order screenshots.

No production connector may treat a photo or transcript as proof of order ownership, refund eligibility, product authenticity, or electrical safety.
