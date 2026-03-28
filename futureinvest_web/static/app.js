const form = document.getElementById("analysis-form");
const resultsGrid = document.getElementById("results-grid");
const resultsEmpty = document.getElementById("results-empty");
const errorBox = document.getElementById("error-box");
const statusPill = document.getElementById("status-pill");
const runMeta = document.getElementById("run-meta");

let metadata = null;

function fieldWrapper(label, innerHtml, className = "span-4") {
  return `
    <div class="field ${className}">
      <label>${label}</label>
      ${innerHtml}
    </div>
  `;
}

function selectHtml(id, options, selectedValue = "") {
  return `<select id="${id}" name="${id}">${options
    .map(
      (option) =>
        `<option value="${option.value}" ${
          String(option.value) === String(selectedValue) ? "selected" : ""
        }>${option.label}</option>`
    )
    .join("")}</select>`;
}

function setSelectOptions(select, values, selectedValue) {
  const fallbackValue = values.includes(selectedValue) ? selectedValue : values[0];
  select.innerHTML = values
    .map(
      (value) =>
        `<option value="${value}" ${String(value) === String(fallbackValue) ? "selected" : ""}>${value}</option>`
    )
    .join("");
}

function setStatus(mode, text) {
  statusPill.className = `status-pill ${mode}`;
  statusPill.textContent = text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function applyInlineFormatting(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdownish(content) {
  const lines = String(content || "").replace(/\r/g, "").split("\n");
  const html = [];
  let paragraph = [];
  let listMode = null;

  function closeList() {
    if (listMode === "ul") {
      html.push("</ul>");
    }
    if (listMode === "ol") {
      html.push("</ol>");
    }
    listMode = null;
  }

  function flushParagraph() {
    if (!paragraph.length) {
      return;
    }
    html.push(`<p>${applyInlineFormatting(paragraph.join(" "))}</p>`);
    paragraph = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      closeList();
      continue;
    }

    if (/^#{1,4}\s+/.test(line)) {
      flushParagraph();
      closeList();
      const title = line.replace(/^#{1,4}\s+/, "");
      html.push(`<h4>${applyInlineFormatting(title)}</h4>`);
      continue;
    }

    if (/^>\s+/.test(line)) {
      flushParagraph();
      closeList();
      html.push(`<blockquote>${applyInlineFormatting(line.replace(/^>\s+/, ""))}</blockquote>`);
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      flushParagraph();
      if (listMode !== "ul") {
        closeList();
        html.push("<ul>");
        listMode = "ul";
      }
      html.push(`<li>${applyInlineFormatting(line.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      flushParagraph();
      if (listMode !== "ol") {
        closeList();
        html.push("<ol>");
        listMode = "ol";
      }
      html.push(`<li>${applyInlineFormatting(line.replace(/^\d+\.\s+/, ""))}</li>`);
      continue;
    }

    if (listMode) {
      closeList();
    }
    paragraph.push(line);
  }

  flushParagraph();
  closeList();

  return html.join("");
}

function renderForm(meta) {
  const defaults = meta.defaults;
  const providerOptions = Object.entries(meta.providers).map(([key, provider]) => ({
    value: key,
    label: provider.label,
  }));
  const runModeOptions = meta.run_modes.map((mode) => ({
    value: mode.key,
    label: `${mode.label} - ${mode.description}`,
  }));
  const positionOptions = meta.position_importance.map((item) => ({
    value: item.key,
    label: item.label,
  }));
  const tokenOptions = meta.token_budget.map((item) => ({
    value: item.key,
    label: item.label,
  }));
  const depthOptions = meta.research_depth.map((item) => ({
    value: item.value,
    label: `${item.label} (${item.value} cycles)`,
  }));

  form.innerHTML = `
    ${fieldWrapper("Instrument", `<input id="ticker" name="ticker" value="${defaults.ticker}" />`, "span-3")}
    ${fieldWrapper(
      "Market Date",
      `<input id="analysis_date" name="analysis_date" type="date" value="${defaults.analysis_date}" />`,
      "span-3"
    )}
    ${fieldWrapper("Run Mode", selectHtml("run_mode", runModeOptions, defaults.run_mode), "span-6")}

    ${fieldWrapper(
      "Position Importance",
      selectHtml("position_importance", positionOptions, defaults.position_importance),
      "span-4"
    )}
    ${fieldWrapper("Token Budget", selectHtml("token_budget", tokenOptions, defaults.token_budget), "span-4")}
    ${fieldWrapper("Review Intensity", selectHtml("research_depth", depthOptions, defaults.research_depth), "span-4")}

    ${fieldWrapper("Model Backend", selectHtml("llm_provider", providerOptions, defaults.llm_provider), "span-4")}
    ${fieldWrapper("Backend URL", `<input id="backend_url" name="backend_url" value="${defaults.backend_url}" />`, "span-4")}
    ${fieldWrapper("Provider Setting", `<select id="provider_setting" name="provider_setting"></select>`, "span-4")}

    ${fieldWrapper("Scanning Engine", `<select id="quick_think_llm" name="quick_think_llm"></select>`, "span-6")}
    ${fieldWrapper("Judgment Engine", `<select id="deep_think_llm" name="deep_think_llm"></select>`, "span-6")}

    <div class="field span-12">
      <label>Signal Stack</label>
      <div class="capability-grid">
        ${meta.capabilities
          .map(
            (capability) => `
              <label class="capability-option">
                <div class="capability-option-top">
                  <div class="capability-copy">
                    <h3>${capability.label}</h3>
                    <span class="capability-tag">Research Engine</span>
                  </div>
                  <span class="capability-toggle">
                    <input
                      type="checkbox"
                      name="selected_analysts"
                      value="${capability.key}"
                      ${defaults.selected_analysts.includes(capability.key) ? "checked" : ""}
                    />
                    <span class="capability-toggle-ui" aria-hidden="true"></span>
                  </span>
                </div>
                <p>${capability.summary}</p>
              </label>
            `
          )
          .join("")}
      </div>
    </div>

    <div class="submit-row span-12">
      <div class="submit-hint">
        Launches the same lean/full Future Invest graph as the CLI, then renders the run as an institutional dossier.
      </div>
      <button class="launch-btn" id="launch-btn" type="submit">Launch Analysis</button>
    </div>
  `;

  bindDynamicControls(meta);
}

function updateProviderFields({ useDefaults = false } = {}) {
  const providerKey = document.getElementById("llm_provider").value;
  const provider = metadata.providers[providerKey];
  const backendUrl = document.getElementById("backend_url");
  const quickSelect = document.getElementById("quick_think_llm");
  const deepSelect = document.getElementById("deep_think_llm");
  const providerSetting = document.getElementById("provider_setting");

  backendUrl.value = provider.backend_url;

  const quickSelected =
    useDefaults && metadata.defaults.llm_provider === providerKey
      ? metadata.defaults.quick_think_llm
      : quickSelect.value;
  const deepSelected =
    useDefaults && metadata.defaults.llm_provider === providerKey
      ? metadata.defaults.deep_think_llm
      : deepSelect.value;

  setSelectOptions(quickSelect, provider.quick_models, quickSelected);
  setSelectOptions(deepSelect, provider.deep_models, deepSelected);

  if (provider.setting_field) {
    providerSetting.disabled = false;
    providerSetting.dataset.field = provider.setting_field;
    const selectedSetting =
      useDefaults && metadata.defaults.llm_provider === providerKey
        ? metadata.defaults[provider.setting_field]
        : providerSetting.value;
    const fallbackValue = provider.setting_options.includes(selectedSetting)
      ? selectedSetting
      : provider.setting_options[0];
    providerSetting.innerHTML = provider.setting_options
      .map(
        (option) =>
          `<option value="${option}" ${String(option) === String(fallbackValue) ? "selected" : ""}>${provider.setting_label}: ${option}</option>`
      )
      .join("");
  } else {
    providerSetting.disabled = true;
    providerSetting.dataset.field = "";
    providerSetting.innerHTML = `<option value="">No extra provider setting</option>`;
  }
}

function updateRunModeRecommendations() {
  const runModeKey = document.getElementById("run_mode").value;
  const runMode = metadata.run_modes.find((mode) => mode.key === runModeKey);
  if (!runMode) {
    return;
  }
  document.getElementById("position_importance").value = runMode.recommended_position_importance;
  document.getElementById("token_budget").value = runMode.recommended_token_budget;
  document.getElementById("research_depth").value = String(runMode.suggested_depth);

  const recommended = new Set(runMode.recommended_analysts || []);
  document
    .querySelectorAll('input[name="selected_analysts"]')
    .forEach((node) => {
      node.checked = recommended.has(node.value);
    });
}

function bindDynamicControls(meta) {
  metadata = meta;
  document.getElementById("llm_provider").addEventListener("change", () => updateProviderFields());
  document.getElementById("run_mode").addEventListener("change", updateRunModeRecommendations);
  updateProviderFields({ useDefaults: true });
  updateRunModeRecommendations();
}

function gatherPayload() {
  const providerSetting = document.getElementById("provider_setting");
  const settingField = providerSetting.dataset.field;
  const payload = {
    ticker: document.getElementById("ticker").value.trim(),
    analysis_date: document.getElementById("analysis_date").value,
    run_mode: document.getElementById("run_mode").value,
    position_importance: document.getElementById("position_importance").value,
    token_budget: document.getElementById("token_budget").value,
    research_depth: Number(document.getElementById("research_depth").value),
    llm_provider: document.getElementById("llm_provider").value,
    backend_url: document.getElementById("backend_url").value.trim(),
    quick_think_llm: document.getElementById("quick_think_llm").value,
    deep_think_llm: document.getElementById("deep_think_llm").value,
    selected_analysts: Array.from(
      document.querySelectorAll('input[name="selected_analysts"]:checked')
    ).map((node) => node.value),
  };
  if (settingField) {
    payload[settingField] = providerSetting.value;
  }
  return payload;
}

function buildResultCard(section) {
  return `
    <article class="result-card key-${section.key}">
      <div class="section-eyebrow">${section.key.replaceAll("_", " ")}</div>
      <h3>${escapeHtml(section.title)}</h3>
      <div class="dossier-body">${renderMarkdownish(section.content)}</div>
    </article>
  `;
}

function renderResults(data) {
  const sections = Array.isArray(data.sections) ? data.sections : [];
  resultsGrid.innerHTML = sections.map(buildResultCard).join("");
  resultsEmpty.classList.toggle("hidden", sections.length > 0);
  runMeta.innerHTML = `
    <span>${escapeHtml(data.ticker)}</span>
    <span>${escapeHtml(data.analysis_date)}</span>
    <span>${escapeHtml(data.institutional_loop_mode)} loop</span>
    <span>${escapeHtml(data.selected_analysts.length)} modules</span>
    <span>Elapsed ${escapeHtml(data.elapsed_seconds)}s</span>
    <span>Decision: ${escapeHtml(data.decision)}</span>
  `;
}

async function loadMetadata() {
  const response = await fetch("/api/meta");
  const meta = await response.json();
  renderForm(meta);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
  resultsGrid.innerHTML = "";
  runMeta.innerHTML = "";
  setStatus("running", "Running");
  resultsEmpty.classList.remove("hidden");

  const launchBtn = document.getElementById("launch-btn");
  launchBtn.disabled = true;

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(gatherPayload()),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Run failed.");
    }
    renderResults(data);
    setStatus("complete", "Complete");
  } catch (error) {
    setStatus("error", "Error");
    errorBox.textContent = error.message;
    errorBox.classList.remove("hidden");
  } finally {
    launchBtn.disabled = false;
  }
});

loadMetadata().catch((error) => {
  setStatus("error", "Error");
  errorBox.textContent = error.message;
  errorBox.classList.remove("hidden");
});
