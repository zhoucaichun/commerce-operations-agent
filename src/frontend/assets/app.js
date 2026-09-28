const $ = (selector) => document.querySelector(selector);
const presets = {
  product: { message: "charger" },
  order: { message: "order ORD-10023 tracking 4821", orderId: "ORD-10023", suffix: "4821" },
  handoff: { message: "create a human support ticket", key: "demo-ticket-001" },
};

document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => {
  const preset = presets[button.dataset.preset];
  $("#message").value = preset.message;
  $("#order-id").value = preset.orderId || "";
  $("#identity-suffix").value = preset.suffix || "";
  $("#idempotency-key").value = preset.key || "";
}));

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
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    $("#status").textContent = data.status;
    $("#answer").textContent = data.answer;
    $("#trace").textContent = JSON.stringify({ tools: data.tool_result_summary, handoff: data.handoff, trace: data.trace }, null, 2);
  } catch (error) {
    $("#status").textContent = "请求失败";
    $("#answer").textContent = `未执行任何真实操作：${error.message}`;
  }
});
