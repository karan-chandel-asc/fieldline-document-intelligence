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
  let payloadText = payloadEl ? payloadEl.textContent.trim() : "";

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  const apiUrl = (template, id) => (template || "").replace("/0/", `/${id}/`);

  const labelize = (key) =>
    String(key || "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

  const currentDocumentId = () =>
    $("[data-review]")?.dataset.documentId ||
    $("#modal-retry")?.dataset.documentId ||
    $("#modal-schema-edit")?.dataset.documentId ||
    "";

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
  const liveRoot = $("[data-review]");
  const isLiveReview = Boolean(liveRoot && liveRoot.dataset.documentId);

  if (ingest && !ingest.hidden) {
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
  } else if (!isLiveReview) {
    bindHighlight();
    if (firstLow) {
      lockedField = firstLow.dataset.field;
      highlight(lockedField, { scroll: false });
    }
  }

  const collectReviewData = () => {
    let data = {};
    try {
      data = JSON.parse(payloadText || "{}");
    } catch {
      data = {};
    }
    ["document_id", "filename", "schema", "status"].forEach((key) => {
      delete data[key];
    });
    $$("[data-fields] [name]").forEach((input) => {
      if (!input.name) return;
      data[input.name] = input.value;
    });
    const rows = $$("[data-line-body] tr");
    if (rows.length) {
      data.line_items = rows.map((tr) => {
        const inputs = $$("input", tr);
        return {
          description: inputs[0]?.value || "",
          qty: inputs[1]?.value || "",
          amount: inputs[2]?.value || "",
        };
      });
    }
    return data;
  };

  const reviewPayloadText = () => {
    if (!liveRoot || !liveRoot.dataset.documentId) return payloadText || "{}";
    let base = {};
    try {
      base = JSON.parse(payloadText || "{}");
    } catch {
      base = {};
    }
    return JSON.stringify({ ...base, ...collectReviewData() }, null, 2);
  };

  const setPendingDocument = (el) => {
    const row = el?.closest("tr");
    const id = el?.dataset.documentId || row?.dataset.docId || "";
    const fileUrl = el?.dataset.fileUrl || row?.dataset.fileUrl || "";
    ["modal-retry", "modal-schema-edit", "modal-preview", "modal-reject"].forEach((modalId) => {
      const modal = document.getElementById(modalId);
      if (!modal) return;
      modal.dataset.documentId = id;
      if (fileUrl) modal.dataset.fileUrl = fileUrl;
    });
    return { id, fileUrl };
  };

  const detailUrlFor = (id) =>
    apiUrl($("#modal-retry")?.dataset.detailUrl || liveRoot?.dataset.detailUrl || "", id);
  const retryUrlFor = (id) =>
    apiUrl($("#modal-retry")?.dataset.retryUrl || liveRoot?.dataset.retryUrl || "", id);

  const patchDocument = async (id, body) => {
    const url = detailUrlFor(id);
    if (!url) throw new Error("Document API is missing");
    const res = await fetch(url, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.csrfToken(),
      },
      body: JSON.stringify(body),
    });
    const result = await res.json();
    if (!res.ok || !result.success) throw new Error(result.message || "Could not update document");
    return result;
  };

  const renderLiveReview = (doc) => {
    if (!liveRoot) return;
    liveRoot.dataset.filename = doc.original_name || "document.pdf";
    const heading = $("[data-review-heading]");
    const crumb = $("[data-review-crumb]");
    const pages = $("[data-review-pages]");
    const schemaLink = $("[data-review-schema]");
    if (heading) heading.textContent = doc.original_name || "Document";
    if (crumb) crumb.textContent = doc.schema_name ? `Human review · ${doc.schema_name}` : "Human review";
    if (pages) pages.textContent = doc.status ? doc.status.replaceAll("_", " ") : "PDF";
    if (schemaLink) schemaLink.textContent = doc.schema_id ? `${doc.schema_name} schema` : "No schema";

    const frame = $("[data-pdf-frame]");
    const missing = $("[data-pdf-missing]");
    if (frame) {
      if (doc.file_url) {
        frame.src = doc.file_url;
        frame.hidden = false;
        if (missing) missing.hidden = true;
      } else {
        frame.removeAttribute("src");
        frame.hidden = true;
        if (missing) missing.hidden = false;
      }
    }

    const hint = $("[data-review-hint]");
    if (hint) hint.textContent = "Edit extracted fields, then approve or reject.";
    const errorEl = $("[data-review-error]");
    if (errorEl) {
      errorEl.textContent = doc.error_message || "";
      errorEl.hidden = !doc.error_message;
    }

    const extracted = doc.extracted_data && typeof doc.extracted_data === "object" ? doc.extracted_data : {};
    const schemaFields = Array.isArray(doc.schema_fields) ? doc.schema_fields : [];
    const keys = [];
    schemaFields.forEach((field) => {
      const key = field.field_name;
      if (key && !keys.includes(key)) keys.push(key);
    });
    Object.keys(extracted).forEach((key) => {
      if (key === "line_items" || typeof extracted[key] === "object") return;
      if (!keys.includes(key)) keys.push(key);
    });
    const required = new Set(
      schemaFields.filter((field) => field.field_required).map((field) => field.field_name)
    );
    const fieldsEl = $("[data-fields]");
    if (fieldsEl) {
      fieldsEl.innerHTML = keys
        .map((key) => {
          const value = extracted[key];
          const empty = value === null || value === undefined || value === "";
          const low = required.has(key) && empty;
          return `<div class="field${low ? " is-low" : ""}" data-field="${escapeHtml(key)}">
            <span class="field-head">${escapeHtml(labelize(key))}</span>
            <input name="${escapeHtml(key)}" value="${escapeHtml(value == null ? "" : value)}" />
            <div class="field-meta">
              <span class="conf-badge ${low ? "conf-warn" : "conf-ok"}">${low ? "Review needed" : "Extracted"}</span>
            </div>
          </div>`;
        })
        .join("");
    }

    const validations = $("[data-validations]");
    if (validations) {
      const missingRequired = keys.filter((key) => required.has(key) && (extracted[key] == null || extracted[key] === ""));
      const items = [];
      if (doc.error_message) items.push({ ok: false, title: doc.error_message });
      if (missingRequired.length) {
        items.push({
          ok: false,
          title: `${missingRequired.length} required field${missingRequired.length === 1 ? "" : "s"} empty`,
        });
      } else items.push({ ok: true, title: "Required fields present" });
      if (doc.status === "approved") items.push({ ok: true, title: "Approved" });
      validations.innerHTML = items
        .map((rule) => `<span class="${rule.ok ? "is-ok" : "is-bad"}">${rule.ok ? "✔" : "!"} ${escapeHtml(rule.title)}</span>`)
        .join("");
    }

    const lineWrap = $("[data-line-items]");
    const lineBody = $("[data-line-body]");
    const lineItems = Array.isArray(extracted.line_items) ? extracted.line_items : [];
    if (lineWrap && lineBody) {
      if (lineItems.length) {
        lineWrap.hidden = false;
        lineBody.innerHTML = lineItems
          .map((item) => {
            const row = item && typeof item === "object" ? item : { description: item };
            return `<tr>
              <td><input value="${escapeHtml(row.description || row[0] || "")}" /></td>
              <td><input value="${escapeHtml(row.qty || row[1] || "")}" /></td>
              <td><input value="${escapeHtml(row.amount || row[2] || "")}" /></td>
            </tr>`;
          })
          .join("");
      } else {
        lineWrap.hidden = true;
        lineBody.innerHTML = "";
      }
    }

    payloadText = JSON.stringify(doc.payload || extracted, null, 2);
    if (payloadEl) payloadEl.textContent = payloadText;
    const jsonView = $("[data-json-view]");
    if (jsonView) jsonView.textContent = payloadText;
    bindHighlight();
  };

  const loadLiveReview = async () => {
    if (!isLiveReview) return;
    try {
      const res = await fetch(detailUrlFor(liveRoot.dataset.documentId));
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load document");
        return;
      }
      renderLiveReview(result.data || {});
    } catch (err) {
      toast("Could not load document");
    }
  };

  window.__approveDocument = async () => {
    const id = liveRoot?.dataset.documentId;
    if (!id) {
      closeAll();
      toast("Approved (UI). Payload ready to export.");
      return;
    }
    try {
      await patchDocument(id, { extracted_data: collectReviewData(), status: "approved" });
      const dest = $("[data-approve-dest]")?.value || "json";
      closeAll();
      if (dest === "csv") {
        downloadText(
          (liveRoot.dataset.filename || "extract").replace(/\.pdf/i, "") + ".csv",
          jsonToCsv(reviewPayloadText()),
          "text/csv"
        );
      } else if (dest === "webhook") {
        if (typeof window.__testWebhook === "function") await window.__testWebhook();
        toast("Approved. Webhook test sent.");
        window.setTimeout(() => {
          window.location = liveRoot.dataset.inboxUrl || "/app/inbox/";
        }, 400);
        return;
      } else {
        downloadText(
          (liveRoot.dataset.filename || "extract").replace(/\.pdf/i, "") + ".json",
          reviewPayloadText(),
          "application/json"
        );
      }
      toast("Approved and exported.");
      window.setTimeout(() => {
        window.location = liveRoot.dataset.inboxUrl || "/app/inbox/";
      }, 400);
    } catch (err) {
      toast(err.message || "Could not approve");
    }
  };

  window.__rejectDocument = async () => {
    const id = liveRoot?.dataset.documentId || $("#modal-reject")?.dataset.documentId;
    if (!id) {
      closeAll();
      toast("Moved to exceptions (UI).");
      return;
    }
    const reason = $("[data-reject-reason]")?.value || "Rejected";
    const note = ($("[data-reject-note]")?.value || "").trim();
    try {
      await patchDocument(id, {
        status: "failed",
        error_message: note ? `${reason}: ${note}` : reason,
      });
      closeAll();
      toast("Sent to exceptions.");
      window.location = liveRoot?.dataset.exceptionsUrl || "/app/exceptions/";
    } catch (err) {
      toast(err.message || "Could not reject");
    }
  };

  window.__retryDocument = async () => {
    const id = $("#modal-retry")?.dataset.documentId || liveRoot?.dataset.documentId;
    if (!id) {
      closeAll();
      toast("Retry queued (UI).");
      return;
    }
    try {
      const res = await fetch(retryUrlFor(id), {
        method: "POST",
        headers: { "X-CSRFToken": window.csrfToken() },
      });
      const result = await res.json();
      closeAll();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not retry");
        return;
      }
      toast(result.message || "Retry queued");
      if (typeof window.__reloadInbox === "function") window.__reloadInbox();
    } catch (err) {
      toast("Could not retry. Start Redis and Celery.");
    }
  };

  window.__changeDocumentSchema = async () => {
    const id = $("#modal-schema-edit")?.dataset.documentId;
    const schemaId = $("[data-reassign-schema]")?.value;
    if (!id || !schemaId) {
      toast("Select a schema");
      return;
    }
    try {
      await patchDocument(id, { schema_id: Number(schemaId) });
      const res = await fetch(retryUrlFor(id), {
        method: "POST",
        headers: { "X-CSRFToken": window.csrfToken() },
      });
      const result = await res.json();
      closeAll();
      if (!res.ok || !result.success) {
        toast(result.message || "Schema saved, but retry failed");
        return;
      }
      toast("Schema saved. Retry queued.");
      if (typeof window.__reloadInbox === "function") window.__reloadInbox();
    } catch (err) {
      toast(err.message || "Could not change schema");
    }
  };

  if (isLiveReview) loadLiveReview();

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
      ["total", "number", true],
    ],
    receipt: [
      ["merchant", "string", true],
      ["paid_at", "date", true],
      ["tax", "number", true],
      ["total", "number", true],
    ],
    bol: [
      ["shipper", "string", true],
      ["consignee", "string", true],
      ["pro_number", "string", true],
      ["weight_lbs", "number", true],
    ],
    blank: [],
  };
  const PRESET_META = {
    invoice: { name: "Invoice", description: "Vendor, dates, PO, currency, totals, line items." },
    receipt: { name: "Receipt", description: "Merchant, timestamp, tax, payment method." },
    bol: { name: "Bill of lading", description: "Shipper, consignee, PRO, weight." },
    blank: { name: "Custom schema", description: "Start from zero — add Tax ID, parcel number, ICD codes…" },
  };
  const FIELD_TYPES = new Set(["string", "number", "boolean", "date", "time", "datetime", "array"]);

  const fieldTable = $("[data-field-table]");
  const renderFields = (rows) => {
    if (!fieldTable) return;
    fieldTable.innerHTML = rows
      .map(
        ([key, type, req]) => `<tr>
          <td>${key}</td>
          <td>${FIELD_TYPES.has(type) ? type : "string"}</td>
          <td>${req ? "Yes" : "No"}</td>
          <td><button class="link" type="button" data-remove-field>Remove</button></td>
        </tr>`
      )
      .join("");
  };

  const schemaPage = $("[data-schema-page]");
  const schemaGrid = $("[data-schema-grid]");
  const schemaCache = new Map();
  const collectSchemaPayload = () => ({
    schema_name: ($("[data-schema-name]")?.value || "").trim(),
    schema_description: ($("[data-schema-description]")?.value || "").trim(),
    schema_fields: [...(fieldTable?.querySelectorAll("tr") || [])].map((tr) => {
      const cells = [...tr.children];
      const type = (cells[1]?.textContent || "string").trim();
      return {
        field_name: (cells[0]?.textContent || "").trim(),
        field_type: FIELD_TYPES.has(type) ? type : "string",
        field_required: (cells[2]?.textContent || "").trim().toLowerCase() === "yes",
      };
    }).filter((field) => field.field_name),
  });
  const schemaCard = (schema) => {
    const count = (schema.schema_fields || []).length;
    const card = document.createElement("article");
    card.className = "schema-card";
    card.dataset.savedSchema = String(schema.id);
    card.innerHTML = `<div class="schema-card-head"><h2></h2><button type="button" class="link" data-delete-schema>Delete</button></div><p></p><span class="logo-kicker"></span>`;
    card.querySelector("h2").textContent = schema.schema_name || "Untitled";
    card.querySelector("p").textContent = schema.schema_description || "No description provided";
    card.querySelector(".logo-kicker").textContent = `${count} field${count === 1 ? "" : "s"}`;
    return card;
  };
  const applySchema = (schema) => {
    const nameInput = $("[data-schema-name]");
    const descInput = $("[data-schema-description]");
    if (nameInput) nameInput.value = schema.schema_name || "Untitled";
    if (descInput) descInput.value = schema.schema_description || "";
    renderFields((schema.schema_fields || []).map((field) => [
      field.field_name,
      field.field_type,
      field.field_required,
    ]));
  };
  const setActiveSchemaCard = (id) => {
    $$("[data-saved-schema]").forEach((card) => {
      card.classList.toggle("is-active", String(card.dataset.savedSchema) === String(id || ""));
    });
    $$("[data-load-schema]").forEach((card) => card.classList.remove("is-active"));
  };

  if (schemaPage && schemaGrid) {
    const listUrl = schemaPage.dataset.listUrl;
    const saveUrl = schemaPage.dataset.saveUrl;
    const deleteUrlTemplate = schemaPage.dataset.deleteUrl;
    const emptyEl = $("[data-schema-empty]");
    const loadingEl = $("[data-schema-loading]");
    const sentinel = $("[data-schema-sentinel]");
    const listRoot = $("[data-schema-list]");
    let page = 1;
    let hasMore = true;
    let loading = false;

    const loadSchemas = async () => {
      if (!listUrl || loading || !hasMore) return;
      loading = true;
      if (loadingEl) loadingEl.hidden = false;
      try {
        const res = await fetch(`${listUrl}?page=${page}&page_size=8`);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not load schemas");
          hasMore = false;
          return;
        }
        const payload = result.data || {};
        (payload.results || []).forEach((schema) => {
          schemaCache.set(String(schema.id), schema);
          schemaGrid.append(schemaCard(schema));
        });
        hasMore = Boolean(payload.has_more);
        page += 1;
      } catch (err) {
        toast("Could not load schemas");
        hasMore = false;
      } finally {
        loading = false;
        if (loadingEl) loadingEl.hidden = true;
        if (emptyEl) emptyEl.hidden = schemaCache.size > 0;
      }
    };

    const saveSchema = async () => {
      if (!saveUrl) return;
      const payload = collectSchemaPayload();
      if (!payload.schema_name) {
        toast("Give the schema a name.");
        return;
      }
      const saveBtn = $("[data-save-schema]");
      if (saveBtn) saveBtn.disabled = true;
      try {
        const res = await fetch(saveUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken(),
          },
          body: JSON.stringify(payload),
        });
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not save schema");
          return;
        }
        const schema = result.data;
        if (schema && schema.id != null) {
          schemaCache.set(String(schema.id), schema);
          const existing = schemaGrid.querySelector(`[data-saved-schema="${schema.id}"]`);
          const card = schemaCard(schema);
          if (existing) existing.replaceWith(card);
          else schemaGrid.prepend(card);
          setActiveSchemaCard(schema.id);
        }
        if (emptyEl) emptyEl.hidden = true;
        toast(result.message || "Schema saved");
      } catch (err) {
        toast("Could not save schema");
      } finally {
        if (saveBtn) saveBtn.disabled = false;
      }
    };

    const deleteSchema = async (schemaId) => {
      if (!deleteUrlTemplate || !schemaId) return;
      const url = deleteUrlTemplate.replace(/\/0\/?$/, `/${schemaId}/`);
      try {
        const res = await fetch(url, {
          method: "DELETE",
          headers: { "X-CSRFToken": window.csrfToken() },
        });
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not delete schema");
          return;
        }
        schemaCache.delete(String(schemaId));
        schemaGrid.querySelector(`[data-saved-schema="${schemaId}"]`)?.remove();
        if (emptyEl) emptyEl.hidden = schemaCache.size > 0;
        toast(result.message || "Schema deleted");
      } catch (err) {
        toast("Could not delete schema");
      }
    };

    window.__saveSchema = saveSchema;
    window.__deleteSchema = deleteSchema;
    loadSchemas();
    if (sentinel && "IntersectionObserver" in window) {
      new IntersectionObserver(
        (entries) => {
          if (entries.some((entry) => entry.isIntersecting)) loadSchemas();
        },
        { root: listRoot, rootMargin: "80px" }
      ).observe(sentinel);
    }
  }

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

  const uploadModal = $("#modal-upload");
  let uploadFiles = [];
  let jobPollTimer = null;

  const setUploadFiles = (files) => {
    uploadFiles = [...files].filter((file) => file.type === "application/pdf" || /\.pdf$/i.test(file.name));
    const hint = $("[data-upload-files]");
    if (!hint) return;
    if (!uploadFiles.length) {
      hint.hidden = true;
      hint.textContent = "";
      return;
    }
    hint.hidden = false;
    hint.textContent = `${uploadFiles.length} PDF${uploadFiles.length === 1 ? "" : "s"}: ${uploadFiles.map((file) => file.name).join(", ")}`;
  };

  const loadUploadSchemas = async () => {
    const url = uploadModal?.dataset.schemaListUrl;
    if (!url) return;
    try {
      const res = await fetch(`${url}?page=1&page_size=50`);
      const result = await res.json();
      const items = (result.data && result.data.results) || [];
      const fill = (select, placeholder) => {
        if (!select) return;
        const current = select.value;
        select.innerHTML = "";
        const first = document.createElement("option");
        first.value = "";
        first.textContent = placeholder;
        select.append(first);
        items.forEach((schema) => {
          const option = document.createElement("option");
          option.value = String(schema.id);
          option.textContent = schema.schema_name;
          select.append(option);
        });
        if (current) select.value = current;
      };
      fill($("[data-upload-schema]"), "No schema");
      fill($("[data-filter-schema]"), "Any");
      fill($("[data-reassign-schema]"), "Select a schema");
    } catch (err) {
      toast("Could not load schemas");
    }
  };

  const jobUrlFor = (id) => (uploadModal?.dataset.jobUrl || "").replace(/\/0\/?$/, `/${id}/`);

  const updateBatchUI = (job) => {
    const card = $("[data-batch]");
    if (!card || !job) return;
    const total = job.total_files || 0;
    const processed = job.processed || 0;
    const now = $("[data-batch-now]", card);
    const tot = $("[data-batch-total]", card);
    const bar = $("[data-batch-bar]", card);
    const statusEl = $("[data-batch-status]", card);
    const ok = $("[data-batch-ok]", card);
    const flag = $("[data-batch-flag]", card);
    const speed = $("[data-batch-speed]", card);
    if (now) now.textContent = String(processed);
    if (tot) tot.textContent = String(total);
    if (ok) ok.textContent = String(job.success_count || 0);
    if (flag) flag.textContent = String(job.flagged_count || 0);
    if (bar) bar.style.width = `${total ? (processed / total) * 100 : 0}%`;
    if (speed) speed.textContent = "Groq + Celery";
    if (statusEl) {
      if (job.status === "queued") statusEl.textContent = `Queued ${total} PDF${total === 1 ? "" : "s"} for Groq extraction.`;
      else if (job.status === "processing") statusEl.textContent = `Processing ${processed} of ${total} files… Groq worker`;
      else if (job.status === "completed") statusEl.textContent = `Done. ${job.success_count || 0} extracted, ${job.flagged_count || 0} flagged.`;
      else statusEl.textContent = job.error_message || "Job failed.";
    }
  };

  const pollJob = (jobId) => {
    const url = jobUrlFor(jobId);
    if (!url) return;
    window.clearInterval(jobPollTimer);
    const tick = async () => {
      try {
        const res = await fetch(url);
        const result = await res.json();
        if (!res.ok || !result.success) return;
        const job = result.data;
        updateBatchUI(job);
        if (job.status === "completed" || job.status === "failed") {
          window.clearInterval(jobPollTimer);
          toast(job.status === "completed" ? "Extraction complete." : (job.error_message || "Extraction failed."));
          if (typeof window.__reloadInbox === "function") window.__reloadInbox();
        }
      } catch (err) {
        /* keep polling until the worker finishes */
      }
    };
    tick();
    jobPollTimer = window.setInterval(tick, 1500);
  };

  const startUpload = async () => {
    if (!uploadModal) return;
    if (!uploadFiles.length) {
      toast("Choose at least one PDF.");
      return;
    }
    const schemaId = $("[data-upload-schema]")?.value;
    const btn = $("[data-upload-start]");
    if (btn) btn.disabled = true;
    const form = new FormData();
    if (schemaId) form.append("schema_id", schemaId);
    uploadFiles.forEach((file) => form.append("files", file));
    try {
      const res = await fetch(uploadModal.dataset.uploadUrl, {
        method: "POST",
        headers: { "X-CSRFToken": window.csrfToken() },
        body: form,
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not start extraction");
        return;
      }
      closeAll();
      toast(result.message || "Extraction queued");
      const job = result.data;
      if (typeof window.__reloadInbox === "function") window.__reloadInbox();
      const inboxUrl = uploadModal.dataset.inboxUrl;
      if (!$("[data-batch]") && inboxUrl) {
        window.location = `${inboxUrl}?job=${job.id}`;
        return;
      }
      updateBatchUI(job);
      pollJob(job.id);
    } catch (err) {
      toast("Could not start extraction");
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  window.__startUpload = startUpload;

  if (uploadModal) {
    const input = $("[data-file-input]", uploadModal);
    const dropzone = $("[data-dropzone]", uploadModal);
    if (input) input.addEventListener("change", () => setUploadFiles(input.files || []));
    if (dropzone) {
      ["dragenter", "dragover"].forEach((evt) => {
        dropzone.addEventListener(evt, (e) => {
          e.preventDefault();
          dropzone.classList.add("is-over");
        });
      });
      ["dragleave", "drop"].forEach((evt) => {
        dropzone.addEventListener(evt, (e) => {
          e.preventDefault();
          dropzone.classList.remove("is-over");
        });
      });
      dropzone.addEventListener("drop", (e) => {
        const files = e.dataTransfer && e.dataTransfer.files;
        if (!files || !files.length) return;
        setUploadFiles(files);
      });
    }
    const jobId = new URLSearchParams(window.location.search).get("job");
    if (jobId) pollJob(jobId);
  }

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
      const modalId = openBtn.getAttribute("data-open");
      openModal(modalId);
      if (modalId === "modal-upload" || modalId === "modal-filters" || modalId === "modal-schema-edit") {
        loadUploadSchemas();
      }
      if (modalId === "modal-webhook" && typeof loadWebhookForm === "function") loadWebhookForm();
      if (["modal-retry", "modal-schema-edit", "modal-preview", "modal-reject"].includes(modalId)) {
        const pending = setPendingDocument(openBtn);
        if (modalId === "modal-preview") {
          const frame = $("[data-preview-frame]");
          const placeholder = $("[data-preview-placeholder]");
          const missing = $("[data-preview-missing]");
          const fileUrl = pending.fileUrl || $("#modal-preview")?.dataset.fileUrl || "";
          if (frame && fileUrl) {
            frame.src = fileUrl;
            frame.hidden = false;
            if (placeholder) placeholder.hidden = true;
            if (missing) missing.hidden = true;
          } else {
            if (frame) {
              frame.removeAttribute("src");
              frame.hidden = true;
            }
            if (placeholder) placeholder.hidden = Boolean(pending.id);
            if (missing) missing.hidden = !pending.id;
          }
        }
      }
      if (modalId === "modal-alerts" && typeof window.__loadAlerts === "function") window.__loadAlerts();
      if (modalId === "modal-search") $("[data-workspace-search]")?.focus();
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
      return;
    }

    if (e.target.closest("[data-download='json']")) {
      if (typeof window.__createExport === "function" && exportsRoot) {
        createExport("json", "all");
        return;
      }
      const name = ($("[data-review]")?.dataset.filename || "fieldline-extract") + ".json";
      downloadText(name.replace(/\.pdf/i, ""), reviewPayloadText(), "application/json");
      toast("Validated JSON downloaded.");
      return;
    }
    if (e.target.closest("[data-download='csv']")) {
      if (typeof window.__createExport === "function" && exportsRoot) {
        createExport("csv", "all");
        return;
      }
      const name = ($("[data-review]")?.dataset.filename || "fieldline-extract") + ".csv";
      downloadText(name.replace(/\.pdf/i, ""), jsonToCsv(reviewPayloadText()), "text/csv");
      toast("CSV downloaded.");
      return;
    }
    if (e.target.closest("[data-copy-sql]")) {
      if (typeof window.__copyExportSql === "function") {
        window.__copyExportSql();
        return;
      }
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
      if (typeof window.__testWebhook === "function") {
        window.__testWebhook();
        closeAll();
        return;
      }
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

    const delBtn = e.target.closest("[data-delete-schema]");
    if (delBtn) {
      e.preventDefault();
      e.stopPropagation();
      const card = delBtn.closest("[data-saved-schema]");
      if (card && typeof window.__deleteSchema === "function") {
        window.__deleteSchema(card.dataset.savedSchema);
      }
      return;
    }
    const saved = e.target.closest("[data-saved-schema]");
    if (saved) {
      const schema = schemaCache.get(String(saved.dataset.savedSchema));
      if (schema) {
        applySchema(schema);
        setActiveSchemaCard(saved.dataset.savedSchema);
        toast("Schema loaded");
      }
      return;
    }
    const load = e.target.closest("[data-load-schema]");
    if (load && fieldTable) {
      $$("[data-load-schema]").forEach((c) => c.classList.remove("is-active"));
      load.classList.add("is-active");
      $$("[data-saved-schema]").forEach((c) => c.classList.remove("is-active"));
      const key = load.dataset.loadSchema;
      const meta = PRESET_META[key] || PRESET_META.blank;
      const nameInput = $("[data-schema-name]");
      const descInput = $("[data-schema-description]");
      if (nameInput) nameInput.value = meta.name;
      if (descInput) descInput.value = meta.description;
      renderFields(PRESETS[key] || []);
      toast("Preset loaded");
      return;
    }
    if (e.target.closest("[data-save-schema]") && typeof window.__saveSchema === "function") {
      closeAll();
      window.__saveSchema();
      return;
    }
    if (e.target.closest("[data-upload-start]") && typeof window.__startUpload === "function") {
      window.__startUpload();
      return;
    }
    if (e.target.closest("[data-apply-filters]") && typeof window.__applyInboxFilters === "function") {
      window.__applyInboxFilters();
      closeAll();
      return;
    }
    if (e.target.closest("[data-reset-filters]") && typeof window.__resetInboxFilters === "function") {
      window.__resetInboxFilters();
      closeAll();
      return;
    }
    if (e.target.closest("[data-export-quick]")) {
      const fmt = e.target.closest("[data-export-quick]").dataset.exportQuick;
      createExport(fmt, "all");
      return;
    }
    if (e.target.closest("[data-confirm-export]") && typeof window.__createExport === "function") {
      closeAll();
      window.__createExport();
      return;
    }
    if (e.target.closest("[data-save-webhook]") && typeof window.__saveWebhook === "function") {
      closeAll();
      window.__saveWebhook();
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

    if (e.target.closest("[data-confirm-approve]")) {
      window.__approveDocument();
      return;
    }
    if (e.target.closest("[data-confirm-reject]")) {
      window.__rejectDocument();
      return;
    }
    if (e.target.closest("[data-confirm-retry]")) {
      window.__retryDocument();
      return;
    }
    if (e.target.closest("[data-confirm-schema-change]")) {
      window.__changeDocumentSchema();
      return;
    }

    const actions = [
      ["data-send-invite", "Invite sent (UI)."],
    ];
    for (const [attr, msg] of actions) {
      if (e.target.closest(`[${attr}]`)) {
        closeAll();
        toast(msg);
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
  const inboxRoot = $("[data-inbox]");
  if (inboxRoot) {
    const body = $("[data-inbox-body]");
    const emptyEl = $("[data-inbox-empty]");
    const loadingEl = $("[data-inbox-loading]");
    const moreBtn = $("[data-inbox-more]");
    const searchInput = $("[data-inbox-search]");
    const listUrl = inboxRoot.dataset.listUrl;
    const reviewUrl = inboxRoot.dataset.reviewUrl || "/app/review/";
    const inboxMode = inboxRoot.dataset.inboxMode || "inbox";
    const fixedStatus = inboxRoot.dataset.fixedStatus || "";
    let page = 1;
    let hasMore = true;
    let loading = false;
    let searchTimer = null;
    const filters = { status: fixedStatus || "all", search: "", schema_id: "", received: "" };
    const statusMeta = {
      queued: ["Queued", "pill-muted"],
      processing: ["Processing", "pill-muted"],
      needs_review: ["Needs review", "pill-warn"],
      extracted: ["Extracted", "pill-ok"],
      approved: ["Approved", "pill-ok"],
      failed: ["Failed", "pill-warn"],
    };

    const actionButton = (label, attrs) => {
      const btn = document.createElement("button");
      btn.className = "link";
      btn.type = "button";
      btn.textContent = label;
      Object.entries(attrs).forEach(([key, value]) => btn.setAttribute(key, value));
      return btn;
    };

    const inboxRow = (doc) => {
      const [label, pill] = statusMeta[doc.status] || [doc.status || "Queued", "pill-muted"];
      const tr = document.createElement("tr");
      tr.dataset.status = doc.status || "";
      tr.dataset.docId = String(doc.id);
      if (doc.file_url) tr.dataset.fileUrl = doc.file_url;
      if (inboxMode === "exceptions") {
        tr.innerHTML = `<td><a class="row-btn" href="${reviewUrl}?id=${doc.id}"><strong></strong><span data-summary></span></a></td><td data-issue></td><td data-received></td><td data-actions></td>`;
        tr.querySelector("strong").textContent = doc.original_name || "Untitled.pdf";
        tr.querySelector("[data-summary]").textContent = doc.schema_name || "";
        tr.querySelector("[data-issue]").textContent = doc.error_message || doc.summary || "Failed";
        tr.querySelector("[data-received]").textContent = doc.received || "";
      } else {
        tr.innerHTML = `<td><a class="row-btn" href="${reviewUrl}?id=${doc.id}"><strong></strong><span data-summary></span></a></td><td data-type></td><td data-received></td><td><span class="pill ${pill}"></span></td><td data-actions></td>`;
        tr.querySelector("strong").textContent = doc.original_name || "Untitled.pdf";
        tr.querySelector("[data-summary]").textContent = doc.summary || "";
        tr.querySelector("[data-type]").textContent = doc.schema_name || "—";
        tr.querySelector("[data-received]").textContent = doc.received || "";
        tr.querySelector(".pill").textContent = label;
      }
      const actions = tr.querySelector("[data-actions]");
      const bits = [];
      if (doc.status === "needs_review" || doc.status === "extracted" || doc.status === "approved") {
        const link = document.createElement("a");
        link.className = "link";
        link.href = `${reviewUrl}?id=${doc.id}`;
        link.textContent = doc.status === "needs_review" ? "Review" : "Open";
        bits.push(link);
      }
      if (doc.status === "failed") {
        bits.push(actionButton("Retry", { "data-open": "modal-retry", "data-document-id": String(doc.id) }));
        bits.push(actionButton("Change schema", { "data-open": "modal-schema-edit", "data-document-id": String(doc.id) }));
        const reviewLink = document.createElement("a");
        reviewLink.className = "link";
        reviewLink.href = `${reviewUrl}?id=${doc.id}`;
        reviewLink.textContent = "Open";
        bits.push(reviewLink);
      }
      if (doc.file_url) {
        bits.push(
          actionButton("Preview", {
            "data-open": "modal-preview",
            "data-document-id": String(doc.id),
            "data-file-url": doc.file_url,
          })
        );
      }
      if (!bits.length) actions.textContent = "—";
      else {
        bits.forEach((el, i) => {
          if (i) actions.append(document.createTextNode(" · "));
          actions.append(el);
        });
      }
      return tr;
    };

    const queryString = () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "12",
        status: filters.status || "all",
      });
      if (filters.search) params.set("search", filters.search);
      if (filters.schema_id) params.set("schema_id", filters.schema_id);
      if (filters.received) params.set("received", filters.received);
      return params.toString();
    };

    const loadInbox = async ({ reset } = { reset: false }) => {
      if (!listUrl || loading) return;
      if (reset) {
        page = 1;
        hasMore = true;
        if (body) body.innerHTML = "";
      }
      if (!hasMore) return;
      loading = true;
      if (loadingEl) loadingEl.hidden = false;
      try {
        const res = await fetch(`${listUrl}?${queryString()}`);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not load documents");
          hasMore = false;
          return;
        }
        const payload = result.data || {};
        (payload.results || []).forEach((doc) => body && body.append(inboxRow(doc)));
        hasMore = Boolean(payload.has_more);
        page += 1;
      } catch (err) {
        toast("Could not load documents");
        hasMore = false;
      } finally {
        loading = false;
        if (loadingEl) loadingEl.hidden = true;
        if (emptyEl) emptyEl.hidden = Boolean(body && body.children.length);
        if (moreBtn) moreBtn.hidden = !(hasMore && body && body.children.length);
      }
    };

    const syncStatusTab = (status) => {
      tabs.forEach((btn) => {
        btn.classList.toggle("is-on", (btn.dataset.filter || "all") === status);
      });
    };

    window.__reloadInbox = () => loadInbox({ reset: true });
    window.__applyInboxFilters = () => {
      filters.schema_id = $("[data-filter-schema]")?.value || "";
      filters.status = fixedStatus || $("[data-filter-status]")?.value || "all";
      filters.received = $("[data-filter-received]")?.value || "";
      syncStatusTab(filters.status === "processing" ? "queued" : filters.status);
      loadInbox({ reset: true });
    };
    window.__resetInboxFilters = () => {
      filters.status = fixedStatus || "all";
      filters.search = "";
      filters.schema_id = "";
      filters.received = "";
      if (searchInput) searchInput.value = "";
      const schemaSelect = $("[data-filter-schema]");
      const statusSelect = $("[data-filter-status]");
      const receivedSelect = $("[data-filter-received]");
      if (schemaSelect) schemaSelect.value = "";
      if (statusSelect) statusSelect.value = filters.status;
      if (receivedSelect) receivedSelect.value = "";
      syncStatusTab(filters.status);
      loadInbox({ reset: true });
    };

    const statusFromUrl = new URLSearchParams(window.location.search).get("status");
    if (fixedStatus) {
      filters.status = fixedStatus;
    } else if (statusFromUrl) {
      filters.status = statusFromUrl;
      const statusSelect = $("[data-filter-status]");
      if (statusSelect) statusSelect.value = filters.status;
      syncStatusTab(filters.status);
    }

    loadInbox({ reset: true });
    tabs.forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.status = btn.dataset.filter || "all";
        const statusSelect = $("[data-filter-status]");
        if (statusSelect) statusSelect.value = filters.status;
        syncStatusTab(filters.status);
        loadInbox({ reset: true });
      });
    });
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => {
          filters.search = searchInput.value.trim();
          loadInbox({ reset: true });
        }, 300);
      });
    }
    if (moreBtn) moreBtn.addEventListener("click", () => loadInbox());
  }

  const dashboardRoot = $("[data-dashboard]");
  if (dashboardRoot) {
    const overviewUrl = dashboardRoot.dataset.overviewUrl;
    const reviewUrl = dashboardRoot.dataset.reviewUrl || "/app/review/";
    const loadOverview = async () => {
      if (!overviewUrl) return;
      try {
        const res = await fetch(overviewUrl);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not load overview");
          return;
        }
        const data = result.data || {};
        ["queued", "needs_review", "extracted_today", "exceptions"].forEach((key) => {
          const el = $(`[data-kpi="${key}"]`);
          if (el) el.textContent = String(data[key] || 0);
        });
        const list = $("[data-attention-list]");
        const empty = $("[data-attention-empty]");
        if (list) {
          list.innerHTML = "";
          (data.attention || []).forEach((doc) => {
            const li = document.createElement("li");
            li.innerHTML = `<a class="row-btn" href="${reviewUrl}?id=${doc.id}"><strong></strong><span></span></a><a class="pill pill-warn" href="${reviewUrl}?id=${doc.id}">Review</a>`;
            li.querySelector("strong").textContent = doc.original_name || "Document";
            li.querySelector("span").textContent = `${doc.schema_name || "Schema"} · ${doc.summary || "Needs review"}`;
            list.append(li);
          });
        }
        if (empty) empty.hidden = Boolean((data.attention || []).length);
        const step = Number(data.pipeline_step || 1);
        $$("[data-pipeline] [data-step]").forEach((el) => {
          const n = Number(el.dataset.step);
          el.classList.toggle("is-done", n < step);
          el.classList.toggle("is-now", n === step);
        });
      } catch (err) {
        toast("Could not load overview");
      }
    };
    loadOverview();
  }

  const exportsRoot = $("[data-exports]");
  const exportModal = $("#modal-export");
  const webhookModal = $("#modal-webhook");

  const createExport = async (fmt, sourceRange) => {
    const url = (exportsRoot && exportsRoot.dataset.createUrl) || (exportModal && exportModal.dataset.createUrl);
    if (!url) return;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.csrfToken(),
        },
        body: JSON.stringify({ format: fmt, source_range: sourceRange || "all" }),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not create export");
        return;
      }
      toast(result.message || "Export ready");
      if (result.data && result.data.download_url) window.location = result.data.download_url;
      if (typeof window.__reloadExports === "function") window.__reloadExports();
    } catch (err) {
      toast("Could not create export");
    }
  };

  const loadWebhookForm = async () => {
    const url = (webhookModal && webhookModal.dataset.webhookApi) || (exportsRoot && exportsRoot.dataset.webhookUrl);
    if (!url) return;
    try {
      const res = await fetch(url);
      const result = await res.json();
      if (!res.ok || !result.success) return;
      const data = result.data || {};
      const urlInput = $("[data-webhook-url-input]");
      const statusEl = $("[data-webhook-status]");
      if (urlInput) urlInput.value = data.url || "";
      if (statusEl) statusEl.textContent = data.last_status ? `Last ping ${data.last_status}` : "Save an endpoint to ping it";
    } catch (err) {
      /* ignore empty webhook */
    }
  };

  window.__createExport = () => {
    const fmt = $("[data-export-format]")?.value || "json";
    const range = $("[data-export-range]")?.value || "all";
    createExport(fmt, range);
  };
  window.__saveWebhook = async () => {
    const url = (webhookModal && webhookModal.dataset.webhookApi) || (exportsRoot && exportsRoot.dataset.webhookUrl);
    if (!url) return;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.csrfToken(),
        },
        body: JSON.stringify({
          url: $("[data-webhook-url-input]")?.value || "",
        }),
      });
      const result = await res.json();
      toast(result.message || (result.success ? "Webhook saved" : "Could not save webhook"));
      if (result.success) loadWebhookForm();
    } catch (err) {
      toast("Could not save webhook");
    }
  };
  window.__testWebhook = async () => {
    const url = (webhookModal && webhookModal.dataset.webhookTestApi) || (exportsRoot && exportsRoot.dataset.webhookTestUrl);
    if (!url) return;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": window.csrfToken() },
      });
      const result = await res.json();
      toast(result.message || "Webhook test sent");
      if (result.success) loadWebhookForm();
    } catch (err) {
      toast("Could not test webhook");
    }
  };

  if (exportsRoot) {
    const listUrl = exportsRoot.dataset.listUrl;
    const sqlUrl = exportsRoot.dataset.sqlUrl;
    const listEl = $("[data-export-list]");
    const emptyEl = $("[data-export-empty]");
    const renderExports = (items) => {
      if (!listEl) return;
      listEl.innerHTML = "";
      items.forEach((item) => {
        const li = document.createElement("li");
        li.innerHTML = `<div><strong></strong><span></span></div><a class="link" href="${item.download_url}">Download</a>`;
        li.querySelector("strong").textContent = item.filename;
        li.querySelector("span").textContent = `${item.row_count} rows · ${item.range_label || item.source_range} · ${item.created_label}`;
        listEl.append(li);
      });
      if (emptyEl) emptyEl.hidden = items.length > 0;
    };
    const loadExports = async () => {
      if (!listUrl) return;
      try {
        const res = await fetch(`${listUrl}?page=1&page_size=12`);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not load exports");
          return;
        }
        renderExports((result.data && result.data.results) || []);
      } catch (err) {
        toast("Could not load exports");
      }
    };
    window.__reloadExports = loadExports;
    window.__copyExportSql = async () => {
      if (!sqlUrl) return;
      try {
        const res = await fetch(sqlUrl);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not copy SQL");
          return;
        }
        const sql = result.data && result.data.sql;
        if (sql && navigator.clipboard) {
          await navigator.clipboard.writeText(sql);
          toast("PostgreSQL insert copied.");
        } else {
          toast("No SQL to copy.");
        }
      } catch (err) {
        toast("Could not copy SQL");
      }
    };
    loadExports();
    loadWebhookForm();
  }

  const searchModal = $("#modal-search");
  if (searchModal) {
    const input = $("[data-workspace-search]");
    const list = $("[data-search-results]");
    const empty = $("[data-search-empty]");
    let searchWait = null;
    const runSearch = async (query) => {
      const url = searchModal.dataset.listUrl;
      if (!url) return;
      if (!query) {
        if (list) list.innerHTML = "";
        if (empty) {
          empty.hidden = false;
          empty.textContent = "Type to search your documents.";
        }
        return;
      }
      try {
        const res = await fetch(`${url}?search=${encodeURIComponent(query)}&page=1&page_size=8`);
        const result = await res.json();
        const items = (result.data && result.data.results) || [];
        if (list) {
          list.innerHTML = "";
          const reviewUrl = searchModal.dataset.reviewUrl || "/app/review/";
          items.forEach((doc) => {
            const li = document.createElement("li");
            li.innerHTML = `<div><strong></strong><span></span></div><a class="link" href="${reviewUrl}?id=${doc.id}">Open</a>`;
            li.querySelector("strong").textContent = doc.original_name || "Document";
            li.querySelector("span").textContent = `${doc.schema_name || "Schema"} · ${(doc.status || "").replaceAll("_", " ")}`;
            list.append(li);
          });
        }
        if (empty) {
          empty.hidden = items.length > 0;
          empty.textContent = items.length ? "" : "No documents matched.";
        }
      } catch (err) {
        toast("Could not search");
      }
    };
    if (input) {
      input.addEventListener("input", () => {
        window.clearTimeout(searchWait);
        searchWait = window.setTimeout(() => runSearch(input.value.trim()), 280);
      });
    }
  }

  window.__loadAlerts = async () => {
    const modal = $("#modal-alerts");
    if (!modal || !modal.dataset.overviewUrl) return;
    const list = $("[data-alerts-list]");
    const empty = $("[data-alerts-empty]");
    try {
      const res = await fetch(modal.dataset.overviewUrl);
      const result = await res.json();
      if (!res.ok || !result.success) return;
      const data = result.data || {};
      if (list) list.innerHTML = "";
      const items = [];
      if (data.needs_review) {
        items.push({
          title: `${data.needs_review} document${data.needs_review === 1 ? "" : "s"} waiting review`,
          detail: "Open inbox to verify extracted fields",
          href: `${modal.dataset.inboxUrl}?status=needs_review`,
        });
      }
      if (data.exceptions) {
        items.push({
          title: `${data.exceptions} exception${data.exceptions === 1 ? "" : "s"}`,
          detail: "Failed extractions need a retry",
          href: modal.dataset.exceptionsUrl,
        });
      }
      (data.attention || []).forEach((doc) => {
        items.push({
          title: doc.original_name || "Document",
          detail: `${doc.schema_name || "Schema"} · ${doc.summary || "Needs review"}`,
          href: `${modal.dataset.reviewUrl}?id=${doc.id}`,
        });
      });
      items.forEach((item) => {
        const li = document.createElement("li");
        li.innerHTML = `<div><strong></strong><span></span></div><a class="link" href="${item.href}">Go</a>`;
        li.querySelector("strong").textContent = item.title;
        li.querySelector("span").textContent = item.detail;
        if (list) list.append(li);
      });
      if (empty) empty.hidden = items.length > 0;
      const bell = document.querySelector("[data-open='modal-alerts']");
      if (bell) bell.classList.toggle("has-dot", Boolean(data.needs_review || data.exceptions));
    } catch (err) {
      /* ignore */
    }
  };
  if ($("#modal-alerts")) window.__loadAlerts();

  const recordsRoot = $("[data-records]");
  if (recordsRoot) {
    const listUrl = recordsRoot.dataset.listUrl;
    const reviewUrl = recordsRoot.dataset.reviewUrl || "/app/review/";
    const head = $("[data-records-head]");
    const body = $("[data-records-body]");
    const emptyEl = $("[data-records-empty]");
    const loadingEl = $("[data-records-loading]");
    const moreBtn = $("[data-records-more]");
    const searchInput = $("[data-records-search]");
    let page = 1;
    let hasMore = true;
    let loading = false;
    let search = "";
    let searchTimer = null;
    let columns = [];
    let rows = [];

    const cellValue = (value) => {
      if (value == null || value === "") return "—";
      return String(value);
    };

    const renderTable = () => {
      if (!head || !body) return;
      const extra = columns.length ? columns : [];
      head.innerHTML = `<tr><th>Document</th><th>Schema</th>${extra.map((key) => `<th>${labelize(key)}</th>`).join("")}<th>When</th><th></th></tr>`;
      body.innerHTML = "";
      rows.forEach((row) => {
        const tr = document.createElement("tr");
        const payload = row.payload && typeof row.payload === "object" ? row.payload : {};
        const reviewHref = row.document_id ? `${reviewUrl}?id=${row.document_id}` : "";
        tr.innerHTML = `<td><strong></strong><span></span></td><td></td>${extra.map(() => "<td></td>").join("")}<td></td><td></td>`;
        const tds = [...tr.children];
        tds[0].querySelector("strong").textContent = row.original_name || "Document";
        tds[0].querySelector("span").textContent = (row.event || "").replace("fieldline.document.", "") || row.status || "";
        tds[1].textContent = row.schema_name || "—";
        extra.forEach((key, i) => {
          tds[2 + i].textContent = cellValue(payload[key]);
          tds[2 + i].title = cellValue(payload[key]);
        });
        tds[tds.length - 2].textContent = row.received || "";
        if (reviewHref) {
          const link = document.createElement("a");
          link.className = "link";
          link.href = reviewHref;
          link.textContent = "Open";
          tds[tds.length - 1].append(link);
        } else {
          tds[tds.length - 1].textContent = "—";
        }
        body.append(tr);
      });
    };

    const loadRecords = async ({ reset } = { reset: false }) => {
      if (!listUrl || loading) return;
      if (reset) {
        page = 1;
        hasMore = true;
        rows = [];
        columns = [];
      }
      if (!hasMore) return;
      loading = true;
      if (loadingEl) loadingEl.hidden = false;
      try {
        const params = new URLSearchParams({ page: String(page), page_size: "12" });
        if (search) params.set("search", search);
        const res = await fetch(`${listUrl}?${params}`);
        const result = await res.json();
        if (!res.ok || !result.success) {
          toast(result.message || "Could not load extracted data");
          hasMore = false;
          return;
        }
        const payload = result.data || {};
        columns = payload.columns || columns;
        (payload.results || []).forEach((row) => rows.push(row));
        hasMore = Boolean(payload.has_more);
        page += 1;
        renderTable();
      } catch (err) {
        toast("Could not load extracted data");
        hasMore = false;
      } finally {
        loading = false;
        if (loadingEl) loadingEl.hidden = true;
        if (emptyEl) emptyEl.hidden = rows.length > 0;
        if (moreBtn) moreBtn.hidden = !(hasMore && rows.length > 0);
      }
    };

    loadRecords({ reset: true });
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => {
          search = searchInput.value.trim();
          loadRecords({ reset: true });
        }, 300);
      });
    }
    if (moreBtn) moreBtn.addEventListener("click", () => loadRecords());
    window.setInterval(() => {
      if (document.hidden) return;
      loadRecords({ reset: true });
    }, 8000);
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
