/* 新闻事件因果图谱推理平台 —— 前端逻辑 */
(function () {
  "use strict";

  const GOLD = "#f5c518";
  const PALETTE = ["#2e7cf6", "#f5c518", "#14b8a6", "#f97316", "#a855f7", "#e11d48", "#64748b"];

  const TABS = {
    causal_tracing: {
      label: "因果追溯",
      hint: "回溯「什么导致了 X」或前瞻「X 会导致什么」，给出多条因果链。点击节点可生成问题。",
      nodeTpl: "是什么导致了{name}？",
      altTpl: "{name}会导致什么？",
    },
    situation_deduction: {
      label: "态势推演",
      hint: "从事件前向推演，输出完整的可能性树（所有分支 + 逐层概率）。",
      nodeTpl: "{name}可能引发哪些后续？",
      altTpl: null,
    },
    counterfactual: {
      label: "反事实推理",
      hint: "「假如 X 没发生会怎样」，级联消去连带节点，给出 PN / PS / PNS。",
      nodeTpl: "假如{name}没有发生会怎样？",
      altTpl: null,
    },
  };

  let chart = null;
  let currentView = null;
  let currentType = "causal_tracing";
  let highlightSet = new Set();

  const $ = (sel) => document.querySelector(sel);

  function esc(s) {
    return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  }
  function fmt(v) {
    if (Array.isArray(v)) return v.join("、");
    if (v && typeof v === "object") return JSON.stringify(v);
    return v == null ? "" : String(v);
  }

  async function api(path, body) {
    const opt = body
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : { method: "GET" };
    const res = await fetch(path, opt);
    return res.json();
  }

  /* ---------------- 数据集 ---------------- */
  async function loadDatasets() {
    const sel = $("#datasetSelect");
    const list = await api("/api/datasets");
    list.forEach((d) => {
      const o = document.createElement("option");
      o.value = d.id;
      o.textContent = `${d.title}  ·  ${d.node_count}节点/${d.edge_count}边`;
      sel.appendChild(o);
    });
  }

  async function onDatasetChange() {
    const id = $("#datasetSelect").value;
    if (!id) return;
    const data = await api("/api/load", { dataset_id: id });
    applyLoaded(data);
  }

  async function onUpload() {
    const file = $("#fileInput").files[0];
    if (!file) return;
    try {
      const graph = JSON.parse(await file.text());
      const data = await api("/api/upload", { graph });
      applyLoaded(data);
    } catch (e) {
      alert("导入失败：请确认是 CausalGraph 格式 JSON（含 nodes/edges，或 events/relations）。\n" + e.message);
    }
  }

  function applyLoaded(data) {
    if (data.error) { alert(data.error); return; }
    currentView = data.view;
    highlightSet.clear();
    renderGraph();
    renderAnalysis(data.analysis, data.meta);
    fillPresetChips(data.queries || []);
    $("#graphMeta").textContent =
      `${data.analysis.node_count} 节点 · ${data.analysis.edge_count} 边`;
    $("#graphHint").style.display = "none";
  }

  /* ---------------- 分析 ---------------- */
  function renderAnalysis(a, meta) {
    if (!a) return;
    const types = Object.entries(a.relation_types || {})
      .map(([k, v]) => `<span class="tag">${esc(k)}×${v}</span>`).join("");
    const hubs = (a.pagerank_top || [])
      .map((h) => `<span class="tag gold">${esc(h.name)}</span>`).join("");
    const roots = (a.roots || []).map((r) => esc(r.name)).join("、") || "—";
    const leaves = (a.leaves || []).map((l) => esc(l.name)).join("、") || "—";
    $("#analysis").innerHTML = `
      <div class="stat-grid">
        <div class="stat"><div class="k">节点</div><div class="v">${a.node_count}</div></div>
        <div class="stat"><div class="k">因果边</div><div class="v">${a.edge_count}</div></div>
        <div class="stat"><div class="k">密度</div><div class="v gold">${a.density}</div></div>
      </div>
      <div class="an-row"><b>根事件</b>（起因）：${roots}</div>
      <div class="an-row"><b>末端事件</b>（最终结果）：${leaves}</div>
      <div class="an-row"><b>关系类型</b>：${types || "—"}</div>
      <div class="an-row"><b>关键枢纽</b>（PageRank Top3）：${hubs || "—"}</div>
    `;
    if (meta && meta.source_url) {
      $("#graphMeta").title = meta.source_url;
    }
  }

  /* ---------------- 图谱渲染 ---------------- */
  function ensureChart() {
    if (chart) return chart;
    if (typeof echarts === "undefined") {
      $("#graphHint").style.display = "block";
      $("#graphHint").textContent = "ECharts 未能加载（CDN 不可达）。请联网后刷新，或把 echarts.min.js 放到 web/static/vendor/ 下。";
      return null;
    }
    chart = echarts.init($("#graph"));
    window.addEventListener("resize", () => chart && chart.resize());
    chart.on("click", (p) => {
      if (p.dataType === "node" && p.data) {
        const tpl = TABS[currentType].nodeTpl.replace("{name}", p.data.name);
        $("#questionInput").value = tpl;
      }
    });
    return chart;
  }

  function buildOption(view) {
    const catColor = {};
    view.categories.forEach((c, i) => (catColor[c.name] = PALETTE[i % PALETTE.length]));
    const nodes = view.nodes.map((n) => ({
      ...n,
      itemStyle: highlightSet.has(n.id)
        ? { borderColor: GOLD, borderWidth: 3, shadowBlur: 14, shadowColor: GOLD }
        : { borderColor: "rgba(255,255,255,.55)", borderWidth: 1 },
    }));
    const links = view.links.map((l) => ({
      ...l,
      lineStyle: highlightSet.has(l.rid)
        ? { color: GOLD, width: 4, opacity: 1, curveness: 0.08 }
        : { color: "#3d5a80", width: 1.2, opacity: 0.7, curveness: 0.08 },
    }));
    return {
      backgroundColor: "transparent",
      tooltip: {
        confine: true,
        formatter(p) {
          if (p.dataType === "edge") {
            const d = p.data;
            const ev = (d.evidence && d.evidence.length) ? d.evidence.join("；") : "";
            return `<b>${esc(d.relation_type)}</b> · 置信度 ${d.confidence ?? "—"}<br/>${esc(ev)}`;
          }
          const d = p.data;
          return `<b>${esc(d.name)}</b><br/>类型：${esc(d.event_type || "—")}<br/>置信度：${d.confidence ?? "—"}`;
        },
      },
      legend: [{
        data: view.categories.map((c) => c.name),
        textStyle: { color: "#93aed6" },
        top: 6, left: "center",
      }],
      series: [{
        type: "graph",
        layout: "force",
        data: nodes,
        links: links,
        categories: view.categories.map((c, i) => ({
          name: c.name,
          itemStyle: { color: PALETTE[i % PALETTE.length] },
        })),
        roam: true,
        draggable: true,
        label: { show: true, position: "right", color: "#e9f1fc", fontSize: 11, formatter: "{b}" },
        force: { repulsion: 260, edgeLength: [70, 160], gravity: 0.08 },
        edgeSymbol: ["none", "arrow"],
        edgeSymbolSize: 7,
        lineStyle: { color: "#3d5a80", width: 1.2, curveness: 0.08 },
        emphasis: { focus: "adjacency", lineStyle: { width: 3 } },
      }],
    };
  }

  function renderGraph() {
    if (!currentView) return;
    const c = ensureChart();
    if (!c) return;
    c.setOption(buildOption(currentView), true);
  }

  function highlightChain(chain) {
    highlightSet = new Set((chain || []).filter(Boolean));
    renderGraph();
  }

  /* ---------------- 操作与结果 ---------------- */
  function selectTab(type) {
    currentType = type;
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.dataset.type === type));
    $("#tabHint").textContent = TABS[type].hint;
    fillPresetChips(currentQueries || []);
  }

  let currentQueries = [];
  function fillPresetChips(queries) {
    currentQueries = queries;
    const box = $("#presetChips");
    box.innerHTML = "";
    const matched = queries.filter((q) => q.question_type === currentType);
    if (!matched.length) return;
    matched.forEach((q) => {
      const s = document.createElement("span");
      s.className = "chip";
      s.textContent = q.question;
      s.title = q.question;
      s.onclick = () => {
        $("#questionInput").value = q.question;
        runQuery();
      };
      box.appendChild(s);
    });
  }

  async function runQuery() {
    const question = $("#questionInput").value.trim();
    if (!question) { alert("请输入问题，或点击节点/预设问题生成。"); return; }
    const btn = $("#runBtn");
    btn.disabled = true; btn.textContent = "推理中…";
    try {
      const ans = await api("/api/query", { question, question_type: currentType });
      renderResult(ans);
    } finally {
      btn.disabled = false; btn.textContent = "运行推理";
    }
  }

  function renderResult(ans) {
    const badge = $("#confBadge");
    if (ans.error) {
      badge.textContent = "";
      $("#result").innerHTML = `<div class="err">${esc(ans.error)}</div>`;
      return;
    }
    const conf = ans.confidence ?? 0;
    badge.textContent = "置信度 " + Math.round(conf * 100) + "%";
    badge.style.color = conf >= 0.7 ? GOLD : "#93aed6";

    let html = `<div class="answer">${esc(ans.answer_text)}</div>`;
    if (ans.evidence_chain && ans.evidence_chain.length) {
      html += `<div class="meta-line"><b>证据链：</b></div>`;
      html += `<div class="ev-chain">` +
        ans.evidence_chain.map((e) => `<span class="ev">${esc(e)}</span>`).join("") + `</div>`;
    }
    const skip = new Set(["tree"]);
    const keys = Object.keys(ans.metadata || {}).filter((k) => !skip.has(k));
    if (keys.length) {
      html += `<div class="meta-line">` +
        keys.map((k) => `<span class="kv"><b>${esc(k)}</b> ${esc(fmt(ans.metadata[k]))}</span>`).join("") +
        `</div>`;
    }
    $("#result").innerHTML = html;
    highlightChain(ans.evidence_chain || []);
  }

  /* ---------------- 初始化 ---------------- */
  function bind() {
    $("#datasetSelect").addEventListener("change", onDatasetChange);
    $("#uploadBtn").addEventListener("click", () => $("#fileInput").click());
    $("#fileInput").addEventListener("change", onUpload);
    $("#analyzeBtn").addEventListener("click", () => { highlightSet.clear(); renderGraph(); });
    $("#resetHighlight").addEventListener("click", () => { highlightSet.clear(); renderGraph(); });
    $("#runBtn").addEventListener("click", runQuery);
    document.querySelectorAll(".tab").forEach((t) =>
      t.addEventListener("click", () => selectTab(t.dataset.type)));
    $("#questionInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) runQuery();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bind();
    loadDatasets();
    selectTab("causal_tracing");
    if (typeof echarts === "undefined") {
      $("#graphHint").style.display = "block";
      $("#graphHint").textContent = "ECharts 未能加载（CDN 不可达）。请联网后刷新。";
    }
  });
})();
