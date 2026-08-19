(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const toast = (msg) => {
    const el = $("[data-toast]");
    if (!el) {
      window.alert(msg);
      return;
    }
    el.hidden = false;
    el.textContent = msg;
    window.clearTimeout(toast._t);
    toast._t = window.setTimeout(() => {
      el.hidden = true;
    }, 2400);
  };
  window.toast = toast;
  window.csrfToken = () => {
    const el = document.querySelector("[name=csrfmiddlewaretoken]");
    if (el && el.value) return el.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  };

  const root = $("[data-modal-root]");
  const closeAll = () => {
    if (!root) return;
    root.hidden = true;
    $$(".modal", root).forEach((m) => {
      m.hidden = true;
    });
    document.body.classList.remove("modal-open");
  };

  const openModal = (id) => {
    if (!root) return;
    const modal = document.getElementById(id);
    if (!modal) return;
    root.hidden = false;
    $$(".modal", root).forEach((m) => {
      m.hidden = true;
    });
    modal.hidden = false;
    document.body.classList.add("modal-open");
  };

  const showAuthPanel = (name) => {
    const card = $("[data-auth-card]");
    if (!card) return;
    $$("[data-auth-panel]", card).forEach((panel) => {
      panel.hidden = panel.getAttribute("data-auth-panel") !== name;
    });
  };

  const payloadEl = $("#review-payload");
  const payloadText = payloadEl ? payloadEl.textContent.trim() : "";

  const downloadText = (filename, text, mime) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const jsonToCsv = (raw) => {
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      return "key,value\n";
    }
    const skip = new Set(["line_items", "validation"]);
    const rows = [["key", "value"]];
    Object.entries(data).forEach(([k, v]) => {
      if (skip.has(k) || typeof v === "object") return;
      rows.push([k, v == null ? "" : String(v)]);
    });
    (data.line_items || []).forEach((item, i) => {
      rows.push([`line_${i + 1}_description`, item.description || ""]);
      rows.push([`line_${i + 1}_qty`, item.qty || ""]);
      rows.push([`line_${i + 1}_amount`, item.amount || ""]);
    });
    return rows.map((r) => r.map((c) => `"${String(c).replaceAll('"', '""')}"`).join(",")).join("\n");
  };

  const highlight = (key, opts = {}) => {
    $$("[data-field]").forEach((el) => el.classList.toggle("is-on", el.dataset.field === key));
    $$("[data-bbox]").forEach((el) => el.classList.toggle("is-on", el.dataset.bbox === key));
    if (opts.scroll === false) return;
    const field = $(`[data-field="${key}"]`);
    if (field) field.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };

  let lockedField = null;
  const firstLow = $("[data-field].is-low");

  const bindHighlight = () => {
    $$("[data-field]").forEach((el) => {
      el.addEventListener("mouseenter", () => highlight(el.dataset.field, { scroll: false }));
      el.addEventListener("mouseleave", () => lockedField && highlight(lockedField, { scroll: false }));
      el.addEventListener("click", () => {
        lockedField = el.dataset.field;
        highlight(lockedField);
      });
      el.addEventListener("focusin", () => {
        lockedField = el.dataset.field;
        highlight(lockedField, { scroll: false });
      });
    });
    $$("[data-bbox]").forEach((el) => {
      el.addEventListener("mouseenter", () => highlight(el.dataset.bbox, { scroll: false }));
      el.addEventListener("mouseleave", () => lockedField && highlight(lockedField, { scroll: false }));
      el.addEventListener("click", (e) => {
        e.preventDefault();
        lockedField = el.dataset.bbox;
        highlight(lockedField);
      });
    });
  };

  const ingest = $("[data-ingest]");
  if (ingest) {
    const steps = ["OCR Scanning…", "Vision LLM Extraction…", "Pydantic Schema Validation…", "Ready for Review"];
    const label = $("[data-ingest-step]");
    const fill = $("[data-ingest-fill]");
    let i = 0;
    const beat = 375;
    const tick = () => {
      if (label) label.textContent = steps[i];
      if (fill) fill.style.width = `${((i + 1) / steps.length) * 100}%`;
      $$("[data-ingest-stage]").forEach((el) => {
        el.classList.toggle("is-on", Number(el.dataset.ingestStage) <= i);
      });
      i += 1;
      if (i < steps.length) window.setTimeout(tick, beat);
      else {
        window.setTimeout(() => {
          ingest.hidden = true;
          bindHighlight();
          if (firstLow) {
            lockedField = firstLow.dataset.field;
            highlight(lockedField, { scroll: false });
          }
        }, beat);
      }
    };
    tick();
  } else {
    bindHighlight();
    if (firstLow) {
      lockedField = firstLow.dataset.field;
      highlight(lockedField, { scroll: false });
    }
  }

  $$("[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$("[data-view]").forEach((b) => b.classList.remove("is-on"));
      btn.classList.add("is-on");
      const view = btn.dataset.view;
      $$("[data-view-panel]").forEach((panel) => {
        panel.hidden = panel.getAttribute("data-view-panel") !== view;
      });
    });
  });

  const PRESETS = {
    invoice: [
      ["vendor", "string", true],
      ["invoice_no", "string", true],
      ["invoice_date", "date", true],
      ["po_number", "string", false],
      ["total", "currency", true],
    ],
    receipt: [
      ["merchant", "string", true],
      ["paid_at", "date", true],
      ["tax", "currency", true],
      ["total", "currency", true],
    ],
    bol: [
      ["shipper", "string", true],
      ["consignee", "string", true],
      ["pro_number", "string", true],
      ["weight_lbs", "number", true],
    ],
    blank: [],
  };

  const fieldTable = $("[data-field-table]");
  const renderFields = (rows) => {
    if (!fieldTable) return;
    fieldTable.innerHTML = rows
      .map(
        ([key, type, req]) => `<tr>
          <td>${key}</td>
          <td>${type}</td>
          <td>${req ? "Yes" : "No"}</td>
          <td><button class="link" type="button" data-remove-field>Remove</button></td>
        </tr>`
      )
      .join("");
  };

  const runBatch = () => {
    const card = $("[data-batch]");
    if (!card) return;
    const status = $("[data-batch-status]", card);
    const bar = $("[data-batch-bar]", card);
    const now = $("[data-batch-now]", card);
    const speed = $("[data-batch-speed]", card);
    const ok = $("[data-batch-ok]", card);
    const flag = $("[data-batch-flag]", card);
    const total = 50;
    let n = 0;
    speed.textContent = "1.2s/doc";
    const tick = () => {
      n += 1;
      const success = Math.max(0, n - 2);
      const flagged = Math.min(2, n);
      now.textContent = String(n);
      ok.textContent = String(success);
      flag.textContent = String(Math.min(flagged, 2));
      bar.style.width = `${(n / total) * 100}%`;
      status.textContent =
        n < total
          ? `Processing ${n} of ${total} files… Vision LLM + Pydantic worker`
          : `Done. ${total - 2} success, 2 flagged for review · avg 1.2s/doc`;
      if (n < total) window.setTimeout(tick, 70);
      else toast("Batch complete (UI). 2 documents need review.");
    };
    tick();
  };

  document.addEventListener("click", (e) => {
    const authShow = e.target.closest("[data-auth-show]");
    if (authShow) {
      e.preventDefault();
      showAuthPanel(authShow.getAttribute("data-auth-show"));
      return;
    }

    const openBtn = e.target.closest("[data-open]");
    if (openBtn) {
      e.preventDefault();
      openModal(openBtn.getAttribute("data-open"));
      return;
    }
    if (e.target.closest("[data-close-modal]")) {
      closeAll();
      return;
    }

    const dropzone = e.target.closest("[data-dropzone]");
    if (dropzone) {
      const input = $("[data-file-input]", dropzone);
      if (input) input.click();
    }

    if (e.target.closest("[data-download='json']")) {
      const name = ($("[data-review]")?.dataset.filename || "fieldline-extract") + ".json";
      downloadText(name.replace(/\.pdf/i, ""), payloadText || "{}", "application/json");
      toast("Validated JSON downloaded.");
      return;
    }
    if (e.target.closest("[data-download='csv']")) {
      const name = ($("[data-review]")?.dataset.filename || "fieldline-extract") + ".csv";
      downloadText(name.replace(/\.pdf/i, ""), jsonToCsv(payloadText), "text/csv");
      toast("CSV downloaded.");
      return;
    }
    if (e.target.closest("[data-copy-sql]")) {
      const sql = ($("#sql-payload")?.textContent || $("#sql-view")?.textContent || "").trim();
      if (sql && navigator.clipboard) {
        navigator.clipboard.writeText(sql).then(() => toast("PostgreSQL insert copied."));
      } else {
        toast("Copy this SQL from the SQL tab.");
      }
      return;
    }
    if (e.target.closest("[data-edit-inline]")) {
      const field = e.target.closest("[data-field]");
      const input = field && $("input", field);
      if (input) {
        input.focus();
        input.select();
      }
      return;
    }
    if (e.target.closest("[data-toggle-api]")) {
      const drawer = $("[data-api-drawer]");
      if (drawer) drawer.hidden = !drawer.hidden;
      return;
    }
    if (e.target.closest("[data-api-tab]")) {
      const tab = e.target.closest("[data-api-tab]").dataset.apiTab;
      $$("[data-api-tab]").forEach((b) => b.classList.toggle("is-on", b.dataset.apiTab === tab));
      $$("[data-api-panel]").forEach((p) => {
        p.hidden = p.getAttribute("data-api-panel") !== tab;
      });
      return;
    }
    if (e.target.closest("[data-copy-api]")) {
      const panel = $$("[data-api-panel]").find((p) => !p.hidden);
      const text = (panel?.textContent || "").trim();
      if (text && navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => toast("Snippet copied."));
      }
      return;
    }
    const quick = e.target.closest("[data-quick-field]");
    if (quick && fieldTable) {
      const map = {
        tax_id: ["tax_id", "string", true],
        gl_code: ["gl_code", "string", true],
        tracking_number: ["tracking_number", "string", false],
      };
      const row = map[quick.dataset.quickField];
      if (row) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${row[0]}</td><td>${row[1]}</td><td>${row[2] ? "Yes" : "No"}</td><td><button class="link" type="button" data-remove-field>Remove</button></td>`;
        fieldTable.append(tr);
        toast(`Added ${row[0]}.`);
      }
      return;
    }
    if (e.target.closest("[data-webhook-test]")) {
      toast("POST https://hooks.example.test/fieldline → 200 OK (UI)");
      closeAll();
      return;
    }
    if (e.target.closest("[data-run-batch]")) {
      runBatch();
      return;
    }
    if (e.target.closest("[data-approve-field]")) {
      const field = e.target.closest("[data-field]");
      if (!field) return;
      field.classList.remove("is-low");
      const badge = $(".conf-badge", field);
      if (badge) {
        badge.className = "conf-badge conf-ok";
        badge.textContent = "Approved";
      }
      const actions = $(".field-actions", field);
      if (actions) actions.remove();
      field.querySelector("[data-edit-inline]")?.remove();
      toast("Field approved (UI).");
      return;
    }

    const load = e.target.closest("[data-load-schema]");
    if (load && fieldTable) {
      $$("[data-load-schema]").forEach((c) => c.classList.remove("is-active"));
      load.classList.add("is-active");
      const key = load.dataset.loadSchema;
      const names = { invoice: "Invoice", receipt: "Receipt", bol: "Bill of lading", blank: "Custom schema" };
      const nameInput = $("[data-schema-name]");
      if (nameInput) nameInput.value = names[key] || "Custom schema";
      renderFields(PRESETS[key] || []);
      toast("Schema loaded (UI).");
      return;
    }
    if (e.target.closest("[data-add-field]") && fieldTable) {
      const key = ($("[data-new-key]")?.value || "").trim().replace(/\s+/g, "_");
      const type = $("[data-new-type]")?.value || "string";
      const req = Boolean($("[data-new-required]")?.checked);
      if (!key) {
        toast("Give the field a name, e.g. tax_id.");
        return;
      }
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${key}</td><td>${type}</td><td>${req ? "Yes" : "No"}</td><td><button class="link" type="button" data-remove-field>Remove</button></td>`;
      fieldTable.append(tr);
      const input = $("[data-new-key]");
      if (input) input.value = "";
      toast(`Added ${key} (${type}).`);
      return;
    }
    if (e.target.closest("[data-remove-field]")) {
      e.target.closest("tr")?.remove();
      return;
    }

    const actions = [
      ["data-upload-start", "Extraction started (UI). Hook your pipeline here."],
      ["data-confirm-approve", "Approved (UI). Payload ready for PostgreSQL."],
      ["data-confirm-reject", "Moved to exceptions (UI)."],
      ["data-confirm-export", "Export queued (UI)."],
      ["data-apply-filters", "Filters applied (UI)."],
      ["data-save-schema", "Schema saved (UI). Worker will use this field map."],
      ["data-send-invite", "Invite sent (UI)."],
      ["data-save-webhook", "Webhook saved (UI)."],
      ["data-confirm-retry", "Retry queued (UI)."],
    ];
    for (const [attr, msg] of actions) {
      if (e.target.closest(`[${attr}]`)) {
        closeAll();
        toast(msg);
        if (attr === "data-upload-start") runBatch();
        return;
      }
    }

    if (e.target.closest("[data-send-reset]")) {
      showAuthPanel("sent");
      toast("Reset link sent (UI).");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    closeAll();
    const drawer = $("[data-api-drawer]");
    if (drawer) drawer.hidden = true;
  });

  const tabs = $$(".tabs button");
  const rows = $$("[data-inbox-table] tbody tr");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((b) => b.classList.remove("is-on"));
      btn.classList.add("is-on");
      const f = btn.dataset.filter;
      rows.forEach((row) => {
        row.hidden = !(f === "all" || row.dataset.status === f);
      });
    });
  });

  const search = $("[data-inbox-search]");
  if (search) {
    search.addEventListener("input", () => {
      const q = search.value.toLowerCase();
      rows.forEach((row) => {
        row.style.display = (row.dataset.name || "").includes(q) ? "" : "none";
      });
    });
  }

  const logoutLink = $("[data-logout]");
  if (logoutLink) {
    logoutLink.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const res = await fetch(logoutLink.getAttribute("data-logout"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken(),
          },
        });
        const result = await res.json();
        window.location = (result.data && result.data.redirect) || logoutLink.href;
      } catch (err) {
        window.location = logoutLink.href;
      }
    });
  }
})();
