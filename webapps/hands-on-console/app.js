/* Hands-on Workshop Console: front end of the plugin webapp.
 *
 * Talks to backend.py through the /api/... routes (see managehandsonenv.webapp.api).
 * Feature buttons and forms are built from what the backend sends, so a feature
 * added to managehandsonenv.features shows up here without any JS change.
 */
(function () {
  "use strict";

  var POLL_MS = 1000;
  var state = { context: null, feature: null, schema: null, job: null, poller: null, logLength: 0 };

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

  function banner(message, isError) {
    var node = $("hoc-banner");
    if (!message) { node.hidden = true; return; }
    node.textContent = message;
    node.className = "hoc-banner" + (isError ? " hoc-banner-error" : "");
    node.hidden = false;
  }

  function formatTime(seconds) {
    if (!seconds) return "";
    var d = new Date(seconds * 1000);
    return d.toTimeString().slice(0, 8);
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

  // ---- button bar -------------------------------------------------------------
  function renderButtons(context) {
    var nav = $("hoc-buttons");
    nav.innerHTML = "";
    context.categories.forEach(function (category, index) {
      var buttons = category.features.map(function (feature) {
        return el("button", {
          type: "button",
          class: "hoc-feature-btn" + (feature.destructive ? " destructive" : ""),
          "data-feature": feature.id,
          title: feature.description || "",
          text: feature.label,
          onclick: function () { selectFeature(feature.id); }
        });
      });
      nav.appendChild(el("div", { class: "hoc-group hoc-group-" + index }, [
        el("div", { class: "hoc-group-name", text: category.name }),
        el("div", { class: "hoc-group-buttons" }, buttons)
      ]));
    });
  }

  // ---- form -------------------------------------------------------------------
  function selectFeature(featureId) {
    Array.prototype.forEach.call(document.querySelectorAll(".hoc-feature-btn"), function (button) {
      button.classList.toggle("active", button.getAttribute("data-feature") === featureId);
    });
    api("/api/features/" + encodeURIComponent(featureId) + "/form").then(function (schema) {
      state.feature = featureId;
      state.schema = schema;
      renderForm(schema);
    }).catch(function (err) { banner("Could not load the form: " + err.message, true); });
  }

  function renderForm(schema) {
    $("hoc-empty").hidden = true;
    $("hoc-feature").hidden = false;
    $("hoc-feature-label").textContent = schema.label;
    $("hoc-feature-description").textContent = schema.description || "";
    var form = $("hoc-form");
    form.innerHTML = "";
    schema.params.forEach(function (param) { form.appendChild(renderField(param)); });
    form.addEventListener("input", applyVisibility);
    form.addEventListener("change", applyVisibility);
    applyVisibility();
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
        inputs = [el("input", { type: "checkbox", name: name, checked: dflt ? "checked" : null })];
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
            document.createTextNode(choice.label || choice.value)
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
    return el("div", { class: "hoc-field", "data-name": name, "data-condition": param.visibilityCondition || "" }, [
      el("label", { text: param.label || name + (param.mandatory ? " *" : "") }),
      el("div", { class: "hoc-input" }, inputs.concat(help))
    ]);
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
    $("hoc-run").disabled = !allowed || !!running || !state.feature;
    $("hoc-run-hint").textContent = !allowed ? "Disabled outside the admin project"
      : running ? "A job is running; wait for it to finish" : "";
  }

  // ---- running ----------------------------------------------------------------
  function runFeature() {
    if (!state.schema) return;
    var params = visibleParams();
    var needsConfirm = state.schema.destructive && ("delete_TF" in params ? !!params.delete_TF : true);
    if (needsConfirm) {
      var summary = Object.keys(params).map(function (k) { return k + " = " + JSON.stringify(params[k]); }).join("\n");
      if (!window.confirm((state.schema.confirm || "This action changes the instance.") +
                          "\n\n" + state.schema.label + "\n" + summary + "\n\nRun it?")) return;
    }
    banner("");
    $("hoc-run").disabled = true;
    post("/api/jobs", { feature_id: state.feature, params: params }).then(function (body) {
      showJob(body.job, true);
      refreshHistory();
    }).catch(function (err) {
      if (err.status === 409 && err.body && err.body.job) {
        banner("Another job is still running: " + err.body.job.label, true);
        showJob(err.body.job, true);
      } else {
        banner("Could not start: " + err.message, true);
      }
      updateRunButton();
    });
  }

  function showJob(job, follow) {
    state.job = job;
    state.logLength = 0;
    $("hoc-log").textContent = "";
    $("hoc-job").hidden = false;
    renderJob(job);
    if (follow && job.active) startPolling(job.id);
    else stopPolling();
    updateRunButton();
  }

  function renderJob(job) {
    $("hoc-job-label").textContent = job.label;
    var status = $("hoc-job-status");
    status.textContent = job.status;
    status.className = "hoc-status " + job.status;

    var bar = $("hoc-progress-bar");
    var text = $("hoc-progress-text");
    if (job.progress_target) {
      var pct = Math.min(100, Math.round(100 * job.progress / job.progress_target));
      bar.className = "hoc-progress-bar";
      bar.style.width = pct + "%";
      text.textContent = job.progress + " / " + job.progress_target;
    } else if (job.active) {
      bar.className = "hoc-progress-bar indeterminate";
      text.textContent = "running";
    } else {
      bar.className = "hoc-progress-bar";
      bar.style.width = "100%";
      text.textContent = job.status;
    }

    if (job.log && job.log.length) {
      var pre = $("hoc-log");
      pre.textContent += (pre.textContent ? "\n" : "") + job.log.join("\n");
      pre.scrollTop = pre.scrollHeight;
    }
    if (job.log_length !== undefined) state.logLength = job.log_length;

    var error = $("hoc-error");
    error.hidden = !job.error;
    error.textContent = job.error || "";
    $("hoc-result").innerHTML = job.result_html || "";
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
    api("/api/jobs?limit=20").then(function (body) {
      var list = $("hoc-history");
      list.innerHTML = "";
      if (!body.jobs.length) {
        list.appendChild(el("li", { class: "hoc-muted", text: "No job yet in this backend session." }));
      }
      body.jobs.forEach(function (job) {
        list.appendChild(el("li", {
          onclick: function () {
            api("/api/jobs/" + job.id).then(function (full) { showJob(full.job, full.job.active); });
          }
        }, [
          el("span", { class: "hoc-when", text: formatTime(job.started_at || job.created_at) }),
          el("span", { class: "hoc-status " + job.status, text: job.status }),
          el("span", { text: job.label + (job.destructive ? " ⚠" : "") })
        ]));
      });
      if (body.current && (!state.job || state.job.id !== body.current.id)) {
        showJob(body.current, true);
      }
    }).catch(function () { /* history is best effort */ });
  }

  // ---- boot -------------------------------------------------------------------
  function boot() {
    $("hoc-run").addEventListener("click", runFeature);
    api("/api/context").then(function (context) {
      state.context = context;
      $("hoc-project").textContent = "project " + context.project_key;
      renderButtons(context);
      if (!context.allowed) {
        banner("This console only runs inside project " + context.admin_project_key +
               " (this webapp lives in " + context.project_key + "). Buttons are shown but Run is disabled.");
      }
      updateRunButton();
      refreshHistory();
    }).catch(function (err) {
      banner("Backend not reachable: " + err.message + ". Start the webapp backend and reload.", true);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
