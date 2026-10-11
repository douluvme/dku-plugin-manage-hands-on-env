/* Hands-on Workshop Console: front end of the plugin webapp.
 *
 * Talks to backend.py through the /api/... routes (see managehandsonenv.webapp.api).
 * The left menu and the forms are built from what the backend sends, so a feature
 * added to managehandsonenv.features shows up here without any JS change.
 */
(function () {
  "use strict";

  var POLL_MS = 1000;
  var STORAGE_KEY = "hands-on-console-ui";
  var state = { context: null, feature: null, schema: null, job: null, poller: null, logLength: 0, tab: "run", historyCount: 0 };

  // ---- backend ---------------------------------------------------------------
  function api(path, options) {
    return fetch(getWebAppBackendUrl(path), options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) {
          var err = new Error(body.error || ("HTTP " + response.status));
          err.status = response.status;
          err.body = body;
          throw err;
        }
        return body;
      });
    });
  }

  function post(path, payload) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  // ---- helpers ---------------------------------------------------------------
  function $(id) { return document.getElementById(id); }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === "class") node.className = attrs[key];
      else if (key === "text") node.textContent = attrs[key];
      else if (key === "html") node.innerHTML = attrs[key];
      else if (key.indexOf("on") === 0) node.addEventListener(key.slice(2), attrs[key]);
      else if (attrs[key] !== null && attrs[key] !== undefined) node.setAttribute(key, attrs[key]);
    });
    (children || []).forEach(function (child) { node.appendChild(child); });
    return node;
  }

  // banner(message, isError, {label, onclick}) — the optional action becomes a button (e.g. Retry)
  function banner(message, isError, action) {
    var node = $("hoc-banner");
    if (!message) { node.hidden = true; return; }
    node.innerHTML = "";
    node.appendChild(el("span", { class: "hoc-banner-text", text: message }));
    if (action) {
      node.appendChild(el("button", { type: "button", class: "hoc-tool-btn hoc-tool-sm", text: action.label, onclick: action.onclick }));
    }
    node.appendChild(el("button", { type: "button", class: "hoc-banner-close", "aria-label": "Dismiss", text: "×",
                                    onclick: function () { node.hidden = true; } }));
    node.className = "hoc-banner" + (isError ? " hoc-banner-error" : "");
    node.hidden = false;
  }

  function formatTime(seconds) {
    if (!seconds) return "";
    var d = new Date(seconds * 1000);
    var time = d.toTimeString().slice(0, 8);
    var today = new Date();
    var sameDay = d.getFullYear() === today.getFullYear() && d.getMonth() === today.getMonth() && d.getDate() === today.getDate();
    return sameDay ? time : d.toISOString().slice(0, 10) + " " + time;
  }

  function formatDuration(job) {
    var start = job.started_at || job.created_at;
    if (!start) return "";
    var end = job.finished_at || (job.active ? Date.now() / 1000 : null);
    if (!end) return "";
    var s = Math.max(0, Math.round(end - start));
    if (s < 60) return s + "s";
    if (s < 3600) return Math.floor(s / 60) + "m " + (s % 60) + "s";
    return Math.floor(s / 3600) + "h " + Math.floor((s % 3600) / 60) + "m";
  }

  function paramsTooltip(params) {
    return Object.keys(params || {}).map(function (k) {
      var v = params[k];
      return k + ": " + (Array.isArray(v) ? v.join(", ") : String(v));
    }).join("\n");
  }

  // Per-viewer UI preferences (collapsed sidebar, closed sections). Best effort only.
  function loadPrefs() {
    try { return JSON.parse(window.localStorage.getItem(STORAGE_KEY)) || {}; } catch (e) { return {}; }
  }
  function savePrefs(update) {
    try {
      var prefs = loadPrefs();
      Object.keys(update).forEach(function (k) { prefs[k] = update[k]; });
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) { /* storage unavailable: nothing to remember */ }
  }

  // ---- visibility conditions ------------------------------------------------
  // Supports the subset used by the descriptors: model.x == 'v', model.x != 'v', model.x,
  // !model.x, combined with && and || (|| binds loosest). No parentheses.
  function evalCondition(condition, model) {
    if (!condition) return true;
    return condition.split("||").some(function (orClause) {
      return orClause.split("&&").every(function (clause) {
        var m = /^\s*(!)?\s*model\.(\w+)\s*(?:(==|!=)\s*(?:'([^']*)'|"([^"]*)"|(true|false|[\d.]+)))?\s*$/.exec(clause);
        if (!m) return true; // unknown syntax: show the field rather than hide it
        var value = model[m[2]];
        if (!m[3]) return m[1] ? !value : !!value;
        var expected = m[4] !== undefined ? m[4] : (m[5] !== undefined ? m[5] : m[6]);
        if (expected === "true") expected = true;
        else if (expected === "false") expected = false;
        var equal = String(value) === String(expected);
        var result = m[3] === "==" ? equal : !equal;
        return m[1] ? !result : result;
      });
    });
  }

  // ---- sidebar menu -----------------------------------------------------------
  function renderMenu(context) {
    var prefs = loadPrefs();
    var closed = prefs.closedSections || {};
    var nav = $("hoc-menu");
    nav.innerHTML = "";
    context.categories.forEach(function (category) {
      var items = category.features.map(function (feature) {
        var children = [el("span", { class: "hoc-item-label", text: feature.menu_label || feature.label })];
        if (feature.destructive) {
          children.push(el("span", { class: "hoc-flag", text: "⚠", title: feature.confirm || "Changes the instance" }));
        }
        children.push(el("span", { class: "hoc-dot", hidden: "hidden", "data-dot": feature.id }));
        return el("li", { role: "none" }, [
          el("button", {
            type: "button",
            role: "menuitem",
            class: "hoc-item",
            "data-feature": feature.id,
            title: feature.label + (feature.description ? " — " + feature.description : ""),
            onclick: function () { selectFeature(feature.id); },
            onkeydown: menuKeydown
          }, children)
        ]);
      });
      var section = el("div", { class: "hoc-section" + (closed[category.name] ? "" : " open"), "data-section": category.name }, [
        el("button", {
          type: "button",
          class: "hoc-section-head",
          "aria-expanded": closed[category.name] ? "false" : "true",
          onclick: function () { toggleSection(section, category.name); }
        }, [
          el("span", { class: "hoc-chevron", text: "▼" }),
          el("span", { text: category.menu_name || category.name })
        ]),
        el("ul", { class: "hoc-items", role: "menu" }, items)
      ]);
      nav.appendChild(section);
    });
    // collapsed-sidebar rail: one initial per section, expands the menu and opens that section
    var rail = $("hoc-rail");
    rail.innerHTML = "";
    context.categories.forEach(function (category) {
      var name = category.menu_name || category.name;
      rail.appendChild(el("button", {
        type: "button", class: "hoc-rail-btn", title: name, "aria-label": name, text: name.charAt(0).toUpperCase(),
        onclick: function () {
          setSidebarCollapsed(false);
          var section = document.querySelector('.hoc-section[data-section="' + category.name.replace(/"/g, '\\"') + '"]');
          if (section && !section.classList.contains("open")) toggleSection(section, category.name);
        }
      }));
    });
  }

  function toggleSection(section, name) {
    var open = !section.classList.contains("open");
    section.classList.toggle("open", open);
    section.querySelector(".hoc-section-head").setAttribute("aria-expanded", open ? "true" : "false");
    var closed = loadPrefs().closedSections || {};
    if (open) delete closed[name]; else closed[name] = true;
    savePrefs({ closedSections: closed });
  }

  function menuKeydown(event) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    var items = Array.prototype.filter.call(document.querySelectorAll(".hoc-item"), function (item) {
      return item.offsetParent !== null; // visible (section open, sidebar expanded)
    });
    var index = items.indexOf(event.currentTarget);
    if (index < 0) return;
    event.preventDefault();
    var next = items[(index + (event.key === "ArrowDown" ? 1 : items.length - 1)) % items.length];
    next.focus();
  }

  function markSelected(featureId) {
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-item"), function (item) {
      var active = item.getAttribute("data-feature") === featureId;
      item.classList.toggle("active", active);
      if (active) item.setAttribute("aria-current", "true"); else item.removeAttribute("aria-current");
    });
  }

  function updateRunningDots() {
    var runningId = state.job && state.job.active ? state.job.feature_id : null;
    Array.prototype.forEach.call(document.querySelectorAll("[data-dot]"), function (dot) {
      dot.hidden = dot.getAttribute("data-dot") !== runningId;
    });
    $("hoc-history-dot").hidden = !runningId;
  }

  // Narrow screens: the sidebar is an off-canvas drawer opened by the hamburger button.
  function setDrawerOpen(open) {
    $("hoc-sidebar").classList.toggle("open", open);
    $("hoc-backdrop").hidden = !open;
    $("hoc-hamburger").setAttribute("aria-expanded", open ? "true" : "false");
  }

  function setSidebarCollapsed(collapsed) {
    var sidebar = $("hoc-sidebar");
    sidebar.classList.toggle("collapsed", collapsed);
    var button = $("hoc-collapse");
    button.title = collapsed ? "Expand menu" : "Collapse menu";
    button.setAttribute("aria-label", button.title);
    savePrefs({ sidebarCollapsed: collapsed });
  }

  // ---- tabs -------------------------------------------------------------------
  function showTab(name) {
    state.tab = name;
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-tab"), function (tab) {
      var active = tab.getAttribute("data-tab") === name;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-pane"), function (pane) {
      pane.hidden = pane.getAttribute("data-pane") !== name;
    });
    if (name === "history") refreshHistory();
  }

  // ---- form -------------------------------------------------------------------
  function selectFeature(featureId, prefill) {
    markSelected(featureId);
    setDrawerOpen(false);
    showTab("run");
    return api("/api/features/" + encodeURIComponent(featureId) + "/form").then(function (schema) {
      state.feature = featureId;
      state.schema = schema;
      renderForm(schema);
      if (prefill) fillForm(schema, prefill);
    }).catch(function (err) { banner("Could not load the form: " + err.message, true); });
  }

  function renderForm(schema) {
    $("hoc-empty").hidden = true;
    $("hoc-feature").hidden = false;
    $("hoc-feature-label").textContent = schema.label;
    $("hoc-feature-description").textContent = schema.description || "";
    var chips = $("hoc-settings");
    chips.innerHTML = "";
    var hints = [];
    (schema.settings || []).forEach(function (setting) {
      chips.appendChild(el("span", { class: "hoc-chip" + (setting.missing ? " missing" : ""), title: setting.hint || "" }, [
        el("span", { class: "hoc-chip-key", text: setting.label }),
        el("span", { class: "hoc-chip-value", text: setting.value })
      ]));
      if (setting.missing && setting.hint) hints.push(setting.hint);
    });
    if (hints.length) chips.appendChild(el("span", { class: "hoc-chip-hint", text: hints.join(" ") }));
    chips.hidden = !(schema.settings && schema.settings.length);
    var form = $("hoc-form");
    form.innerHTML = "";
    schema.params.forEach(function (param) { form.appendChild(renderField(param)); });
    $("hoc-run-error").hidden = true;
    applyVisibility();
    updateRunButton();
  }

  // Put a job's parameters back into the form (every input type the form renders).
  function fillForm(schema, params) {
    (schema.params || []).forEach(function (param) {
      if (!(param.name in params)) return;
      var field = document.querySelector('.hoc-field[data-name="' + param.name + '"]');
      if (!field) return;
      var value = params[param.name];
      switch (param.type) {
        case "BOOLEAN":
          field.querySelector("input").checked = !!value;
          break;
        case "MULTISELECT":
          Array.prototype.forEach.call(field.querySelectorAll("input"), function (input) {
            input.checked = Array.isArray(value) && value.indexOf(input.value) >= 0;
          });
          break;
        case "STRINGS":
          field.querySelector("textarea").value = Array.isArray(value) ? value.join("\n") : (value || "");
          break;
        default:
          var input = field.querySelector("input, select, textarea");
          if (input) input.value = value === null || value === undefined ? "" : value;
      }
    });
    applyVisibility();
    updateRunButton();
  }

  function dryRunParam() {
    return state.schema && state.schema.params.filter(function (p) { return p.name === "delete_TF" && p.type === "BOOLEAN"; })[0];
  }

  function isRealRun() {
    var param = dryRunParam();
    if (!param) return state.schema ? state.schema.destructive : false;
    var model = readForm();
    return evalCondition(param.visibilityCondition, model) && !!model.delete_TF;
  }

  function onFormEdit(event) {
    applyVisibility();
    var field = event.target && event.target.closest ? event.target.closest(".hoc-field") : null;
    if (field && field.classList.contains("invalid")) setFieldError(field.getAttribute("data-name"), "");
    updateRunButton();
  }

  function renderField(param) {
    var inputs;
    var name = param.name;
    var dflt = param.defaultValue;
    switch (param.type) {
      case "INT":
      case "DOUBLE":
        inputs = [el("input", { type: "number", name: name, step: param.type === "INT" ? "1" : "any",
                                value: dflt !== undefined ? dflt : "" })];
        break;
      case "BOOLEAN":
        if (name === "delete_TF") {
          // the dry-run / real-run decision gets a switch so it cannot be overlooked
          inputs = [el("label", { class: "hoc-switch" }, [
            el("input", { type: "checkbox", name: name, checked: dflt ? "checked" : null, role: "switch" }),
            el("span", { class: "hoc-switch-track", "aria-hidden": "true" }),
            el("span", { class: "hoc-switch-text", "data-switch-text": name })
          ])];
        } else {
          inputs = [el("input", { type: "checkbox", name: name, checked: dflt ? "checked" : null })];
        }
        break;
      case "SELECT":
        inputs = [el("select", { name: name }, (param.choices || []).map(function (choice) {
          return el("option", { value: choice.value, text: choice.label || choice.value,
                                selected: String(choice.value) === String(dflt) ? "selected" : null });
        }))];
        break;
      case "MULTISELECT":
        inputs = [el("div", { class: "hoc-checklist", "data-multiselect": name }, (param.choices || []).map(function (choice) {
          var checked = Array.isArray(dflt) && dflt.indexOf(choice.value) >= 0;
          return el("label", {}, [
            el("input", { type: "checkbox", name: name, value: choice.value, checked: checked ? "checked" : null }),
            el("span", { class: "hoc-choice-text", text: choice.label || choice.value })
          ]);
        }))];
        break;
      case "STRINGS":
        inputs = [el("textarea", { name: name, "data-strings": "1", placeholder: "one value per line",
                                   text: Array.isArray(dflt) ? dflt.join("\n") : "" })];
        break;
      case "TEXTAREA":
        inputs = [el("textarea", { name: name, text: dflt || "" })];
        break;
      case "PASSWORD":
        inputs = [el("input", { type: "password", name: name, value: dflt || "" })];
        break;
      default:
        inputs = [el("input", { type: "text", name: name, value: dflt !== undefined ? dflt : "" })];
    }
    var help = param.description ? [el("div", { class: "hoc-help", text: param.description })] : [];
    var labelChildren = [document.createTextNode(param.label || name)];
    if (param.mandatory) labelChildren.push(el("span", { class: "hoc-req", text: "*", title: "required" }));
    var error = el("div", { class: "hoc-field-error", role: "alert", hidden: "hidden" });
    return el("div", { class: "hoc-field", "data-name": name, "data-condition": param.visibilityCondition || "",
                       "data-mandatory": param.mandatory ? "1" : "" }, [
      el("label", {}, labelChildren),
      el("div", { class: "hoc-input" }, inputs.concat(help, [error]))
    ]);
  }

  function isEmptyValue(param, value) {
    switch (param.type) {
      case "INT":
      case "DOUBLE": return value === null || value === undefined || isNaN(value);
      case "BOOLEAN": return false;
      case "MULTISELECT":
      case "STRINGS": return !value || value.length === 0;
      default: return value === undefined || value === null || String(value).trim() === "";
    }
  }

  function setFieldError(name, message) {
    var field = document.querySelector('.hoc-field[data-name="' + name + '"]');
    if (!field) return;
    var error = field.querySelector(".hoc-field-error");
    error.textContent = message || "";
    error.hidden = !message;
    field.classList.toggle("invalid", !!message);
    Array.prototype.forEach.call(field.querySelectorAll("input, select, textarea"), function (input) {
      if (message) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
    });
  }

  // Mandatory visible fields must have a value; returns the name of the first invalid one or null.
  function validateForm() {
    var model = readForm();
    var firstInvalid = null;
    (state.schema ? state.schema.params : []).forEach(function (param) {
      var visible = evalCondition(param.visibilityCondition, model);
      var invalid = visible && param.mandatory && isEmptyValue(param, model[param.name]);
      setFieldError(param.name, invalid ? "This field is required." : "");
      if (invalid && !firstInvalid) firstInvalid = param.name;
    });
    if (firstInvalid) {
      var field = document.querySelector('.hoc-field[data-name="' + firstInvalid + '"]');
      var input = field && field.querySelector("input, select, textarea");
      if (input) input.focus();
    }
    return firstInvalid;
  }

  function readForm() {
    var model = {};
    (state.schema ? state.schema.params : []).forEach(function (param) {
      var field = document.querySelector('.hoc-field[data-name="' + param.name + '"]');
      if (!field) return;
      switch (param.type) {
        case "BOOLEAN":
          model[param.name] = field.querySelector("input").checked;
          break;
        case "MULTISELECT":
          model[param.name] = Array.prototype.map.call(field.querySelectorAll("input:checked"), function (i) { return i.value; });
          break;
        case "STRINGS":
          model[param.name] = field.querySelector("textarea").value.split("\n")
            .map(function (s) { return s.trim(); }).filter(function (s) { return s; });
          break;
        case "INT":
          model[param.name] = field.querySelector("input").value === "" ? null : parseInt(field.querySelector("input").value, 10);
          break;
        case "DOUBLE":
          model[param.name] = field.querySelector("input").value === "" ? null : parseFloat(field.querySelector("input").value);
          break;
        default:
          model[param.name] = (field.querySelector("input, select, textarea") || {}).value;
      }
    });
    return model;
  }

  function applyVisibility() {
    var model = readForm();
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-field"), function (field) {
      field.hidden = !evalCondition(field.getAttribute("data-condition"), model);
    });
  }

  function visibleParams() {
    // only send what the user can see, like DSS does for hidden params
    var model = readForm();
    var params = {};
    (state.schema ? state.schema.params : []).forEach(function (param) {
      if (evalCondition(param.visibilityCondition, model)) params[param.name] = model[param.name];
    });
    return params;
  }

  function updateRunButton() {
    var running = state.job && state.job.active;
    var allowed = state.context && state.context.allowed;
    var button = $("hoc-run");
    button.disabled = !allowed || !!running || !state.feature;
    $("hoc-run-hint").textContent = !allowed ? "Disabled outside the admin project"
      : running ? "A job is running; wait for it to finish" : "";
    var real = isRealRun();
    var hasSwitch = !!dryRunParam();
    button.textContent = hasSwitch ? (real ? "Delete for real" : "Run dry run") : "Run";
    button.classList.toggle("danger", hasSwitch && real);
    var switchText = document.querySelector('[data-switch-text="delete_TF"]');
    if (switchText) switchText.textContent = real ? "Delete for real" : "Dry run (list only)";
    $("hoc-rerun").hidden = !(state.job && !state.job.active);
  }

  // ---- confirmation ---------------------------------------------------------------
  function describeValue(param, value) {
    if (Array.isArray(value)) {
      var labels = (param.choices || []);
      return value.map(function (v) {
        var choice = labels.filter(function (c) { return String(c.value) === String(v); })[0];
        return choice ? (choice.label || v) : v;
      }).join(", ") || "(none)";
    }
    if (typeof value === "boolean") return value ? "yes" : "no";
    if (param.choices) {
      var match = param.choices.filter(function (c) { return String(c.value) === String(value); })[0];
      if (match) return match.label || String(value);
    }
    return value === null || value === undefined || value === "" ? "(empty)" : String(value);
  }

  // Resolves to true when the user confirms. Uses the in-page dialog, or window.confirm without <dialog>.
  function confirmRun(schema, params, real) {
    var dialog = $("hoc-confirm");
    var text = schema.confirm || "This action changes the instance.";
    if (typeof HTMLDialogElement !== "function" || !dialog.showModal) {
      var summary = Object.keys(params).map(function (k) { return k + " = " + JSON.stringify(params[k]); }).join("\n");
      return Promise.resolve(window.confirm(text + "\n\n" + schema.label + "\n" + summary + "\n\nRun it?"));
    }
    $("hoc-confirm-title").textContent = (real && dryRunParam() ? "Delete for real: " : "Confirm: ") + schema.label;
    $("hoc-confirm-text").textContent = text;
    var table = $("hoc-confirm-params");
    table.innerHTML = "";
    schema.params.forEach(function (param) {
      if (!(param.name in params)) return;
      table.appendChild(el("tr", {}, [
        el("th", { text: param.label || param.name }),
        el("td", { text: describeValue(param, params[param.name]) })
      ]));
    });
    dialog.classList.toggle("danger", !!real);
    $("hoc-confirm-ok").textContent = real && dryRunParam() ? "Delete for real" : "Run";
    return new Promise(function (resolve) {
      function done(ok) {
        $("hoc-confirm-ok").removeEventListener("click", onOk);
        $("hoc-confirm-cancel").removeEventListener("click", onCancel);
        dialog.removeEventListener("close", onClose);
        if (dialog.open) dialog.close();
        resolve(ok);
      }
      function onOk() { done(true); }
      function onCancel() { done(false); }
      function onClose() { done(false); }
      $("hoc-confirm-ok").addEventListener("click", onOk);
      $("hoc-confirm-cancel").addEventListener("click", onCancel);
      dialog.addEventListener("close", onClose);
      dialog.showModal();
      $("hoc-confirm-cancel").focus();
    });
  }

  // ---- running ----------------------------------------------------------------
  function runFeature() {
    if (!state.schema || $("hoc-run").disabled) return;
    if (validateForm()) return;
    var params = visibleParams();
    var real = isRealRun();
    var needsConfirm = state.schema.destructive && ("delete_TF" in params ? !!params.delete_TF : true);
    var proceed = needsConfirm ? confirmRun(state.schema, params, real) : Promise.resolve(true);
    proceed.then(function (ok) {
      if (!ok) return;
      banner("");
      $("hoc-run-error").hidden = true;
      $("hoc-run").disabled = true;
      return post("/api/jobs", { feature_id: state.feature, params: params }).then(function (body) {
        showJob(body.job, true);
        refreshHistory();
      }).catch(function (err) {
        if (err.status === 409 && err.body && err.body.job) {
          banner("Another job is still running: " + err.body.job.label, true);
          showJob(err.body.job, true);
        } else {
          var error = $("hoc-run-error");
          error.textContent = "Could not start: " + err.message;
          error.hidden = false;
        }
        updateRunButton();
      });
    });
  }

  function showJob(job, follow) {
    var isNew = !state.job || state.job.id !== job.id;
    state.job = job;
    state.logLength = 0;
    state.lastStatus = null;
    $("hoc-log").textContent = "";
    $("hoc-job").hidden = false;
    showTab("run");
    renderJob(job);
    if (follow && job.active) startPolling(job.id);
    else stopPolling();
    updateRunButton();
    if (isNew) $("hoc-job").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Reopen a job: select its feature, prefill the form with its parameters, then show the job.
  function openJob(jobSummary) {
    api("/api/jobs/" + jobSummary.id).then(function (full) {
      var job = full.job;
      return selectFeature(job.feature_id, job.params).then(function () { showJob(job, job.active); });
    }).catch(function (err) { banner("Could not open the job: " + err.message, true); });
  }

  function rerunCurrent() {
    if (!state.job) return;
    var job = state.job;
    selectFeature(job.feature_id, job.params).then(function () {
      $("hoc-feature").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function copyLog() {
    var text = $("hoc-log").textContent;
    var done = function () {
      var button = $("hoc-copy-log");
      button.textContent = "Copied";
      setTimeout(function () { button.textContent = "Copy"; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else { fallbackCopy(text); done(); }
  }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } catch (e) { /* nothing more to try */ }
    document.body.removeChild(area);
  }

  function renderJob(job) {
    $("hoc-job-label").textContent = job.label;
    var status = $("hoc-job-status");
    status.textContent = job.status;
    status.className = "hoc-status " + job.status;

    var bar = $("hoc-progress-bar");
    var label;
    if (job.progress_target) {
      var pct = Math.min(100, Math.round(100 * job.progress / job.progress_target));
      bar.className = "hoc-progress-bar";
      bar.style.setProperty("--pct", String(pct));
      label = job.progress + " / " + job.progress_target;
    } else if (job.active) {
      bar.className = "hoc-progress-bar indeterminate";
      label = "running";
    } else {
      bar.className = "hoc-progress-bar";
      bar.style.setProperty("--pct", "100");
      label = job.status;
    }
    // dark copy over the track, white copy clipped to the fill (see style.css)
    $("hoc-progress-text").textContent = label;
    $("hoc-progress-text-light").textContent = label;

    if (job.log && job.log.length) {
      var pre = $("hoc-log");
      pre.textContent += (pre.textContent ? "\n" : "") + job.log.join("\n");
      pre.scrollTop = pre.scrollHeight;
    }
    if (job.log_length !== undefined) state.logLength = job.log_length;
    $("hoc-log-count").textContent = state.logLength ? String(state.logLength) : "";
    if (job.status !== state.lastStatus) {
      // open while running and on failure, folded away once a job succeeded
      $("hoc-log-details").open = job.active || job.status === "failed";
      state.lastStatus = job.status;
    }

    var error = $("hoc-error");
    error.hidden = !job.error;
    error.textContent = job.error || "";
    $("hoc-result").innerHTML = job.result_html || "";
    updateRunningDots();
  }

  function startPolling(jobId) {
    stopPolling();
    state.poller = setInterval(function () {
      api("/api/jobs/" + jobId + "?log_from=" + state.logLength).then(function (body) {
        var job = body.job;
        state.job = job;
        renderJob(job);
        if (!job.active) {
          stopPolling();
          updateRunButton();
          refreshHistory();
        }
      }).catch(function (err) {
        banner("Lost contact with the backend: " + err.message, true);
        stopPolling();
      });
    }, POLL_MS);
  }

  function stopPolling() {
    if (state.poller) clearInterval(state.poller);
    state.poller = null;
  }

  // ---- history ----------------------------------------------------------------
  function refreshHistory() {
    api("/api/jobs?limit=50").then(function (body) {
      var list = $("hoc-history");
      list.innerHTML = "";
      if (!body.jobs.length) {
        list.appendChild(el("li", { class: "hoc-muted", text: "No job yet in this backend session." }));
      }
      body.jobs.forEach(function (job) {
        var cells = [
          el("span", { class: "hoc-when", text: formatTime(job.started_at || job.created_at) }),
          el("span", { class: "hoc-duration", text: formatDuration(job) }),
          el("span", { class: "hoc-status " + job.status, text: job.status }),
          el("span", { class: "hoc-history-label", text: job.label })
        ];
        if (job.params && job.params.delete_TF === false) cells.push(el("span", { class: "hoc-badge", text: "dry run" }));
        if (job.destructive) cells.push(el("span", { class: "hoc-flag", text: "⚠", title: "changed the instance" }));
        list.appendChild(el("li", {
          "data-job": job.id,
          class: state.job && state.job.id === job.id ? "active" : "",
          title: paramsTooltip(job.params),
          onclick: function () { openJob(job); }
        }, cells));
      });
      state.historyCount = body.jobs.length;
      $("hoc-history-count").textContent = body.jobs.length ? String(body.jobs.length) : "";
      if (body.current && (!state.job || state.job.id !== body.current.id)) {
        showJob(body.current, true);
      } else {
        updateRunningDots();
      }
    }).catch(function () { /* history is best effort */ });
  }

  // ---- boot -------------------------------------------------------------------
  function boot() {
    $("hoc-run").addEventListener("click", runFeature);
    // Enter inside a field runs the feature instead of letting the browser reload the page
    $("hoc-form").addEventListener("submit", function (event) { event.preventDefault(); runFeature(); });
    $("hoc-form").addEventListener("input", onFormEdit);
    $("hoc-form").addEventListener("change", onFormEdit);
    $("hoc-collapse").addEventListener("click", function () {
      setSidebarCollapsed(!$("hoc-sidebar").classList.contains("collapsed"));
    });
    $("hoc-hamburger").addEventListener("click", function () {
      setDrawerOpen(!$("hoc-sidebar").classList.contains("open"));
    });
    $("hoc-backdrop").addEventListener("click", function () { setDrawerOpen(false); });
    $("hoc-rerun").addEventListener("click", rerunCurrent);
    $("hoc-copy-log").addEventListener("click", function (event) { event.preventDefault(); copyLog(); });
    $("hoc-confirm").addEventListener("click", function (event) {   // click on the backdrop closes
      if (event.target === $("hoc-confirm")) $("hoc-confirm").close();
    });
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-tab"), function (tab) {
      tab.addEventListener("click", function () { showTab(tab.getAttribute("data-tab")); });
    });
    if (loadPrefs().sidebarCollapsed) setSidebarCollapsed(true);
    loadContext();
  }

  function loadContext() {
    banner("");
    api("/api/context").then(function (context) {
      state.context = context;
      $("hoc-project").textContent = "project " + context.project_key;
      $("hoc-sidebar-project").textContent = context.project_key;
      renderMenu(context);
      if (!context.allowed) {
        banner("This console only runs inside project " + context.admin_project_key +
               " (this webapp lives in " + context.project_key + "). The menu is shown but Run is disabled.");
      }
      updateRunButton();
      refreshHistory();
    }).catch(function (err) {
      banner("Backend not reachable: " + err.message + ". Start the webapp backend, then retry.", true,
             { label: "Retry", onclick: loadContext });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
