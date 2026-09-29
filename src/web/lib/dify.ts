export async function postToDify(payload: Record<string, unknown>) {
  const apiBaseUrl = process.env.DIFY_API_BASE_URL;
  const apiKey = process.env.DIFY_API_KEY;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);

  if (!apiBaseUrl || !apiKey) {
    return {
      mode: "mock",
      message: "Dify environment variables are not configured yet."
    };
  }

  try {
    const response = await fetch(`${apiBaseUrl}/chat-messages`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Dify request failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Dify request timed out after 60 seconds");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function isMockEnabled() {
  return process.env.NEXT_PUBLIC_USE_MOCK === "true";
}
