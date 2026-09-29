const $ = (selector) => document.querySelector(selector);
const historyKey = "commerce-agent-synthetic-history";
let lastRequest = null;

const setList = (element, items) => {
  element.replaceChildren();
  if (!items.length) { const item = document.createElement("li"); item.textContent = "暂无"; element.append(item); return; }
  items.forEach((text) => { const item = document.createElement("li"); item.textContent = text; element.append(item); });
};
const renderHistory = () => {
  const items = JSON.parse(localStorage.getItem(historyKey) || "[]");
  setList($("#history"), items.map((item) => `${item.status}：${item.summary}`));
};
$("#clear-history").addEventListener("click", () => { localStorage.removeItem(historyKey); renderHistory(); });
renderHistory();

const presets = {
  product: { message: "charger" },
  order: { message: "order ORD-10023 tracking 4821", orderId: "ORD-10023", suffix: "4821" },
  handoff: { message: "create a human support ticket", key: "demo-ticket-001" },
};
const errorMessage = (status, detail) => ({
  401: "身份验证未通过：请提供有效的合成 Bearer Token。",
  403: "当前合成角色没有执行此查询的权限。",
  409: "相同幂等请求正在处理，请稍后重试。",
  422: "输入校验未通过：请检查会话 ID、订单信息和幂等键格式。",
  429: "请求过于频繁，请稍后再试。",
}[status] || "请求未完成。") + (detail ? ` ${detail}` : "");
const renderGroup = (id, data, prefix) => setList($(id), Object.entries(data).filter(([key]) => key.startsWith(prefix)).map(([key, value]) => `${key.slice(prefix.length)}：${value}`));
const refreshMetrics = async () => {
  const response = await fetch("/metrics");
  const metrics = await response.json();
  $("#metrics").textContent = `请求 ${metrics.chat_requests}｜完成 ${metrics.completed}｜人工接管 ${metrics.handoffs}｜工具/请求 ${metrics.tool_calls_per_chat}`;
  renderGroup("#tool-metrics", metrics, "tool:"); renderGroup("#handoff-metrics", metrics, "handoff:"); renderGroup("#failure-metrics", metrics, "failure:");
  setList($("#recent-handoffs"), metrics.recent_handoffs || []);
  const points = metrics.metric_snapshots || [];
  $("#metric-trend").textContent = points.length ? `时间快照：${points.map((point) => `${point.bucket} 请求 ${point.chat_requests} / 完成 ${point.completed} / 接管 ${point.handoffs}`).join("；")}` : "尚无时间快照";
};
$("#refresh-metrics").addEventListener("click", refreshMetrics); refreshMetrics();

const renderDetails = (data) => {
  const ticket = (data.answer || "").match(/SIM-TKT-\d+/)?.[0];
  const order = (data.answer || "").match(/ORD-\d+/)?.[0];
  $("#detail-card").textContent = ticket ? `模拟工单：${ticket}\n状态：${data.status}\n仅供人工接管处理，不会执行真实退款、取消或地址修改。` : order ? `模拟订单：${order}\n状态：${data.status}\n数据仅来自本项目合成种子。` : `本次状态：${data.status}\n未识别出订单或工单编号。`;
};
const sendRequest = async (request) => {
  $("#status").textContent = "查询中";
  $("#retry").hidden = true;
  try {
    const response = await fetch("/api/v1/chat", { method: "POST", headers: request.headers, body: JSON.stringify(request.body) });
    const data = await response.json();
    if (!response.ok) throw new Error(errorMessage(response.status, data.detail));
    $("#status").textContent = data.status;
    $("#answer").textContent = data.answer;
    $("#trace").textContent = JSON.stringify({ tools: data.tool_result_summary, handoff: data.handoff, trace: data.trace }, null, 2);
    renderDetails(data);
    const items = JSON.parse(localStorage.getItem(historyKey) || "[]");
    localStorage.setItem(historyKey, JSON.stringify([{ status: data.status, summary: data.answer.slice(0, 80) }, ...items].slice(0, 10)));
    renderHistory(); refreshMetrics();
  } catch (error) {
    $("#status").textContent = "请求失败";
    $("#answer").textContent = `未执行任何真实操作：${error.message}`;
    $("#detail-card").textContent = "可恢复操作：检查输入、认证或限流提示后，可重试同一安全查询。未执行真实业务操作。";
    $("#retry").hidden = false;
  }
};
$("#retry").addEventListener("click", () => { if (lastRequest) sendRequest(lastRequest); });
document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => {
  const preset = presets[button.dataset.preset]; $("#message").value = preset.message; $("#order-id").value = preset.orderId || ""; $("#identity-suffix").value = preset.suffix || ""; $("#idempotency-key").value = preset.key || "";
}));
document.addEventListener("keydown", (event) => { if (!event.altKey || event.ctrlKey || event.metaKey) return; const preset = { "1": "product", "2": "order", "3": "handoff" }[event.key]; if (preset) { event.preventDefault(); document.querySelector(`[data-preset="${preset}"]`).click(); $("#message").focus(); } });
$("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault(); const slots = {}; if ($("#order-id").value.trim()) slots.order_id = $("#order-id").value.trim(); if ($("#identity-suffix").value.trim()) slots.identity_suffix = $("#identity-suffix").value.trim();
  const body = { thread_id: `web-${crypto.randomUUID()}`, message: $("#message").value.trim(), slots }; if ($("#idempotency-key").value.trim()) body.idempotency_key = $("#idempotency-key").value.trim();
  const headers = { "Content-Type": "application/json" }; if ($("#token").value.trim()) headers.Authorization = `Bearer ${$("#token").value.trim()}`;
  lastRequest = { body, headers }; sendRequest(lastRequest);
});
