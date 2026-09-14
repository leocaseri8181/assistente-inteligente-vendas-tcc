const tenantId = "demo";
const pageSize = 20;
let offset = 0;
let currentTotal = 0;
let optionsLoaded = false;
let authMode = "login";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const compactMoney = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const percent = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 });
const monthLabel = new Intl.DateTimeFormat("pt-BR", { month: "short", timeZone: "UTC" });
const dateLabel = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });

const $ = (selector) => document.querySelector(selector);
const statusElement = $("#app-status");

function safe(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

async function request(path, params = {}) {
  const url = new URL(path, window.location.origin);
  Object.entries({ tenant_id: tenantId, ...params }).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) url.searchParams.set(key, value);
  });
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) showAuthGate();
    throw new Error(apiErrorMessage(body.detail, response.status));
  }
  return response.json();
}

function apiErrorMessage(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return detail[0].msg || `Falha HTTP ${status}`;
  if (detail && typeof detail.message === "string") {
    const firstError = Array.isArray(detail.errors) && detail.errors.length ? ` ${detail.errors[0]}` : "";
    return `${detail.message}${firstError}`;
  }
  return `Falha HTTP ${status}`;
}

async function authRequest(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(apiErrorMessage(body.detail, response.status));
  return body;
}

function setAuthMode(mode) {
  authMode = mode;
  const signup = mode === "signup";
  $("#login-tab").setAttribute("aria-selected", String(!signup));
  $("#signup-tab").setAttribute("aria-selected", String(signup));
  $("#company-field").hidden = !signup;
  $("#company-name").required = signup;
  $("#auth-password").autocomplete = signup ? "new-password" : "current-password";
  $("#auth-title").textContent = signup ? "Crie seu espaço comercial" : "Entre no painel comercial";
  $("#auth-description").textContent = signup
    ? "A primeira conta cria uma empresa e recebe o papel de responsável."
    : "Use sua conta para acessar os dados da sua empresa.";
  $("#auth-submit").textContent = signup ? "Criar conta com segurança" : "Entrar com segurança";
  $("#auth-status").textContent = "";
}

function showAuthGate() {
  const gate = $("#auth-gate");
  gate.hidden = false;
  $(".shell").inert = true;
  requestAnimationFrame(() => $("#auth-email").focus());
}

function hideAuthGate() {
  $("#auth-gate").hidden = true;
  $(".shell").inert = false;
}

function renderDataEnvironment(session) {
  const remoteData = session.data_backend === "supabase";
  const environment = $("#data-environment");
  environment.textContent = remoteData ? "Banco Supabase" : "Modo local";
  environment.classList.toggle("remote-ready", remoteData);
}

function renderSession(session) {
  const control = $("#user-control");
  renderDataEnvironment(session);
  if (!session.auth_enabled) {
    control.hidden = true;
    return;
  }
  control.hidden = false;
  $("#user-email").textContent = session.user?.email || "Usuário autenticado";
  $("#user-organization").textContent = session.membership?.organizations?.name || "Empresa em preparação";
}

async function loadSession() {
  const response = await fetch("/api/auth/session");
  if (!response.ok) throw new Error("Não foi possível verificar a sessão.");
  return response.json();
}

async function submitAuth(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!form.reportValidity()) return;
  const button = $("#auth-submit");
  const status = $("#auth-status");
  button.disabled = true;
  status.className = "auth-status";
  status.textContent = authMode === "signup" ? "Criando seu espaço protegido…" : "Verificando suas credenciais…";
  try {
    const payload = {
      email: $("#auth-email").value.trim(),
      password: $("#auth-password").value,
    };
    if (authMode === "signup") payload.company_name = $("#company-name").value.trim();
    const result = await authRequest(`/api/auth/${authMode}`, payload);
    if (result.confirmation_required) {
      setAuthMode("login");
      status.className = "auth-status success";
      status.textContent = "Cadastro recebido. Confirme o e-mail e depois entre com sua senha.";
      return;
    }
    const session = await loadSession();
    renderSession(session);
    hideAuthGate();
    optionsLoaded = false;
    await initialize();
  } catch (error) {
    status.className = "auth-status error";
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function trapAuthFocus(event) {
  if (event.key !== "Tab") return;
  const controls = [...$("#auth-gate").querySelectorAll("button:not(:disabled), input:not(:disabled)")]
    .filter((element) => !element.closest("[hidden]"));
  if (!controls.length) return;
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

async function logout() {
  $("#logout-button").disabled = true;
  try {
    await authRequest("/api/auth/logout", {});
  } finally {
    $("#logout-button").disabled = false;
    $("#user-control").hidden = true;
    showAuthGate();
  }
}

function periodParams() {
  return { date_from: $("#date-from").value, date_to: $("#date-to").value };
}

function setStatus(message = "", error = false) {
  statusElement.textContent = message;
  statusElement.classList.toggle("error", error);
}

function updateActiveNavigation() {
  const current = window.location.hash || "#overview";
  document.querySelectorAll(".nav-item").forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === current);
  });
}

function renderSummary(data) {
  const closed = data.closed_period;
  $("#snapshot-date").textContent = data.snapshot_date ? dateLabel.format(new Date(`${data.snapshot_date}T00:00:00Z`)) : "Sem data";
  $("#won-value").textContent = compactMoney.format(closed.won_value);
  $("#won-count").textContent = `${integer.format(closed.won_count)} negócios ganhos`;
  $("#win-rate").textContent = closed.win_rate === null ? "n.d." : percent.format(closed.win_rate);
  $("#cycle-days").textContent = closed.average_cycle_days === null ? "n.d." : `${integer.format(closed.average_cycle_days)} dias`;
  $("#average-won").textContent = closed.average_won_value === null ? "n.d." : compactMoney.format(closed.average_won_value);
  if (!$("#date-from").value) $("#date-from").value = data.period.date_from || "";
  if (!$("#date-to").value) $("#date-to").value = data.period.date_to || "";
  renderPipeline(data.pipeline_snapshot);
}

function renderPipeline(pipeline) {
  const entries = [
    ["prospecting", "Prospecção", pipeline.prospecting],
    ["engaging", "Engajamento", pipeline.engaging],
    ["won", "Ganhas", pipeline.won],
    ["lost", "Perdidas", pipeline.lost],
  ];
  $("#pipeline-total").textContent = `${integer.format(pipeline.total)} oportunidades`;
  $("#pipeline-track").innerHTML = entries.map(([key, label, value]) =>
    `<span class="pipeline-segment segment-${key}" style="width:${(value / pipeline.total) * 100}%" title="${safe(label)}: ${value}"></span>`
  ).join("");
  $("#pipeline-legend").innerHTML = entries.map(([key, label, value]) =>
    `<div><i class="segment-${key}"></i><span>${safe(label)}</span><strong>${integer.format(value)}</strong></div>`
  ).join("");
}

function renderTrend(rows) {
  const target = $("#trend-chart");
  if (!rows.length) {
    target.innerHTML = '<p class="empty-row">Nenhum fechamento no período selecionado.</p>';
    return;
  }
  const maximum = Math.max(...rows.flatMap((row) => [row.won_count, row.lost_count]), 1);
  target.innerHTML = rows.map((row) => {
    const label = monthLabel.format(new Date(`${row.month}-01T00:00:00Z`)).replace(".", "");
    return `<div class="trend-month" aria-label="${safe(label)}: ${row.won_count} ganhos e ${row.lost_count} perdas">
      <div class="bar-pair"><i class="bar won" style="height:${Math.max(2, row.won_count / maximum * 100)}%"></i><i class="bar lost" style="height:${Math.max(2, row.lost_count / maximum * 100)}%"></i></div>
      <small>${safe(label)}</small>
    </div>`;
  }).join("");
}

function renderProducts(rows) {
  const target = $("#product-rows");
  if (!rows.length) {
    target.innerHTML = '<tr><td colspan="3" class="empty-row">Nenhum produto com fechamento no período.</td></tr>';
    return;
  }
  target.innerHTML = rows.map((row) => `<tr>
    <td><strong>${safe(row.product)}</strong><br><small>${integer.format(row.closed_count)} encerrados</small></td>
    <td class="rate-cell">${percent.format(row.win_rate)}<div class="rate-track"><i style="width:${row.win_rate * 100}%"></i></div></td>
    <td>${money.format(row.won_value)}</td>
  </tr>`).join("");
}

function fillOptions(options) {
  if (optionsLoaded) return;
  $("#product-filter").insertAdjacentHTML("beforeend", options.products.map((value) => `<option value="${safe(value)}">${safe(value)}</option>`).join(""));
  $("#manager-filter").insertAdjacentHTML("beforeend", options.managers.map((value) => `<option value="${safe(value)}">${safe(value)}</option>`).join(""));
  optionsLoaded = true;
}

function reviewBadge(level) {
  const definitions = {
    review_now: ["Revisar agora", "review-now"],
    attention: ["Atenção", "attention"],
    routine: ["Rotina", "routine"],
  };
  const [label, className] = definitions[level] || definitions.routine;
  return `<span class="review-badge ${className}">${label}</span>`;
}

function renderOpportunities(data) {
  currentTotal = data.total;
  $("#opportunity-total").textContent = `${integer.format(data.total)} abertas`;
  const target = $("#opportunity-rows");
  if (!data.items.length) {
    target.innerHTML = '<tr><td colspan="5" class="empty-row">Nenhuma oportunidade corresponde aos filtros.</td></tr>';
  } else {
    target.innerHTML = data.items.map((item) => `<tr>
      <td>${reviewBadge(item.review_level)}</td>
      <td><strong>${safe(item.account || "Conta não informada")}</strong><small>${safe(item.opportunity_id)}</small></td>
      <td>${safe(item.product)}</td>
      <td><strong>${safe(item.sales_agent)}</strong><br><small>${safe(item.manager)}</small></td>
      <td>${safe(item.review_reason)}</td>
    </tr>`).join("");
  }
  const start = data.total ? data.offset + 1 : 0;
  const end = Math.min(data.offset + data.items.length, data.total);
  $("#page-label").textContent = `${integer.format(start)}–${integer.format(end)} de ${integer.format(data.total)}`;
  $("#previous-page").disabled = offset === 0;
  $("#next-page").disabled = offset + pageSize >= data.total;
}

function opportunityParams() {
  return {
    stage: $("#stage-filter").value,
    product: $("#product-filter").value,
    manager: $("#manager-filter").value,
    limit: pageSize,
    offset,
  };
}

async function loadAnalytics() {
  setStatus("Atualizando indicadores…");
  try {
    const params = periodParams();
    const [summary, trends, products] = await Promise.all([
      request("/api/summary", params), request("/api/trends", params), request("/api/products", params),
    ]);
    renderSummary(summary);
    renderTrend(trends);
    renderProducts(products);
    setStatus("");
  } catch (error) {
    setStatus(`Não foi possível carregar os indicadores: ${error.message}`, true);
  }
}

async function loadOpportunities() {
  setStatus("Atualizando oportunidades…");
  try {
    const data = await request("/api/opportunities", opportunityParams());
    renderOpportunities(data);
    setStatus("");
  } catch (error) {
    setStatus(`Não foi possível carregar as oportunidades: ${error.message}`, true);
  }
}

async function initialize() {
  setStatus("Carregando dados…");
  try {
    const [options] = await Promise.all([request("/api/options"), loadAnalytics(), loadOpportunities()]);
    fillOptions(options);
    setStatus("");
  } catch (error) {
    setStatus(`Não foi possível iniciar o painel: ${error.message}`, true);
  }
}

const importFields = ["accounts", "products", "sales_teams", "sales_pipeline"];

function updateImportChecklist() {
  let complete = true;
  importFields.forEach((field) => {
    const input = $(`[name="${field}"]`);
    const filename = $(`[data-file-name="${field}"]`);
    const state = $(`[data-file-state="${field}"]`);
    const selected = input.files.length > 0;
    complete = complete && selected;
    filename.textContent = selected ? input.files[0].name : `${field}.csv`;
    state.textContent = selected ? "Pronto" : "Pendente";
    state.classList.toggle("ready", selected);
  });
  $("#import-button").disabled = !complete;
}

function showImportResult(message, kind = "") {
  const target = $("#import-result");
  target.textContent = message;
  target.className = `import-result ${kind}`.trim();
}

async function refreshAfterImport() {
  optionsLoaded = false;
  $("#product-filter").innerHTML = '<option value="">Todos os produtos</option>';
  $("#manager-filter").innerHTML = '<option value="">Todos os gestores</option>';
  const options = await request("/api/options");
  fillOptions(options);
  offset = 0;
  await Promise.all([loadAnalytics(), loadOpportunities()]);
}

async function submitImport(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = $("#import-button");
  button.disabled = true;
  button.textContent = "Validando lote…";
  showImportResult("Conferindo estrutura, tipos e referências dos quatro arquivos.", "working");
  const formData = new FormData(form);
  formData.append("tenant_id", tenantId);
  formData.append("tenant_name", "MavenTech Demo");
  try {
    const response = await fetch("/api/imports", { method: "POST", body: formData });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(apiErrorMessage(body.detail, response.status));
    const action = body.status === "skipped" ? "Lote já registrado; nenhuma duplicata foi criada." : `${integer.format(body.row_count)} oportunidades importadas com sucesso.`;
    showImportResult(action, "success");
    await refreshAfterImport();
  } catch (error) {
    showImportResult(error.message, "error");
  } finally {
    button.textContent = "Validar e importar";
    updateImportChecklist();
  }
}

$("#period-form").addEventListener("submit", (event) => { event.preventDefault(); loadAnalytics(); });
$("#opportunity-filters").addEventListener("change", () => { offset = 0; loadOpportunities(); });
$("#opportunity-filters").addEventListener("reset", () => { setTimeout(() => { offset = 0; loadOpportunities(); }, 0); });
$("#previous-page").addEventListener("click", () => { offset = Math.max(0, offset - pageSize); loadOpportunities(); });
$("#next-page").addEventListener("click", () => { if (offset + pageSize < currentTotal) { offset += pageSize; loadOpportunities(); } });
$("#import-form").addEventListener("change", updateImportChecklist);
$("#import-form").addEventListener("submit", submitImport);
$("#login-tab").addEventListener("click", () => setAuthMode("login"));
$("#signup-tab").addEventListener("click", () => setAuthMode("signup"));
$("#auth-form").addEventListener("submit", submitAuth);
$("#auth-gate").addEventListener("keydown", trapAuthFocus);
$("#logout-button").addEventListener("click", logout);
window.addEventListener("hashchange", updateActiveNavigation);

async function boot() {
  updateImportChecklist();
  updateActiveNavigation();
  try {
    const session = await loadSession();
    renderDataEnvironment(session);
    if (session.auth_enabled && !session.authenticated) {
      showAuthGate();
      setStatus("Entre para carregar os dados da sua empresa.");
      return;
    }
    renderSession(session);
    hideAuthGate();
    await initialize();
  } catch (error) {
    setStatus(error.message, true);
  }
}

boot().finally(() => {
  const target = window.location.hash ? document.querySelector(window.location.hash) : null;
  if (target) {
    const previousBehavior = document.documentElement.style.scrollBehavior;
    document.documentElement.style.scrollBehavior = "auto";
    target.scrollIntoView({ block: "start" });
    document.documentElement.style.scrollBehavior = previousBehavior;
  }
});
