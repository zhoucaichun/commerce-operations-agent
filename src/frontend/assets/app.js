const $ = (selector) => document.querySelector(selector);
const presets = {
  product: { message: "charger" },
  order: { message: "order ORD-10023 tracking 4821", orderId: "ORD-10023", suffix: "4821" },
  handoff: { message: "create a human support ticket", key: "demo-ticket-001" },
};

const errorMessage = (status, detail) => {
  const messages = {
    401: "身份验证未通过：请提供有效的合成 Bearer Token。",
    403: "当前合成角色没有执行此查询的权限。",
    409: "相同幂等请求正在处理中，请稍后重试。",
    422: "输入校验未通过：请检查会话 ID、订单信息和幂等键格式。",
    429: "请求过于频繁，请稍后再试。",
  };
  return `${messages[status] || "请求未完成。"}${detail ? ` ${detail}` : ""}`;
};

document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => {
  const preset = presets[button.dataset.preset];
  $("#message").value = preset.message;
  $("#order-id").value = preset.orderId || "";
  $("#identity-suffix").value = preset.suffix || "";
  $("#idempotency-key").value = preset.key || "";
}));

document.addEventListener("keydown", (event) => {
  if (!event.altKey || event.ctrlKey || event.metaKey) return;
  const preset = { "1": "product", "2": "order", "3": "handoff" }[event.key];
  if (!preset) return;
  event.preventDefault();
  document.querySelector(`[data-preset="${preset}"]`).click();
  $("#message").focus();
});

$("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const slots = {};
  if ($("#order-id").value.trim()) slots.order_id = $("#order-id").value.trim();
  if ($("#identity-suffix").value.trim()) slots.identity_suffix = $("#identity-suffix").value.trim();
  const body = { thread_id: `web-${crypto.randomUUID()}`, message: $("#message").value.trim(), slots };
  if ($("#idempotency-key").value.trim()) body.idempotency_key = $("#idempotency-key").value.trim();
  const headers = { "Content-Type": "application/json" };
  if ($("#token").value.trim()) headers.Authorization = `Bearer ${$("#token").value.trim()}`;
  $("#status").textContent = "查询中";
  try {
    const response = await fetch("/api/v1/chat", { method: "POST", headers, body: JSON.stringify(body) });
    const data = await response.json();
    if (!response.ok) throw new Error(errorMessage(response.status, data.detail));
    $("#status").textContent = data.status;
    $("#answer").textContent = data.answer;
    $("#trace").textContent = JSON.stringify({ tools: data.tool_result_summary, handoff: data.handoff, trace: data.trace }, null, 2);
  } catch (error) {
    $("#status").textContent = "请求失败";
    $("#answer").textContent = `未执行任何真实操作：${error.message}`;
  }
});
