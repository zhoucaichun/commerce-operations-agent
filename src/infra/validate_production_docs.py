"""Ensure production boundary documents retain their required safety guidance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "docs/operations/PRODUCTION.md": ("nginx -t", "certificate rotation", "Do not copy private keys"),
    "docs/operations/IDENTITY_PROVIDER_DESIGN.md": ("需审批的发布路径", "未实现", "上述阶段均未由本仓库实现"),
    "README.md": ("validate_proxy_config.py", "IDENTITY_PROVIDER_DESIGN.md"),
    "docs/operations/SECURITY_APPROVAL_CHECKLIST.md": ("状态：**未批准**", "不得添加任何 OIDC 提供方配置"),
}


def validate() -> list[str]:
    failures = []
    for relative, markers in REQUIRED.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative} missing: {marker}")
    return failures


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("production documentation validation failed: " + "; ".join(failures))
    print("production documentation validation passed")
