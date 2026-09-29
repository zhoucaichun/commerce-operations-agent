type AgentProxyPayload = {
  thread_id: string;
  message: string;
  slots?: Record<string, string>;
  idempotency_key?: string;
};

export async function postToCommerceAgent(payload: AgentProxyPayload) {
  const apiBaseUrl = process.env.COMMERCE_AGENT_API_BASE_URL;
  const syntheticToken = process.env.COMMERCE_AGENT_DEMO_TOKEN;

  if (!apiBaseUrl) {
    throw new Error("COMMERCE_AGENT_API_BASE_URL is not configured.");
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(syntheticToken ? { Authorization: `Bearer ${syntheticToken}` } : {})
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: controller.signal
    });
    const data = await response.json();
    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Commerce Agent request timed out after 15 seconds");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
