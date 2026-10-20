/*
 * The Intelligence Agency (theintelligenceagency.net) — Frontend & Mobile PWA Application
 * Engineered by Critical Softworks
 */

const TOKEN_KEY = "tia_session_token";
let currentDashboard = null;
let deferredPwaPrompt = null;

// ---------------------------------------------------------------------------
// 1. Critical Softworks Animated Boot Splash Screen (60 FPS Canvas)
// ---------------------------------------------------------------------------
function runCriticalSoftworksSplash() {
  const overlay = document.getElementById("cs-splash-overlay");
  const canvas = document.getElementById("splash-canvas");
  if (!overlay || !canvas) return;

  // Skip splash if already shown in this tab session
  if (sessionStorage.getItem("tia_splash_shown") === "1") {
    overlay.classList.add("hidden");
    return;
  }
  sessionStorage.setItem("tia_splash_shown", "1");

  const ctx = canvas.getContext("2d");
  const startTime = performance.now();
  const duration = 1650;

  function drawFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / duration);
    const phase = elapsed * 0.005;

    ctx.fillStyle = "#060b14";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle telemetry grid
    ctx.strokeStyle = "rgba(22, 48, 82, 0.35)";
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 34) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 34) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Dual Telemetry Sine Waves
    ctx.strokeStyle = "rgba(0, 229, 255, 0.45)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let x = 0; x <= canvas.width; x += 6) {
      const y = 160 + Math.sin(x * 0.018 + phase) * 24 * Math.sin(phase * 0.5);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.strokeStyle = "rgba(0, 240, 118, 0.35)";
    ctx.beginPath();
    for (let x = 0; x <= canvas.width; x += 6) {
      const y = 175 + Math.cos(x * 0.014 - phase * 1.2) * 18;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Orbital Radar Ring & Hex Emblem
    const cx = canvas.width / 2;
    const cy = 112;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(phase * 0.6);
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, 44, 0, Math.PI * 1.35);
    ctx.stroke();
    ctx.strokeStyle = "#00f076";
    ctx.beginPath();
    ctx.arc(0, 0, 52, Math.PI, Math.PI * 1.85);
    ctx.stroke();
    ctx.restore();

    // Titles
    ctx.fillStyle = "#00e5ff";
    ctx.font = "bold 20px monospace";
    ctx.textAlign = "center";
    ctx.fillText("THE INTELLIGENCE AGENCY // HQ", cx, 206);

    ctx.fillStyle = "#7ea0c4";
    ctx.font = "11px monospace";
    ctx.fillText("CRITICAL SOFTWORKS • SIGINT & CRYPTANALYSIS NETWORK", cx, 228);

    // Status Telemetry
    const stages = [
      "INITIALIZING TLS 1.3 QUANTUM-RESISTANT HANDSHAKE...",
      "MOUNTING DECLASSIFIED FOIA & SIGINT ARCHIVES...",
      "VERIFYING @THEINTELLIGENCEAGENCY.NET CALLSIGN REGISTRY...",
      "TERMINAL CLEARANCE VERIFIED // ONLINE."
    ];
    const stageIdx = Math.min(stages.length - 1, Math.floor(progress * stages.length));
    ctx.fillStyle = "#00f076";
    ctx.font = "bold 11px monospace";
    ctx.fillText(stages[stageIdx], cx, 268);

    // Progress Bar
    const barW = 460;
    const barX = (canvas.width - barW) / 2;
    ctx.strokeStyle = "#1d3b63";
    ctx.strokeRect(barX, 282, barW, 10);
    ctx.fillStyle = "#00e5ff";
    ctx.fillRect(barX + 1, 283, (barW - 2) * progress, 8);

    if (progress < 1) {
      requestAnimationFrame(drawFrame);
    } else {
      overlay.classList.add("hidden");
    }
  }

  requestAnimationFrame(drawFrame);
}

// ---------------------------------------------------------------------------
// 2. Fallback for <dialog closedby="any"> (Safari / iOS Light-Dismiss)
// ---------------------------------------------------------------------------
function initDialogLightDismissFallbacks() {
  const dialogs = document.querySelectorAll("dialog.cyber-dialog");
  dialogs.forEach((dialog) => {
    if (!("closedBy" in HTMLDialogElement.prototype)) {
      dialog.addEventListener("click", (event) => {
        if (event.target !== dialog) return;
        const rect = dialog.getBoundingClientRect();
        const isDialogContent =
          rect.top <= event.clientY &&
          event.clientY <= rect.top + rect.height &&
          rect.left <= event.clientX &&
          event.clientX <= rect.left + rect.width;
        if (isDialogContent) return;
        dialog.close();
      });
    }
  });
}

function openEnlistModal(planTier = "OPERATIVE_MONTHLY") {
  const dlg = document.getElementById("dlg-enlist");
  const searched = document.getElementById("input-check-callsign")?.value.trim();
  if (searched) {
    document.getElementById("enlist-callsign").value = searched;
  }
  const tierSelect = document.getElementById("enlist-tier");
  if (tierSelect && planTier) {
    tierSelect.value = planTier;
  }
  dlg.showModal();
}
window.openEnlistModal = openEnlistModal;

// ---------------------------------------------------------------------------
// 3. Callsign Availability Checker
// ---------------------------------------------------------------------------
async function checkCallsignAvailability() {
  const input = document.getElementById("input-check-callsign");
  const out = document.getElementById("callsign-check-output");
  const raw = (input.value || "").trim();
  if (!raw) {
    out.style.color = "var(--accent-amber)";
    out.textContent = "Enter a desired callsign (e.g., agent.falcon) first.";
    return;
  }
  out.style.color = "var(--text-accent)";
  out.textContent = "Querying Directorate Callsign Registry...";
  try {
    const res = await fetch(`/api/callsign/check?callsign=${encodeURIComponent(raw)}`);
    const data = await res.json();
    if (data.available) {
      out.style.color = "var(--accent-green)";
      out.textContent = `✔ ${data.reason}`;
    } else {
      out.style.color = "var(--accent-red)";
      out.textContent = `✕ UNAVAILABLE // ${data.reason}`;
    }
  } catch (err) {
    out.style.color = "var(--accent-red)";
    out.textContent = "Error contacting Directorate registry.";
  }
}

// ---------------------------------------------------------------------------
// 4. Dashboard Rendering (Webmail, Cipher Missions, FOIA Vault, Dossier)
// ---------------------------------------------------------------------------
function formatRedactedText(rawText) {
  return rawText.replace(/\[([^\]]+)\]/g, (_, secret) => {
    return `<span class="redacted-bar" title="Click or hover to declassify" onclick="this.classList.toggle('revealed')">[${secret}]</span>`;
  });
}

function renderMessageReader(msg) {
  const reader = document.getElementById("message-reader-container");
  if (!msg) return;
  reader.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem; border-bottom:1px solid #162b47; padding-bottom:0.65rem; margin-bottom:0.75rem;">
      <div>
        <div style="color:var(--text-accent); font-weight:700; font-size:1rem;">${escapeHtml(msg.subject)}</div>
        <div style="color:var(--text-secondary); font-size:0.78rem; margin-top:0.2rem;">
          FROM: ${escapeHtml(msg.sender)} &bull; TO: ${escapeHtml(msg.recipient)} &bull; ${escapeHtml(msg.created_at)}
        </div>
      </div>
      <span class="status-pill" style="margin:0;">${escapeHtml(msg.classification || "INTERNAL AGENCY")}</span>
    </div>
    <div style="white-space:pre-wrap; font-size:0.88rem; color:var(--text-primary); line-height:1.65;">${escapeHtml(msg.body)}</div>
  `;
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadAgentDashboard() {
  const token = localStorage.getItem(TOKEN_KEY);
  const toggleBtn = document.getElementById("btn-toggle-public-hq");
  if (!token) {
    document.getElementById("agent-hq-section").classList.remove("active");
    document.getElementById("public-landing-section").style.display = "block";
    document.getElementById("btn-logout").style.display = "none";
    if (toggleBtn) toggleBtn.style.display = "none";
    document.getElementById("btn-open-login").style.display = "inline-flex";
    document.getElementById("btn-open-enlist").style.display = "inline-flex";
    return;
  }

  try {
    const res = await fetch("/api/agent/dashboard", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      localStorage.removeItem(TOKEN_KEY);
      return loadAgentDashboard();
    }
    const data = await res.json();
    currentDashboard = data;

    document.getElementById("public-landing-section").style.display = "none";
    document.getElementById("agent-hq-section").classList.add("active");
    document.getElementById("btn-logout").style.display = "inline-flex";
    if (toggleBtn) {
      toggleBtn.style.display = "inline-flex";
      toggleBtn.textContent = "🌐 Public Academy Page";
    }
    document.getElementById("btn-open-login").style.display = "none";
    document.getElementById("btn-open-enlist").style.display = "none";

    const a = data.agent;
    document.getElementById("hq-clearance-badge").textContent = `CLEARANCE: ${a.clearance_level} // VERIFIED`;
    document.getElementById("hq-agent-title").textContent = `OPERATIVE: ${a.display_name.toUpperCase()}`;
    document.getElementById("hq-agent-email").textContent = `OFFICIAL AGENCY CHANNEL: ${a.email_address}`;
    document.getElementById("hq-agent-rank").textContent = `RANK: ${a.rank}`;
    document.getElementById("hq-agent-xp").textContent = `XP: ${a.xp} // CLEARANCE ID: ${a.license_key}`;
    document.getElementById("dossier-license-key").textContent = a.license_key;

    // Director Course Studio Access (james.f or DIRECTOR clearance)
    const studioTabBtn = document.getElementById("tab-btn-course-studio");
    if (studioTabBtn) {
      if (a.is_director) {
        studioTabBtn.style.display = "inline-flex";
        initDirectorCourseStudio();
      } else {
        studioTabBtn.style.display = "none";
      }
    }

    // Render Inbox List
    const inboxContainer = document.getElementById("inbox-list-container");
    inboxContainer.innerHTML = "";
    const allMsgs = [...(data.inbox || []), ...(data.sent || [])];
    if (allMsgs.length === 0) {
      inboxContainer.innerHTML = `<div style="color:var(--text-secondary);">No transmissions in vault.</div>`;
    } else {
      allMsgs.forEach((m, idx) => {
        const item = document.createElement("div");
        item.className = "msg-item" + (idx === 0 ? " active" : "");
        const tag = m.folder === "sent" ? "[SENT] " : "[INBOX] ";
        item.innerHTML = `
          <div style="color:var(--text-accent); font-weight:700; font-size:0.83rem;">${escapeHtml(tag + m.subject)}</div>
          <div style="color:var(--text-secondary); font-size:0.74rem; margin-top:0.2rem;">${escapeHtml(m.sender)}</div>
          <div style="color:var(--text-secondary); font-size:0.7rem;">${escapeHtml(m.created_at)}</div>
        `;
        item.addEventListener("click", () => {
          document.querySelectorAll(".msg-item").forEach((el) => el.classList.remove("active"));
          item.classList.add("active");
          renderMessageReader(m);
        });
        inboxContainer.appendChild(item);
      });
      renderMessageReader(allMsgs[0]);
    }

    // Render Missions
    const missionsContainer = document.getElementById("missions-list-container");
    missionsContainer.innerHTML = "";
    (data.missions || []).forEach((m) => {
      const card = document.createElement("div");
      card.className = "intel-card";
      card.style.marginBottom = "1rem";
      const badgeHtml = m.completed
        ? `<span class="status-pill" style="margin:0;">✔ SOLVED (+${m.xp} XP EARNED)</span>`
        : `<span class="status-pill" style="margin:0; border-color:var(--accent-amber); color:var(--accent-amber);">ACTIVE MISSION // +${m.xp} XP</span>`;

      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.5rem;">
          <h3>[${escapeHtml(m.code)}] ${escapeHtml(m.title)}</h3>
          ${badgeHtml}
        </div>
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.5rem;">
          CATEGORY: ${escapeHtml(m.category)} &bull; DIFFICULTY: ${escapeHtml(m.difficulty)}
        </div>
        <p style="margin-bottom:0.5rem;">${escapeHtml(m.briefing)}</p>
        <div class="cipher-box">${escapeHtml(m.cipher_display)}</div>
        <div style="font-size:0.76rem; color:var(--text-secondary); margin-bottom:0.65rem;">
          💡 <strong>Field Hint:</strong> ${escapeHtml(m.hint)}
        </div>
        ${
          m.completed
            ? `<div style="color:var(--accent-green); font-weight:700; font-size:0.82rem;">✔ Commendation logged in your Operative Dossier.</div>`
            : `
          <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
            <input type="text" class="cyber-input" id="ans-${m.id}" placeholder="Enter decoded solution..." style="max-width:320px;" />
            <button type="button" class="btn btn-accent" onclick="submitMissionAnswer('${m.id}')">⚡ Verify Solution</button>
            <span id="status-${m.id}" style="font-size:0.8rem; align-self:center;"></span>
          </div>
        `
        }
      `;
      missionsContainer.appendChild(card);
    });

    // Render FOIA Vault
    const foiaContainer = document.getElementById("foia-list-container");
    foiaContainer.innerHTML = "";
    (data.foia_dossiers || []).forEach((f) => {
      const card = document.createElement("div");
      card.className = "intel-card";
      card.style.marginBottom = "1rem";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.4rem;">
          <h3>${escapeHtml(f.title)}</h3>
          <span class="status-pill" style="margin:0; border-color:var(--accent-red); color:var(--accent-red);">${escapeHtml(f.classification)}</span>
        </div>
        <div style="font-size:0.74rem; color:var(--text-secondary); margin-bottom:0.6rem;">
          DOCUMENT ID: ${escapeHtml(f.doc_number)} &bull; ${escapeHtml(f.date)}
        </div>
        <p>${escapeHtml(f.summary)}</p>
        <div class="cipher-box" style="color:var(--text-primary);">${formatRedactedText(escapeHtml(f.redacted_excerpt))}</div>
      `;
      foiaContainer.appendChild(card);
    });

    // Render Earned Certificates & Academy Courses
    renderAcademySection(data.academy_courses || [], data.certificates || []);

    // Update Dossier clearance plan badge
    const planBadge = document.getElementById("dossier-plan-badge");
    const planStatus = document.getElementById("dossier-plan-status");
    const tierLabels = {
      "CADET_FREE": "PLAN: CADET RECRUIT (FREE)",
      "OPERATIVE_MONTHLY": "PLAN: LEVEL-5 OPERATIVE ($4.99/MO)",
      "OPERATIVE_ANNUAL": "PLAN: OPERATIVE ANNUAL PASS ($39.99/YR)",
      "STATION_CHIEF_LIFETIME": "PLAN: STATION CHIEF (LIFETIME — $69)",
      "DIRECTOR": "PLAN: DIRECTORATE (FULL ACCESS)"
    };
    if (planBadge) planBadge.textContent = tierLabels[a.plan_tier] || `PLAN: ${a.plan_tier || a.clearance_level}`;
    if (planStatus) planStatus.textContent = `Status: Active • ${a.clearance_level}`;

    const portalBtn = document.getElementById("btn-customer-portal");
    if (portalBtn) {
      if (a.stripe_customer_id || (a.plan_tier && a.plan_tier !== "CADET_FREE" && a.plan_tier !== "DIRECTOR")) {
        portalBtn.style.display = "inline-flex";
      } else {
        portalBtn.style.display = "none";
      }
    }
  } catch (err) {
    console.error("Dashboard load error:", err);
  }
}

function buildCourseCurriculumHtml(c, scopePrefix) {
  const totalLessons = c.total_lessons || (c.modules || []).length || 5;
  const doneLessons = c.completed_lessons || 0;
  const progressPct = c.progress_pct || 0;
  const totalDuration = c.estimated_duration || "2.0 Hours (5 Lessons + Cyber Range Lab)";

  const progressHtml = `
    <div class="course-progress-wrap">
      <div class="course-progress-header">
        <span>📚 <strong>CURRICULUM PROGRESS:</strong> <span id="prog-text-${scopePrefix}-${escapeHtml(c.id)}">${doneLessons} / ${totalLessons} Lessons Verified (${progressPct}%)</span></span>
        <span>⏱ ${escapeHtml(totalDuration)}</span>
      </div>
      <div class="course-progress-track">
        <div class="course-progress-fill" id="prog-bar-${scopePrefix}-${escapeHtml(c.id)}" style="width:${progressPct}%;"></div>
      </div>
    </div>
  `;

  const modulesHtml = (c.modules || [])
    .map((m, mIdx) => {
      const lessonId = m.lesson_id || `${c.id}-m${mIdx + 1}`;
      const isDone = !!m.completed;

      // Locked module (Cadet paywall) — show upgrade CTA
      if (m.is_locked) {
        return `
          <div class="lesson-disclosure" style="background:#050d18; border:1px solid #162a44; padding:0.75rem 1rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.3rem;">
            <span>🔒 <strong>${escapeHtml(m.title)}</strong> <span style="color:var(--text-secondary); font-size:0.73rem;">${escapeHtml(m.duration || "")}</span></span>
            <span style="font-size:0.72rem; color:var(--accent-amber);">🛡 Clearance Upgrade Required</span>
            <button type="button" class="btn btn-accent" onclick="startClearanceCheckout('OPERATIVE_MONTHLY')" style="font-size:0.73rem; padding:0.3rem 0.8rem;">
              ⚡ Unlock — Level-5 ($4.99/mo)
            </button>
          </div>`;
      }

      const statusBadge = isDone
        ? `<span id="lesson-badge-${scopePrefix}-${escapeHtml(lessonId)}" style="color:var(--accent-green); font-size:0.76rem;">✔ COMPLETED (+50 XP)</span>`
        : `<span id="lesson-badge-${scopePrefix}-${escapeHtml(lessonId)}" style="color:var(--accent-amber); font-size:0.76rem;">⏳ ${escapeHtml(m.duration || "20 min")} &bull; +50 XP Checkpoint ▾</span>`;

      const objectivesList = (m.objectives || [])
        .map((obj) => `<li>${escapeHtml(obj)}</li>`)
        .join("");

      const objectivesHtml = objectivesList
        ? `
          <div class="objectives-box">
            <div style="color:var(--text-accent); font-size:0.75rem; font-weight:700;">🎯 LESSON LEARNING OBJECTIVES:</div>
            <ul>${objectivesList}</ul>
          </div>
        `
        : "";

      const checkpointHtml = m.checkpoint_q
        ? `
          <div class="checkpoint-box">
            <div style="color:var(--accent-amber); font-size:0.76rem; font-weight:700; margin-bottom:0.3rem;">
              🧩 LESSON CHECKPOINT VERIFICATION (+50 XP)
            </div>
            <div style="color:#ffffff; font-size:0.82rem; margin-bottom:0.5rem;">${escapeHtml(m.checkpoint_q)}</div>
            <div style="display:flex; flex-wrap:wrap; gap:0.45rem; align-items:center;">
              <input
                type="text"
                class="cyber-input"
                id="chk-input-${scopePrefix}-${escapeHtml(lessonId)}"
                style="max-width:290px;"
                placeholder="Type your technical answer..."
                onkeydown="if(event.key==='Enter'){event.preventDefault();submitLessonCheckpoint('${escapeHtml(c.id)}','${escapeHtml(lessonId)}','${scopePrefix}');}"
              />
              <button type="button" class="btn btn-accent" onclick="submitLessonCheckpoint('${escapeHtml(c.id)}','${escapeHtml(lessonId)}','${scopePrefix}')">
                ⚡ Verify Checkpoint (+50 XP)
              </button>
              <button type="button" class="btn" onclick="toggleCheckpointHint('${scopePrefix}-${escapeHtml(lessonId)}')">
                💡 Hint
              </button>
            </div>
            <div id="chk-hint-${scopePrefix}-${escapeHtml(lessonId)}" style="display:none; margin-top:0.45rem; font-size:0.76rem; color:var(--text-secondary);">
              <strong>Field Hint:</strong> ${escapeHtml(m.checkpoint_hint || "")}
            </div>
            <div id="chk-status-${scopePrefix}-${escapeHtml(lessonId)}" style="margin-top:0.45rem; font-size:0.79rem;"></div>
          </div>
        `
        : "";

      return `
        <details class="lesson-disclosure ${isDone ? "lesson-done" : ""}" id="lesson-card-${scopePrefix}-${escapeHtml(lessonId)}" ${mIdx === 0 ? "open" : ""}>
          <summary>
            <span>📖 ${escapeHtml(m.title)}</span>
            ${statusBadge}
          </summary>
          <div class="lesson-body">
            ${objectivesHtml}
            <div class="lesson-theory">${escapeHtml(m.content)}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
              <span style="color:var(--text-accent); font-size:0.74rem; font-weight:700;">💻 REFERENCE IMPLEMENTATION / CLI WALKTHROUGH</span>
              <button type="button" class="btn" style="padding:0.2rem 0.55rem; font-size:0.7rem;" onclick="copyLessonCode(this)">📋 Copy Code</button>
            </div>
            <div class="cipher-box" style="margin:0; font-size:0.78rem; line-height:1.5;">${escapeHtml(m.code_sample)}</div>
            ${checkpointHtml}
          </div>
        </details>
      `;
    })
    .join("");

  let labHtml = "";
  if (c.lab) {
    const chipsHtml = (c.lab.suggested_commands || [])
      .map(
        (cmd) => `
          <button
            type="button"
            class="lab-chip"
            data-course="${escapeHtml(c.id)}"
            data-scope="${scopePrefix}"
            data-cmd="${escapeHtml(cmd)}"
            onclick="runLabChip(this)"
          >▶ ${escapeHtml(cmd)}</button>
        `
      )
      .join("");

    labHtml = `
      <div class="cyber-lab-box">
        <div class="cyber-lab-header">
          <div>
            <span style="color:var(--accent-green); font-weight:700; font-size:0.86rem;">🖥 ${escapeHtml(c.lab.title || "INTERACTIVE CYBER RANGE LAB")}</span>
          </div>
          <span class="status-pill" style="margin:0; border-color:var(--accent-green); color:var(--accent-green);">LIVE SANDBOX // CAPTURE THE FLAG</span>
        </div>
        <div class="cyber-lab-body">
          <p style="color:var(--text-primary); font-size:0.81rem; line-height:1.55; margin-bottom:0.5rem;">
            <strong>Mission Scenario:</strong> ${escapeHtml(c.lab.scenario || "")}
          </p>
          <div style="font-size:0.76rem; color:var(--accent-amber); margin-bottom:0.45rem;">
            <strong>Practical Objective:</strong> ${escapeHtml(c.lab.flag_hint || "Execute the diagnostic commands below to capture FLAG{...}")}
          </div>
          <div style="font-size:0.73rem; color:var(--text-secondary);">Click any command below to execute it in the sandbox (or type a custom command):</div>
          <div class="lab-cmd-chips">${chipsHtml}</div>
          <div class="lab-terminal-screen" id="lab-screen-${scopePrefix}-${escapeHtml(c.id)}">SIGINT CYBER RANGE SANDBOX // ${escapeHtml(c.code)} READY
Type 'help' or click any command chip above to execute live diagnostics and capture the course FLAG{...}.
------------------------------------------------------------------------------</div>
          <div class="lab-prompt-row">
            <span class="lab-prompt-prefix">operative@sigint-lab:~$</span>
            <input
              type="text"
              class="cyber-input"
              id="lab-input-${scopePrefix}-${escapeHtml(c.id)}"
              style="flex:1 1 240px;"
              placeholder="Enter command (e.g. help)..."
              onkeydown="if(event.key==='Enter'){event.preventDefault();execLabCommand('${escapeHtml(c.id)}','${scopePrefix}');}"
            />
            <button type="button" class="btn btn-green" onclick="execLabCommand('${escapeHtml(c.id)}','${scopePrefix}')">▶ Execute</button>
            <button type="button" class="btn" onclick="clearLabScreen('${escapeHtml(c.id)}','${scopePrefix}')">Clear</button>
          </div>
          <div id="lab-flag-banner-${scopePrefix}-${escapeHtml(c.id)}" style="display:none; margin-top:0.6rem; padding:0.55rem 0.75rem; background:#071f15; border:1px solid var(--accent-green); color:var(--accent-green); font-size:0.8rem;"></div>
        </div>
      </div>
    `;
  }

  return { progressHtml, modulesHtml, labHtml };
}

function renderAcademySection(courses, certificates) {
  const certsContainer = document.getElementById("hq-certificates-container");
  const coursesContainer = document.getElementById("hq-academy-courses-container");
  if (!certsContainer || !coursesContainer) return;

  certsContainer.innerHTML = "";
  if (certificates.length > 0) {
    const heading = document.createElement("h4");
    heading.style.cssText = "color:var(--accent-amber); margin-bottom:0.6rem; font-size:0.88rem;";
    heading.textContent = `🏅 YOUR EARNED DIRECTORATE CERTIFICATIONS (${certificates.length})`;
    certsContainer.appendChild(heading);

    certificates.forEach((cert) => {
      const dip = document.createElement("div");
      dip.className = "cert-diploma-card";
      dip.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
          <div>
            <div style="color:var(--accent-amber); font-size:0.75rem; font-weight:700;">OFFICIAL DIRECTORATE DIPLOMA // VERIFIED CREDENTIAL</div>
            <h3 style="color:#ffffff; font-size:1.05rem; margin:0.25rem 0;">🎓 ${escapeHtml(cert.credential_title)}</h3>
            <div style="color:var(--text-accent); font-size:0.82rem;">Awarded to: <strong>${escapeHtml(cert.agent_name)}</strong> (<code>${escapeHtml(cert.agent_email)}</code>)</div>
          </div>
          <span class="status-pill" style="margin:0; border-color:var(--accent-green); color:var(--accent-green);">SCORE: ${cert.score_pct}% // VERIFIED</span>
        </div>
        <div style="margin-top:0.65rem; font-size:0.77rem; color:var(--text-secondary); line-height:1.5;">
          <div><strong>Course Completed:</strong> [${escapeHtml(cert.course_code)}] ${escapeHtml(cert.course_title)}</div>
          <div><strong>Continuing Education:</strong> ${escapeHtml(cert.ceu_credits)} &bull; <strong>Issued:</strong> ${escapeHtml(cert.issued_at)}</div>
          <div><strong>Certificate ID:</strong> <code style="color:var(--accent-amber); font-weight:700;">${escapeHtml(cert.cert_id)}</code> &bull; <strong>SHA-256 Sig:</strong> <code>${escapeHtml(cert.sha256_signature)}</code></div>
        </div>
      `;
      certsContainer.appendChild(dip);
    });
  }

  coursesContainer.innerHTML = "";
  courses.forEach((c, idx) => {
    const details = document.createElement("details");
    details.className = "academy-disclosure";
    details.setAttribute("name", "hq-academy-accordion");
    if (idx === 0) details.open = true;

    const badgeHtml = c.completed
      ? `<span style="color:var(--accent-green); font-size:0.78rem;">✔ CERTIFIED (${escapeHtml(c.certificate?.cert_id || "EARNED")})</span>`
      : `<span style="color:var(--accent-amber); font-size:0.78rem;">5 Lessons + Lab &bull; +${c.xp} XP &bull; ${escapeHtml(c.ceu_credits.split("(")[0].trim())} ▾</span>`;

    const { progressHtml, modulesHtml, labHtml } = buildCourseCurriculumHtml(c, "hq");

    const questionsHtml = (c.exam || [])
      .map(
        (q) => `
        <div class="exam-question-card">
          <div style="color:#ffffff; font-weight:700; font-size:0.84rem; margin-bottom:0.45rem;">${escapeHtml(q.question)}</div>
          ${q.options
            .map(
              (opt) => `
            <label class="exam-option-label">
              <input type="radio" name="exam-${escapeHtml(c.id)}-${escapeHtml(q.q_id)}" value="${escapeHtml(opt.value)}" />
              <span>${escapeHtml(opt.label)}</span>
            </label>
          `
            )
            .join("")}
        </div>
      `
      )
      .join("");

    const examFormInner = `
      <div class="exam-question-card" style="border-color:var(--accent-green);">
        <div style="color:var(--accent-green); font-weight:700; font-size:0.84rem; margin-bottom:0.35rem;">
          🚩 PRACTICAL CYBER RANGE LAB FLAG (REQUIRED FOR CERTIFICATION)
        </div>
        <div style="color:var(--text-secondary); font-size:0.78rem; margin-bottom:0.45rem;">
          Run the diagnostic commands in the Interactive Cyber Range Lab Terminal above to capture this course's <code>FLAG{...}</code> (it will auto-fill below when captured):
        </div>
        <input
          type="text"
          class="cyber-input"
          id="exam-flag-hq-${escapeHtml(c.id)}"
          placeholder="FLAG{...}"
          style="max-width:420px; border-color:var(--accent-green);"
        />
      </div>
      ${questionsHtml}
      <div style="display:flex; flex-wrap:wrap; align-items:center; gap:0.65rem; margin-top:0.65rem;">
        <button type="button" class="btn btn-green" onclick="submitAcademyExam('${escapeHtml(c.id)}', ${(c.exam || []).length})">
          🎓 Submit Lab Flag &amp; 6-Question Exam (+${c.xp} XP)
        </button>
        <span id="exam-status-${escapeHtml(c.id)}" style="font-size:0.82rem;"></span>
      </div>
    `;

    let examSectionHtml = "";
    if (c.exam_locked) {
      examSectionHtml = `
        <div style="margin-top:1.25rem; border-top:1px solid #1b3659; padding-top:1rem;">
          <h4 style="color:var(--accent-amber); font-size:0.92rem; margin-bottom:0.6rem;">
            🔒 FINAL CERTIFICATION EXAM — CLEARANCE UPGRADE REQUIRED
          </h4>
          <div style="padding:0.85rem; background:#050d18; border:1px solid #162a44; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.65rem;">
            <div style="font-size:0.81rem; color:var(--text-primary);">
              🛡 <strong>Certification exams require Level-5 Operative clearance or above.</strong>
              <div style="color:var(--text-secondary); font-size:0.74rem; margin-top:0.3rem;">Upgrade to unlock: ${escapeHtml(c.credential_title)} + SHA-256 signed certificate.</div>
            </div>
            <button type="button" class="btn btn-accent" onclick="startClearanceCheckout('OPERATIVE_MONTHLY')">
              ⚡ Upgrade — Level-5 ($4.99/mo)
            </button>
          </div>
        </div>
      `;
    } else if (c.completed && c.certificate) {
      examSectionHtml = `
        <div style="margin-top:1rem; padding:0.85rem; background:#071914; border:1px solid var(--accent-green); color:var(--accent-green); font-size:0.83rem;">
          ✔ <strong>CERTIFICATION COMPLETE:</strong> You have earned <strong>${escapeHtml(c.credential_title)}</strong> (Certificate ID: <code>${escapeHtml(c.certificate.cert_id)}</code>).
        </div>
        <details class="lesson-disclosure" style="margin-top:0.75rem;">
          <summary>
            <span>📝 Review / Practice 6-Question Certification Exam (${escapeHtml(c.credential_title)})</span>
            <span style="color:var(--text-accent); font-size:0.75rem;">Expand Exam ▾</span>
          </summary>
          <div class="lesson-body">
            ${examFormInner}
          </div>
        </details>
      `;
    } else {
      examSectionHtml = `
        <div style="margin-top:1.25rem; border-top:1px solid #1b3659; padding-top:1rem;">
          <h4 style="color:var(--accent-amber); font-size:0.92rem; margin-bottom:0.6rem;">
            📝 FINAL CERTIFICATION EXAM &amp; LAB FLAG VERIFICATION // ${escapeHtml(c.credential_title)}
          </h4>
          ${examFormInner}
        </div>
      `;
    }

    details.innerHTML = `
      <summary>
        <span>[${escapeHtml(c.code)}] ${escapeHtml(c.title)}</span>
        ${badgeHtml}
      </summary>
      <div class="academy-disclosure-body">
        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.65rem;">
          ${escapeHtml(c.division)} &bull; <strong>Credential:</strong> <span style="color:var(--accent-amber);">${escapeHtml(c.credential_title)}</span> &bull; ${escapeHtml(c.ceu_credits)}
        </div>
        <p style="color:var(--text-secondary); font-size:0.82rem; margin-top:0.35rem;">${escapeHtml(c.summary)}</p>
        ${progressHtml}
        ${modulesHtml}
        ${labHtml}
        ${examSectionHtml}
      </div>
    `;
    coursesContainer.appendChild(details);
  });
}

async function loadPublicAcademyCurriculum() {
  const pubContainer = document.getElementById("public-academy-accordion");
  if (!pubContainer) return;
  try {
    const res = await fetch("/api/academy/courses");
    if (!res.ok) return;
    const data = await res.json();
    const courses = data.courses || [];
    if (!courses.length) return;

    pubContainer.innerHTML = "";
    courses.forEach((c, idx) => {
      const details = document.createElement("details");
      details.className = "academy-disclosure";
      details.setAttribute("name", "public-academy-preview");
      if (idx === 0) details.open = true;

      const { progressHtml, modulesHtml, labHtml } = buildCourseCurriculumHtml(c, "pub");

      details.innerHTML = `
        <summary>
          <span>[${escapeHtml(c.code)}] ${escapeHtml(c.title)}</span>
          <span style="color:var(--accent-green); font-size:0.78rem;">5 Lessons + Live Cyber Range &bull; ${escapeHtml(c.ceu_credits.split("(")[0].trim())} &bull; +${c.xp} XP ▾</span>
        </summary>
        <div class="academy-disclosure-body">
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.65rem;">
            ${escapeHtml(c.division)} &bull; <strong>Earned Credential:</strong> <span style="color:var(--accent-amber);">${escapeHtml(c.credential_title)}</span> &bull; ${escapeHtml(c.ceu_credits)}
          </div>
          <p style="color:var(--text-secondary); font-size:0.82rem; margin-top:0.35rem;">${escapeHtml(c.summary)}</p>
          ${progressHtml}
          ${modulesHtml}
          ${labHtml}
          <div style="margin-top:1rem; padding:0.85rem; background:#081526; border:1px solid var(--border-active); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
            <div style="font-size:0.81rem; color:var(--text-primary);">
              🎓 <strong>Ready to take the 6-Question Certification Exam &amp; claim your SHA-256 signed <code>TIA-CERT-2026</code> diploma?</strong>
            </div>
            <button type="button" class="btn btn-green" onclick="openEnlistModal('OPERATIVE_MONTHLY')">🎖 Enlist or Sign In to Certify &rarr;</button>
          </div>
        </div>
      `;
      pubContainer.appendChild(details);
    });
  } catch (err) {
    console.error("Public curriculum load error:", err);
  }
}

function toggleCheckpointHint(key) {
  const el = document.getElementById(`chk-hint-${key}`);
  if (el) {
    el.style.display = el.style.display === "none" ? "block" : "none";
  }
}
window.toggleCheckpointHint = toggleCheckpointHint;

function copyLessonCode(btn) {
  const box = btn?.parentElement?.nextElementSibling;
  if (!box) return;
  navigator.clipboard.writeText(box.textContent || "");
  const old = btn.textContent;
  btn.textContent = "✔ Copied!";
  setTimeout(() => {
    btn.textContent = old;
  }, 1400);
}
window.copyLessonCode = copyLessonCode;

async function submitLessonCheckpoint(courseId, lessonId, scopePrefix) {
  const key = `${scopePrefix}-${lessonId}`;
  const input = document.getElementById(`chk-input-${key}`);
  const statusEl = document.getElementById(`chk-status-${key}`);
  if (!input || !statusEl) return;

  const answer = input.value.trim();
  if (!answer) {
    statusEl.style.color = "var(--accent-amber)";
    statusEl.textContent = "Enter an answer to verify this lesson checkpoint.";
    return;
  }

  statusEl.style.color = "var(--text-accent)";
  statusEl.textContent = "Verifying lesson checkpoint...";

  const token = localStorage.getItem(TOKEN_KEY) || "";
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const res = await fetch("/api/academy/lesson-checkpoint", {
      method: "POST",
      headers,
      body: JSON.stringify({ course_id: courseId, lesson_id: lessonId, answer })
    });
    const data = await res.json();
    if (data.correct) {
      statusEl.style.color = "var(--accent-green)";
      statusEl.textContent = `✔ ${data.message}`;
      const badge = document.getElementById(`lesson-badge-${key}`);
      if (badge) {
        badge.style.color = "var(--accent-green)";
        badge.textContent = "✔ COMPLETED (+50 XP)";
      }
      const card = document.getElementById(`lesson-card-${key}`);
      if (card) card.classList.add("lesson-done");

      if (typeof data.progress_pct === "number") {
        const bar = document.getElementById(`prog-bar-${scopePrefix}-${courseId}`);
        const txt = document.getElementById(`prog-text-${scopePrefix}-${courseId}`);
        if (bar) bar.style.width = `${data.progress_pct}%`;
        if (txt) txt.textContent = `${data.completed_lessons} / ${data.total_lessons} Lessons Verified (${data.progress_pct}%)`;
      }
      if (data.xp) {
        const xpEl = document.getElementById("hq-xp");
        const rankEl = document.getElementById("hq-rank-badge");
        if (xpEl) xpEl.textContent = `${data.xp} XP`;
        if (rankEl && data.rank) rankEl.textContent = data.rank;
      }
    } else {
      statusEl.style.color = "var(--accent-red)";
      statusEl.textContent = `✖ ${data.message || "Incorrect answer."}`;
    }
  } catch (err) {
    statusEl.style.color = "var(--accent-red)";
    statusEl.textContent = "Network error verifying checkpoint.";
  }
}
window.submitLessonCheckpoint = submitLessonCheckpoint;

function runLabChip(btn) {
  const courseId = btn.getAttribute("data-course");
  const scopePrefix = btn.getAttribute("data-scope") || "hq";
  const cmd = btn.getAttribute("data-cmd") || "";
  const input = document.getElementById(`lab-input-${scopePrefix}-${courseId}`);
  if (input) {
    input.value = cmd;
    execLabCommand(courseId, scopePrefix);
  }
}
window.runLabChip = runLabChip;

function clearLabScreen(courseId, scopePrefix) {
  const screen = document.getElementById(`lab-screen-${scopePrefix}-${courseId}`);
  if (screen) {
    screen.textContent = `SIGINT CYBER RANGE SANDBOX // READY\n------------------------------------------------------------------------------`;
  }
}
window.clearLabScreen = clearLabScreen;

async function execLabCommand(courseId, scopePrefix) {
  const input = document.getElementById(`lab-input-${scopePrefix}-${courseId}`);
  const screen = document.getElementById(`lab-screen-${scopePrefix}-${courseId}`);
  if (!input || !screen) return;

  const command = input.value.trim();
  if (!command) return;

  if (command.toLowerCase() === "clear") {
    clearLabScreen(courseId, scopePrefix);
    input.value = "";
    return;
  }

  screen.textContent += `\n\noperative@sigint-lab:~$ ${command}\n[Executing...]`;
  screen.scrollTop = screen.scrollHeight;
  input.value = "";

  try {
    const res = await fetch("/api/academy/lab-exec", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course_id: courseId, command })
    });
    const data = await res.json();
    const output = data.output || "(No output)";
    screen.textContent = screen.textContent.replace(/\n\[Executing\.\.\.\]$/, `\n${output}`);
    screen.scrollTop = screen.scrollHeight;

    // Detect if a FLAG{...} was captured in the output!
    const flagMatch = output.match(/FLAG\{[A-Z0-9_]+\}/);
    if (flagMatch) {
      const capturedFlag = flagMatch[0];
      const flagInputHq = document.getElementById(`exam-flag-hq-${courseId}`);
      if (flagInputHq) flagInputHq.value = capturedFlag;

      const banner = document.getElementById(`lab-flag-banner-${scopePrefix}-${courseId}`);
      if (banner) {
        banner.style.display = "block";
        banner.innerHTML = `🚩 <strong>PRACTICAL LAB FLAG CAPTURED:</strong> <code>${escapeHtml(capturedFlag)}</code> — Automatically filled into the Certification Exam below!`;
      }
    }
  } catch (err) {
    screen.textContent = screen.textContent.replace(/\n\[Executing\.\.\.\]$/, `\n[ERROR] Failed to reach Cyber Range sandbox API.`);
  }
}
window.execLabCommand = execLabCommand;

async function submitAcademyExam(courseId, totalQuestions = 6) {
  const statusEl = document.getElementById(`exam-status-${courseId}`);
  const token = localStorage.getItem(TOKEN_KEY);
  if (!statusEl || !token) return;

  const flagInput = document.getElementById(`exam-flag-hq-${courseId}`);
  const labFlag = flagInput ? flagInput.value.trim() : "";
  if (!labFlag) {
    statusEl.style.color = "var(--accent-amber)";
    statusEl.textContent = "Please run the Interactive Cyber Range Lab commands above to capture and enter the course FLAG{...} first!";
    return;
  }

  const answers = {};
  const checkedRadios = document.querySelectorAll(`input[name^="exam-${courseId}-"]:checked`);
  checkedRadios.forEach((r) => {
    const prefix = `exam-${courseId}-`;
    if (r.name.startsWith(prefix)) {
      const qid = r.name.substring(prefix.length);
      answers[qid] = r.value;
    }
  });

  if (Object.keys(answers).length < totalQuestions) {
    statusEl.style.color = "var(--accent-amber)";
    statusEl.textContent = `Please select an answer for all ${totalQuestions} exam questions before submitting.`;
    return;
  }

  statusEl.style.color = "var(--text-accent)";
  statusEl.textContent = "Verifying Practical Lab Flag, grading 6-question exam & signing credential...";

  const res = await fetch("/api/academy/exam", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ course_id: courseId, lab_flag: labFlag, answers })
  });
  const data = await res.json();
  if (data.passed) {
    statusEl.style.color = "var(--accent-green)";
    statusEl.textContent = data.message;
    setTimeout(() => loadAgentDashboard(), 900);
  } else {
    statusEl.style.color = "var(--accent-red)";
    statusEl.textContent = data.message || "Exam failed. Review the modules and try again.";
  }
}
window.submitAcademyExam = submitAcademyExam;


async function verifyCertificateId() {
  const input = document.getElementById("input-verify-cert");
  const out = document.getElementById("cert-verify-output");
  if (!input || !out) return;
  const certId = input.value.trim().toUpperCase();
  if (!certId) {
    out.style.color = "var(--accent-amber)";
    out.textContent = "Please enter a TIA-CERT-... Certificate ID to verify.";
    return;
  }
  out.style.color = "var(--text-accent)";
  out.textContent = "Querying Directorate Academy Cryptographic Registry...";
  try {
    const res = await fetch(`/api/certificates/verify?cert_id=${encodeURIComponent(certId)}`);
    const data = await res.json();
    if (res.ok && data.valid && data.certificate) {
      const c = data.certificate;
      out.style.color = "var(--accent-green)";
      out.innerHTML = `
        ✔ <strong>AUTHENTICATED CREDENTIAL:</strong> <code>${escapeHtml(c.cert_id)}</code><br/>
        <strong>Recipient:</strong> ${escapeHtml(c.agent_name)} (<code>${escapeHtml(c.agent_email)}</code>) &bull;
        <strong>Credential:</strong> <span style="color:var(--accent-amber);">${escapeHtml(c.credential_title)}</span><br/>
        <strong>Course:</strong> [${escapeHtml(c.course_code)}] ${escapeHtml(c.course_title)} (${escapeHtml(c.ceu_credits)})<br/>
        <strong>Issued:</strong> ${escapeHtml(c.issued_at)} &bull; <strong>SHA-256 Signature:</strong> <code>${escapeHtml(c.sha256_signature)}</code>
      `;
    } else {
      out.style.color = "var(--accent-red)";
      out.textContent = `✖ ${data.error || "Certificate ID not found."}`;
    }
  } catch (err) {
    out.style.color = "var(--accent-red)";
    out.textContent = "Network error querying verification registry.";
  }
}

async function submitMissionAnswer(missionId) {
  const input = document.getElementById(`ans-${missionId}`);
  const statusEl = document.getElementById(`status-${missionId}`);
  const token = localStorage.getItem(TOKEN_KEY);
  if (!input || !token) return;

  statusEl.style.color = "var(--text-accent)";
  statusEl.textContent = "Verifying...";

  const res = await fetch("/api/missions/solve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ mission_id: missionId, answer: input.value })
  });
  const data = await res.json();
  if (data.correct) {
    statusEl.style.color = "var(--accent-green)";
    statusEl.textContent = data.message;
    setTimeout(() => loadAgentDashboard(), 800);
  } else {
    statusEl.style.color = "var(--accent-red)";
    statusEl.textContent = data.message || "Incorrect solution.";
  }
}
window.submitMissionAnswer = submitMissionAnswer;

// ---------------------------------------------------------------------------
// 5. Display Theme (Tactical vs Modern Sleek) & Event Listeners
// ---------------------------------------------------------------------------

function updateThemeToggleUi(theme) {
  const iconEl = document.getElementById("theme-toggle-icon");
  const textEl = document.getElementById("theme-toggle-text");
  const btn = document.getElementById("btn-theme-toggle");
  if (!btn) return;

  if (theme === "modern") {
    if (iconEl) iconEl.textContent = "🛰";
    if (textEl) textEl.textContent = "Tactical Mode";
    btn.title = "Switch to Tactical Terminal HUD";
  } else {
    if (iconEl) iconEl.textContent = "✨";
    if (textEl) textEl.textContent = "Modern Sleek";
    btn.title = "Switch to Modern Sleek Reader Theme";
  }
}

function initDisplayTheme() {
  const btn = document.getElementById("btn-theme-toggle");
  let currentTheme = "tactical";
  try {
    currentTheme = localStorage.getItem("tia-display-theme") || "tactical";
  } catch (e) {}

  if (currentTheme === "modern") {
    document.documentElement.setAttribute("data-theme", "modern");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  updateThemeToggleUi(currentTheme);

  if (btn) {
    btn.addEventListener("click", () => {
      currentTheme = currentTheme === "modern" ? "tactical" : "modern";
      if (currentTheme === "modern") {
        document.documentElement.setAttribute("data-theme", "modern");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
      try {
        localStorage.setItem("tia-display-theme", currentTheme);
      } catch (e) {}
      updateThemeToggleUi(currentTheme);
    });
  }

  window.addEventListener("storage", (e) => {
    if (e.key === "tia-display-theme") {
      const newTheme = e.newValue || "tactical";
      currentTheme = newTheme;
      if (newTheme === "modern") {
        document.documentElement.setAttribute("data-theme", "modern");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
      updateThemeToggleUi(newTheme);
    }
  });
}
window.initDisplayTheme = initDisplayTheme;

document.addEventListener("DOMContentLoaded", () => {
  initDisplayTheme();
  runCriticalSoftworksSplash();
  initDialogLightDismissFallbacks();
  loadPublicAcademyCurriculum();
  handlePaymentReturn();
  loadAgentDashboard();

  // Register Service Worker for Mobile PWA
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPwaPrompt = e;
    const btnPwa = document.getElementById("btn-install-pwa");
    if (btnPwa) btnPwa.style.display = "inline-flex";
  });

  document.getElementById("btn-install-pwa")?.addEventListener("click", async () => {
    if (!deferredPwaPrompt) return;
    deferredPwaPrompt.prompt();
    await deferredPwaPrompt.userChoice;
    deferredPwaPrompt = null;
  });

  document.getElementById("btn-check-callsign")?.addEventListener("click", checkCallsignAvailability);
  document.getElementById("input-check-callsign")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      checkCallsignAvailability();
    }
  });

  document.getElementById("btn-verify-cert")?.addEventListener("click", verifyCertificateId);
  document.getElementById("input-verify-cert")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      verifyCertificateId();
    }
  });

  // Auto-verify if ?verify=TIA-CERT-... is in URL
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("verify")) {
    const certInput = document.getElementById("input-verify-cert");
    if (certInput) {
      certInput.value = urlParams.get("verify");
      verifyCertificateId();
    }
  }

  document.getElementById("btn-open-instructor-modal")?.addEventListener("click", () => {
    document.getElementById("dlg-instructor")?.showModal();
  });

  document.getElementById("form-instructor")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const statusEl = document.getElementById("inst-status");
    statusEl.style.color = "var(--text-accent)";
    statusEl.textContent = "Transmitting credentials to Directorate Command...";
    const payload = {
      full_name: document.getElementById("inst-name").value,
      email: document.getElementById("inst-email").value,
      credentials: document.getElementById("inst-creds").value,
      proposed_topic: document.getElementById("inst-topic").value,
      background: document.getElementById("inst-bio").value
    };
    const res = await fetch("/api/academy/instructor-apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      statusEl.style.color = "var(--accent-green)";
      statusEl.textContent = `✔ ${data.message}`;
      document.getElementById("form-instructor").reset();
      setTimeout(() => {
        document.getElementById("dlg-instructor")?.close();
        statusEl.textContent = "";
      }, 1500);
    } else {
      statusEl.style.color = "var(--accent-red)";
      statusEl.textContent = `✖ ${data.error || "Submission failed."}`;
    }
  });

  document.getElementById("btn-claim-searched-callsign")?.addEventListener("click", () => {
    openEnlistModal("OPERATIVE_MONTHLY");
  });

  document.getElementById("brand-home-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    const token = localStorage.getItem(TOKEN_KEY);
    const hqSec = document.getElementById("agent-hq-section");
    const pubSec = document.getElementById("public-landing-section");
    const toggleBtn = document.getElementById("btn-toggle-public-hq");
    if (token && currentDashboard) {
      pubSec.style.display = "none";
      hqSec.classList.add("active");
      if (toggleBtn) toggleBtn.textContent = "🌐 Public Academy Page";
    } else {
      hqSec.classList.remove("active");
      pubSec.style.display = "block";
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  document.getElementById("btn-toggle-public-hq")?.addEventListener("click", () => {
    const hqSec = document.getElementById("agent-hq-section");
    const pubSec = document.getElementById("public-landing-section");
    const toggleBtn = document.getElementById("btn-toggle-public-hq");
    if (hqSec.classList.contains("active")) {
      hqSec.classList.remove("active");
      pubSec.style.display = "block";
      toggleBtn.textContent = "📡 Return to Agent HQ";
    } else {
      pubSec.style.display = "none";
      hqSec.classList.add("active");
      toggleBtn.textContent = "🌐 Public Academy Page";
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  document.getElementById("btn-open-enlist")?.addEventListener("click", () => openEnlistModal("OPERATIVE_MONTHLY"));
  document.getElementById("btn-open-login")?.addEventListener("click", () => {
    document.getElementById("dlg-login").showModal();
  });

  document.getElementById("btn-logout")?.addEventListener("click", () => {
    localStorage.removeItem(TOKEN_KEY);
    loadAgentDashboard();
  });

  // HQ Tabs
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".hq-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const pane = document.getElementById(btn.dataset.tab);
      if (pane) pane.classList.add("active");
    });
  });

  // Enlistment Submit
  document.getElementById("form-enlist")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("enlist-error");
    errEl.textContent = "";
    const payload = {
      callsign: document.getElementById("enlist-callsign").value,
      display_name: document.getElementById("enlist-name").value,
      password: document.getElementById("enlist-password").value,
      recovery_email: document.getElementById("enlist-recovery").value,
      plan_tier: document.getElementById("enlist-tier").value
    };
    const res = await fetch("/api/enlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.error || "Enlistment failed.";
      return;
    }
    localStorage.setItem(TOKEN_KEY, data.token);
    document.getElementById("dlg-enlist").close();
    loadAgentDashboard();
  });

  // Login Submit
  document.getElementById("form-login")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("login-error");
    errEl.textContent = "";
    const payload = {
      callsign: document.getElementById("login-callsign").value,
      password: document.getElementById("login-password").value
    };
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.error || "Authentication failed.";
      return;
    }
    localStorage.setItem(TOKEN_KEY, data.token);
    document.getElementById("dlg-login").close();
    loadAgentDashboard();
  });

  // Webmail Compose Drawer
  document.getElementById("btn-toggle-compose")?.addEventListener("click", () => {
    const drawer = document.getElementById("compose-drawer");
    drawer.style.display = drawer.style.display === "none" ? "block" : "none";
  });
  document.getElementById("btn-cancel-compose")?.addEventListener("click", () => {
    document.getElementById("compose-drawer").style.display = "none";
  });
  document.getElementById("btn-refresh-dashboard")?.addEventListener("click", loadAgentDashboard);

  document.getElementById("form-send-mail")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const statusEl = document.getElementById("mail-send-status");
    statusEl.textContent = "Encrypting & transmitting via Amazon SES...";
    const token = localStorage.getItem(TOKEN_KEY);
    const payload = {
      recipient: document.getElementById("mail-to").value,
      subject: document.getElementById("mail-subject").value,
      body: document.getElementById("mail-body").value
    };
    const res = await fetch("/api/mail/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      statusEl.textContent = `✔ Sent! (${data.detail})`;
      document.getElementById("form-send-mail").reset();
      setTimeout(() => {
        document.getElementById("compose-drawer").style.display = "none";
        statusEl.textContent = "";
        loadAgentDashboard();
      }, 900);
    } else {
      statusEl.textContent = `✕ Error: ${data.error || "Failed"}`;
    }
  });

  // Copy License Key
  document.getElementById("btn-copy-license")?.addEventListener("click", () => {
    const keyTxt = document.getElementById("dossier-license-key")?.textContent || "";
    navigator.clipboard.writeText(keyTxt);
    const btn = document.getElementById("btn-copy-license");
    btn.textContent = "✔ Copied to Clipboard!";
    setTimeout(() => (btn.textContent = "📋 Copy License Key"), 1800);
  });
});

// ---------------------------------------------------------------------------
// 6. Director Course Studio (Restricted to Director james.f)
// ---------------------------------------------------------------------------
let studioCourses = [];
let currentStudioCourseId = null;
let studioListenersAttached = false;

async function initDirectorCourseStudio() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return;

  try {
    const res = await fetch("/api/admin/courses", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      console.warn("Studio unauthorized or failed to fetch admin courses.");
      return;
    }
    const data = await res.json();
    studioCourses = data.courses || [];

    const select = document.getElementById("studio-course-select");
    if (!select) return;

    select.innerHTML = "";
    studioCourses.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `[${c.code}] ${c.title}`;
      select.appendChild(opt);
    });

    if (!currentStudioCourseId && studioCourses.length > 0) {
      currentStudioCourseId = studioCourses[0].id;
    }

    if (currentStudioCourseId) {
      select.value = currentStudioCourseId;
      loadCourseIntoStudio(currentStudioCourseId);
    }

    if (!studioListenersAttached) {
      attachStudioListeners();
      studioListenersAttached = true;
    }
  } catch (err) {
    console.error("Failed to initialize Director Course Studio:", err);
  }
}

function attachStudioListeners() {
  document.getElementById("studio-course-select")?.addEventListener("change", (e) => {
    loadCourseIntoStudio(e.target.value);
  });

  document.getElementById("btn-studio-new")?.addEventListener("click", () => {
    const defaultNewCourse = {
      id: "acad-501",
      code: "ACAD-501",
      division: "DIVISION 05 // OFFENSIVE SECURITY & EXPLOITATION",
      title: "New Advanced Cyber & IT Track",
      credential_title: "Certified Defensive Operator (CDO)",
      ceu_credits: "3.5 CEU Credits (NIST NICE: Protect & Defend)",
      xp: 1000,
      estimated_duration: "3.0 Hours (5 Lessons + Cyber Range Lab)",
      summary: "Comprehensive hands-on training track authored in Director Course Studio.",
      modules: [
        {
          lesson_id: "acad-501-m1",
          title: "Module 1: Architecture & Theoretical Foundations",
          duration: "25 min",
          objectives: [
            "Analyze core protocols and trust boundaries",
            "Identify vectors of exploitation and policy controls"
          ],
          content: "Operatives must establish disciplined understanding of protocol internals and defense-in-depth principles before engaging in active operations.",
          code_sample: "# Defensive auditing command\nopenssl s_client -connect target.local:443 -tls1_3",
          checkpoint_q: "Which RFC or standard governs this protocol implementation?",
          checkpoint_a: "8314",
          checkpoint_hint: "Review standard protocol definitions."
        }
      ],
      lab: {
        title: "Interactive Cyber Range Lab: Practical Field Exercise",
        flag: "FLAG{STUDIO_LAB_VERIFIED}",
        scenario: "Investigate target infrastructure, audit running services, and extract verification proof.",
        hint: "Run 'status' and 'audit' commands in the simulator.",
        suggested_commands: ["help", "status", "audit", "extract-flag"],
        custom_commands: {
          "status": "Target host 192.168.10.5 ONLINE. Service auditing active.",
          "audit": "Running security posture verification...\n[VULNERABILITY] Misconfigured permission detected.\nFLAG{STUDIO_LAB_VERIFIED}"
        }
      },
      exam: [
        {
          q_id: "q1",
          question: "1. What is the primary objective of zero-trust verification in this operational environment?",
          options: [
            { value: "VERIFY", label: "A) Never trust, always verify every access request regardless of perimeter" },
            { value: "PERIMETER", label: "B) Rely strictly on perimeter firewalls without endpoint authentication" },
            { value: "SHARED_KEY", label: "C) Use single shared static credentials across internal hosts" },
            { value: "UNENCRYPTED", label: "D) Transmit internal telemetry unencrypted" }
          ],
          answer: "VERIFY",
          explanation: "Zero trust principles require explicit per-session cryptographic authentication."
        }
      ]
    };
    loadCourseIntoStudio(defaultNewCourse);
  });

  document.getElementById("btn-studio-toggle-ai")?.addEventListener("click", () => {
    const drawer = document.getElementById("studio-ai-drawer");
    if (drawer) {
      drawer.style.display = drawer.style.display === "none" ? "block" : "none";
      if (drawer.style.display === "block") {
        document.getElementById("ai-ingest-topic")?.focus();
      }
    }
  });

  document.getElementById("btn-studio-close-ai")?.addEventListener("click", () => {
    const drawer = document.getElementById("studio-ai-drawer");
    if (drawer) drawer.style.display = "none";
  });

  document.getElementById("btn-studio-run-ai")?.addEventListener("click", runAiIngestion);
  document.getElementById("btn-studio-save")?.addEventListener("click", saveStudioCourse);
  document.getElementById("btn-studio-save-bottom")?.addEventListener("click", saveStudioCourse);
  document.getElementById("btn-studio-delete")?.addEventListener("click", deleteStudioCourse);
  document.getElementById("btn-studio-export")?.addEventListener("click", exportStudioJson);

  document.getElementById("btn-studio-add-lesson")?.addEventListener("click", addStudioLesson);
  document.getElementById("btn-studio-add-cmd")?.addEventListener("click", addStudioCommand);
  document.getElementById("btn-studio-add-exam-q")?.addEventListener("click", addStudioExamQuestion);
}

function loadCourseIntoStudio(courseIdOrObj) {
  let c = null;
  if (typeof courseIdOrObj === "string") {
    c = studioCourses.find((x) => x.id === courseIdOrObj);
  } else if (courseIdOrObj && typeof courseIdOrObj === "object") {
    c = courseIdOrObj;
  }

  if (!c) return;
  currentStudioCourseId = c.id || "new-course";

  document.getElementById("st-code").value = c.code || "";
  document.getElementById("st-id").value = c.id || "";
  document.getElementById("st-division").value = c.division || "";
  document.getElementById("st-title").value = c.title || "";
  document.getElementById("st-cred").value = c.credential_title || "";
  document.getElementById("st-ceu").value = c.ceu_credits || "";
  document.getElementById("st-xp").value = c.xp || 500;
  document.getElementById("st-duration").value = c.estimated_duration || "2.5 Hours";
  const freePreviewEl = document.getElementById("st-free-preview");
  if (freePreviewEl) freePreviewEl.value = c.free_preview_count ?? 2;
  document.getElementById("st-summary").value = c.summary || "";

  renderStudioLessons(c.modules || []);

  const lab = c.lab || {};
  document.getElementById("st-lab-title").value = lab.title || "";
  document.getElementById("st-lab-flag").value = lab.flag || lab.practical_flag || "";
  document.getElementById("st-lab-scenario").value = lab.scenario || "";
  document.getElementById("st-lab-hint").value = lab.flag_hint || lab.hint || "";
  document.getElementById("st-lab-chips").value = (lab.suggested_commands || []).join(", ");
  renderStudioCommands(lab.custom_commands || {});

  renderStudioExam(c.exam || []);

  const statusEl = document.getElementById("studio-status-msg");
  if (statusEl) {
    statusEl.style.display = "block";
    statusEl.style.color = "var(--text-accent)";
    statusEl.textContent = `Editing Track [${c.code || "NEW"}] ${c.title || ""}`;
  }
}

function renderStudioLessons(modules) {
  const container = document.getElementById("studio-lessons-list");
  const countEl = document.getElementById("studio-lesson-count");
  if (!container) return;

  container.innerHTML = "";
  if (countEl) countEl.textContent = (modules || []).length;

  (modules || []).forEach((m, idx) => {
    const card = document.createElement("div");
    card.className = "studio-lesson-card";
    card.dataset.index = idx;

    const objectivesText = (m.objectives || []).join("\n");

    card.innerHTML = `
      <div class="studio-card-header">
        <span style="color:var(--text-accent); font-weight:700; font-size:0.84rem;">
          📖 LESSON #${idx + 1}: <span class="st-lesson-title-preview">${escapeHtml(m.title || "Untitled Lesson")}</span>
        </span>
        <div style="display:flex; gap:0.35rem; align-items:center;">
          <button type="button" class="btn" onclick="moveStudioLesson(${idx}, -1)" title="Move Up" style="padding:0.2rem 0.5rem; font-size:0.7rem;">▲</button>
          <button type="button" class="btn" onclick="moveStudioLesson(${idx}, 1)" title="Move Down" style="padding:0.2rem 0.5rem; font-size:0.7rem;">▼</button>
          <button type="button" class="btn btn-red" onclick="deleteStudioLesson(${idx})" title="Delete Lesson" style="padding:0.2rem 0.55rem; font-size:0.7rem;">🗑</button>
        </div>
      </div>
      <div class="grid-3" style="margin-bottom:0.5rem;">
        <div class="form-field">
          <label>LESSON ID / SLUG</label>
          <input type="text" class="cyber-input st-lesson-id" value="${escapeHtml(m.lesson_id || "")}" placeholder="e.g. acad-101-m1" />
        </div>
        <div class="form-field" style="grid-column: span 2;">
          <label>LESSON TITLE</label>
          <input type="text" class="cyber-input st-lesson-title" value="${escapeHtml(m.title || "")}" placeholder="Module 1: Title" oninput="updateLessonTitlePreview(this)" />
        </div>
      </div>
      <div class="grid-2" style="margin-bottom:0.5rem;">
        <div class="form-field">
          <label>ESTIMATED DURATION</label>
          <input type="text" class="cyber-input st-lesson-duration" value="${escapeHtml(m.duration || "25 min")}" placeholder="25 min" />
        </div>
        <div class="form-field">
          <label>LEARNING OBJECTIVES (ONE PER LINE)</label>
          <textarea class="cyber-input st-lesson-objectives" rows="2" placeholder="Objective 1&#10;Objective 2">${escapeHtml(objectivesText)}</textarea>
        </div>
      </div>
      <div class="form-field" style="margin-bottom:0.5rem;">
        <label>LESSON THEORY &amp; COMPREHENSIVE TECHNICAL CONTENT</label>
        <textarea class="cyber-input st-lesson-content" rows="6" placeholder="Full comprehensive technical guidance and theory...">${escapeHtml(m.content || "")}</textarea>
      </div>
      <div class="form-field" style="margin-bottom:0.5rem;">
        <label>REFERENCE CODE SAMPLE / CLI COMMANDS</label>
        <textarea class="cyber-input st-lesson-code" rows="4" placeholder="# CLI commands, configuration, or Python script...">${escapeHtml(m.code_sample || "")}</textarea>
      </div>
      <div style="background:#091424; border:1px solid #1a3c69; padding:0.65rem; margin-top:0.5rem;">
        <div style="color:var(--accent-amber); font-weight:700; font-size:0.76rem; margin-bottom:0.4rem;">
          🧩 CHECKPOINT INTERACTIVE VERIFICATION (+50 XP)
        </div>
        <div class="grid-3">
          <div class="form-field" style="grid-column: span 2;">
            <label>CHECKPOINT QUESTION</label>
            <input type="text" class="cyber-input st-lesson-chk-q" value="${escapeHtml(m.checkpoint_q || "")}" placeholder="Verification question for operative..." />
          </div>
          <div class="form-field">
            <label>VERIFIED ANSWER</label>
            <input type="text" class="cyber-input st-lesson-chk-a" value="${escapeHtml(m.checkpoint_a || "")}" placeholder="e.g. 8314" />
          </div>
        </div>
        <div class="form-field" style="margin-top:0.4rem;">
          <label>CHECKPOINT FIELD HINT</label>
          <input type="text" class="cyber-input st-lesson-chk-hint" value="${escapeHtml(m.checkpoint_hint || "")}" placeholder="Guidance hint if stuck..." />
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateLessonTitlePreview(input) {
  const card = input.closest(".studio-lesson-card");
  const preview = card?.querySelector(".st-lesson-title-preview");
  if (preview) {
    preview.textContent = input.value.trim() || "Untitled Lesson";
  }
}
window.updateLessonTitlePreview = updateLessonTitlePreview;

function collectCurrentLessonsFromDom() {
  const cards = document.querySelectorAll("#studio-lessons-list .studio-lesson-card");
  const lessons = [];
  cards.forEach((card) => {
    const rawObjs = card.querySelector(".st-lesson-objectives")?.value || "";
    const objectives = rawObjs
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    lessons.push({
      lesson_id: card.querySelector(".st-lesson-id")?.value.trim() || "",
      title: card.querySelector(".st-lesson-title")?.value.trim() || "",
      duration: card.querySelector(".st-lesson-duration")?.value.trim() || "25 min",
      objectives,
      content: card.querySelector(".st-lesson-content")?.value || "",
      code_sample: card.querySelector(".st-lesson-code")?.value || "",
      checkpoint_q: card.querySelector(".st-lesson-chk-q")?.value.trim() || "",
      checkpoint_a: card.querySelector(".st-lesson-chk-a")?.value.trim() || "",
      checkpoint_hint: card.querySelector(".st-lesson-chk-hint")?.value.trim() || ""
    });
  });
  return lessons;
}

function addStudioLesson() {
  const current = collectCurrentLessonsFromDom();
  const cId = document.getElementById("st-id")?.value.trim() || "track";
  const num = current.length + 1;
  current.push({
    lesson_id: `${cId}-m${num}`,
    title: `Module ${num}: New Lesson Title`,
    duration: "25 min",
    objectives: ["Analyze technical requirements and attack surfaces", "Implement verifiable security controls"],
    content: "Operatives will investigate and master the following technical operational domain...",
    code_sample: "# Interactive execution or python code\n",
    checkpoint_q: "What parameter or standard applies to this operation?",
    checkpoint_a: "answer",
    checkpoint_hint: "Check the reference code sample."
  });
  renderStudioLessons(current);
}

function moveStudioLesson(idx, delta) {
  const current = collectCurrentLessonsFromDom();
  const targetIdx = idx + delta;
  if (targetIdx < 0 || targetIdx >= current.length) return;
  const temp = current[idx];
  current[idx] = current[targetIdx];
  current[targetIdx] = temp;
  renderStudioLessons(current);
}
window.moveStudioLesson = moveStudioLesson;

function deleteStudioLesson(idx) {
  const current = collectCurrentLessonsFromDom();
  if (current.length <= 1) {
    alert("Courses must have at least one lesson.");
    return;
  }
  current.splice(idx, 1);
  renderStudioLessons(current);
}
window.deleteStudioLesson = deleteStudioLesson;

function renderStudioCommands(customCommands) {
  const container = document.getElementById("studio-commands-list");
  if (!container) return;
  container.innerHTML = "";

  const entries = Object.entries(customCommands || {});
  if (entries.length === 0) {
    addStudioCommand();
    return;
  }

  entries.forEach(([cmdKey, cmdVal]) => {
    const row = document.createElement("div");
    row.className = "studio-cmd-row";
    row.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
        <div style="flex:1;">
          <label style="font-size:0.72rem; color:var(--accent-green); font-weight:700;">COMMAND TRIGGER (e.g. audit-tls --verbose)</label>
          <input type="text" class="cyber-input studio-cmd-key" value="${escapeHtml(cmdKey)}" placeholder="e.g. scan-host or audit-policy" />
        </div>
        <button type="button" class="btn btn-red" onclick="this.closest('.studio-cmd-row').remove()" style="padding:0.25rem 0.55rem; font-size:0.7rem; align-self:flex-end; margin-bottom:0.15rem;">🗑</button>
      </div>
      <div>
        <label style="font-size:0.72rem; color:var(--text-secondary);">TERMINAL SIMULATOR OUTPUT (Include FLAG{...} if winning command)</label>
        <textarea class="cyber-input studio-cmd-val" rows="3" placeholder="Terminal response output...&#10;FLAG{YOUR_FLAG_HERE}">${escapeHtml(cmdVal)}</textarea>
      </div>
    `;
    container.appendChild(row);
  });
}

function addStudioCommand() {
  const container = document.getElementById("studio-commands-list");
  if (!container) return;
  const row = document.createElement("div");
  row.className = "studio-cmd-row";
  row.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
      <div style="flex:1;">
        <label style="font-size:0.72rem; color:var(--accent-green); font-weight:700;">COMMAND TRIGGER (e.g. audit-policy)</label>
        <input type="text" class="cyber-input studio-cmd-key" placeholder="e.g. run-exploit or check-signature" />
      </div>
      <button type="button" class="btn btn-red" onclick="this.closest('.studio-cmd-row').remove()" style="padding:0.25rem 0.55rem; font-size:0.7rem; align-self:flex-end; margin-bottom:0.15rem;">🗑</button>
    </div>
    <div>
      <label style="font-size:0.72rem; color:var(--text-secondary);">TERMINAL SIMULATOR OUTPUT (Include FLAG{...} if winning command)</label>
      <textarea class="cyber-input studio-cmd-val" rows="3" placeholder="Auditing service... OK&#10;FLAG{YOUR_FLAG_HERE}"></textarea>
    </div>
  `;
  container.appendChild(row);
}

function renderStudioExam(examQuestions) {
  const container = document.getElementById("studio-exam-list");
  const countEl = document.getElementById("studio-exam-count");
  if (!container) return;

  container.innerHTML = "";
  if (countEl) countEl.textContent = (examQuestions || []).length;

  (examQuestions || []).forEach((q, idx) => {
    const card = document.createElement("div");
    card.className = "studio-exam-card";
    card.dataset.index = idx;

    const optLetters = ["A", "B", "C", "D"];
    const optionsHtml = optLetters
      .map((letter, optIdx) => {
        const opt = (q.options || [])[optIdx];
        const optVal = typeof opt === "object" ? (opt.value || letter) : (opt || letter);
        let optLabel = typeof opt === "object" ? (opt.label || opt.value || "") : (opt || "");
        optLabel = optLabel.replace(/^[A-D]\)\s*/, "");
        return `
          <div class="studio-opt-row">
            <span style="font-weight:700; color:var(--accent-amber); min-width:24px;">${letter}:</span>
            <input type="text" class="cyber-input st-exam-opt-text" data-letter="${letter}" value="${escapeHtml(optLabel)}" placeholder="Option ${letter} description..." style="flex:1;" />
            <input type="hidden" class="st-exam-opt-val" value="${escapeHtml(optVal)}" />
          </div>
        `;
      })
      .join("");

    const currentAns = (q.answer || "A").toUpperCase();
    const isAnsA = currentAns === "A" || ((q.options || [])[0]?.value?.toUpperCase() === currentAns);
    const isAnsB = currentAns === "B" || ((q.options || [])[1]?.value?.toUpperCase() === currentAns);
    const isAnsC = currentAns === "C" || ((q.options || [])[2]?.value?.toUpperCase() === currentAns);
    const isAnsD = currentAns === "D" || ((q.options || [])[3]?.value?.toUpperCase() === currentAns);

    card.innerHTML = `
      <div class="studio-card-header">
        <span style="color:var(--accent-amber); font-weight:700; font-size:0.84rem;">
          📝 QUESTION #${idx + 1} (<code>q${idx + 1}</code>)
        </span>
        <button type="button" class="btn btn-red" onclick="deleteStudioExamQuestion(${idx})" style="padding:0.2rem 0.55rem; font-size:0.7rem;">🗑</button>
      </div>
      <div class="form-field" style="margin-bottom:0.5rem;">
        <label>QUESTION TEXT</label>
        <textarea class="cyber-input st-exam-question" rows="2" placeholder="e.g. 1. What defense mitigates timing attacks in hash comparison?">${escapeHtml(q.question || "")}</textarea>
      </div>
      <div style="margin-bottom:0.5rem;">
        <label style="font-size:0.74rem; color:var(--text-accent); font-weight:700;">MULTIPLE CHOICE OPTIONS (A, B, C, D)</label>
        ${optionsHtml}
      </div>
      <div class="grid-2">
        <div class="form-field">
          <label>CORRECT ANSWER</label>
          <select class="cyber-input st-exam-answer">
            <option value="A" ${isAnsA ? "selected" : ""}>Option A</option>
            <option value="B" ${isAnsB ? "selected" : ""}>Option B</option>
            <option value="C" ${isAnsC ? "selected" : ""}>Option C</option>
            <option value="D" ${isAnsD ? "selected" : ""}>Option D</option>
          </select>
        </div>
        <div class="form-field">
          <label>TECHNICAL EXPLANATION (POST-EXAM FEEDBACK)</label>
          <input type="text" class="cyber-input st-exam-explanation" value="${escapeHtml(q.explanation || "")}" placeholder="Explanation of why this answer is correct..." />
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function collectCurrentExamFromDom() {
  const cards = document.querySelectorAll("#studio-exam-list .studio-exam-card");
  const exam = [];
  cards.forEach((card, idx) => {
    const qid = `q${idx + 1}`;
    const question = card.querySelector(".st-exam-question")?.value.trim() || "";
    const optRows = card.querySelectorAll(".studio-opt-row");
    const options = [];
    const letterVals = {};

    ["A", "B", "C", "D"].forEach((letter, optIdx) => {
      const row = optRows[optIdx];
      const text = row ? row.querySelector(".st-exam-opt-text").value.trim() : `Option ${letter}`;
      const hiddenVal = row ? row.querySelector(".st-exam-opt-val").value.trim() : letter;
      const finalVal = (hiddenVal && hiddenVal !== letter && isNaN(hiddenVal)) ? hiddenVal : letter;
      letterVals[letter] = finalVal;
      options.push({ value: finalVal, label: `${letter}) ${text}` });
    });

    const chosenLetter = card.querySelector(".st-exam-answer")?.value || "A";
    const answer = letterVals[chosenLetter] || chosenLetter;
    const explanation = card.querySelector(".st-exam-explanation")?.value.trim() || "";

    exam.push({
      q_id: qid,
      question,
      options,
      answer,
      explanation
    });
  });
  return exam;
}

function addStudioExamQuestion() {
  const current = collectCurrentExamFromDom();
  const num = current.length + 1;
  current.push({
    q_id: `q${num}`,
    question: `${num}. Question title...`,
    options: [
      { value: "A", label: "A) Correct primary control" },
      { value: "B", label: "B) Insecure perimeter assumption" },
      { value: "C", label: "C) Unauthenticated access model" },
      { value: "D", label: "D) Deprecated protocol fallback" }
    ],
    answer: "A",
    explanation: "Primary technical rationale explaining the correct answer."
  });
  renderStudioExam(current);
}

function deleteStudioExamQuestion(idx) {
  const current = collectCurrentExamFromDom();
  if (current.length <= 1) {
    alert("Exams must have at least one question.");
    return;
  }
  current.splice(idx, 1);
  renderStudioExam(current);
}
window.deleteStudioExamQuestion = deleteStudioExamQuestion;

function collectStudioCourseData() {
  const id = document.getElementById("st-id").value.trim();
  const code = document.getElementById("st-code").value.trim();
  const division = document.getElementById("st-division").value.trim();
  const title = document.getElementById("st-title").value.trim();
  const credential_title = document.getElementById("st-cred").value.trim();
  const ceu_credits = document.getElementById("st-ceu").value.trim();
  const xp = parseInt(document.getElementById("st-xp").value, 10) || 500;
  const estimated_duration = document.getElementById("st-duration").value.trim();
  const free_preview_count = parseInt(document.getElementById("st-free-preview")?.value, 10);
  const summary = document.getElementById("st-summary").value.trim();

  const modules = collectCurrentLessonsFromDom();

  // Lab
  const lab_title = document.getElementById("st-lab-title").value.trim();
  const lab_flag = document.getElementById("st-lab-flag").value.trim();
  const lab_scenario = document.getElementById("st-lab-scenario").value.trim();
  const lab_hint = document.getElementById("st-lab-hint").value.trim();
  const rawChips = document.getElementById("st-lab-chips").value || "";
  const suggested_commands = rawChips
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  const custom_commands = {};
  document.querySelectorAll("#studio-commands-list .studio-cmd-row").forEach((row) => {
    const k = row.querySelector(".studio-cmd-key")?.value.trim();
    const v = row.querySelector(".studio-cmd-val")?.value;
    if (k) custom_commands[k] = v || "";
  });

  const lab = {
    title: lab_title,
    flag: lab_flag,
    practical_flag: lab_flag,
    scenario: lab_scenario,
    hint: lab_hint,
    flag_hint: lab_hint,
    suggested_commands,
    custom_commands
  };

  const exam = collectCurrentExamFromDom();

  return {
    id,
    code,
    division,
    title,
    credential_title,
    ceu_credits,
    xp,
    estimated_duration,
    summary,
    modules,
    lab,
    exam,
    free_preview_count: isNaN(free_preview_count) ? 2 : free_preview_count,
    is_published: 1
  };
}

async function saveStudioCourse() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    alert("Authentication token expired. Please re-authenticate as Director.");
    return;
  }

  const course = collectStudioCourseData();
  if (!course.id || !course.code || !course.title) {
    alert("Course Code, Slug ID, and Title are required.");
    return;
  }

  const statusMsg = document.getElementById("studio-status-msg");
  const bottomStatus = document.getElementById("studio-bottom-status");
  const setStatus = (txt, isErr = false) => {
    const color = isErr ? "var(--accent-red)" : "var(--accent-green)";
    if (statusMsg) {
      statusMsg.style.display = "block";
      statusMsg.style.color = color;
      statusMsg.textContent = txt;
    }
    if (bottomStatus) {
      bottomStatus.style.color = color;
      bottomStatus.textContent = txt;
    }
  };

  setStatus("💾 Writing track to Directorate SQLite database & publishing live...");

  try {
    const res = await fetch("/api/admin/courses/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ course })
    });
    const data = await res.json();
    if (res.ok) {
      setStatus(`✔ SUCCESS // Track [${course.code}] saved and live!`);
      currentStudioCourseId = course.id;
      // Re-fetch courses and refresh public & agent views
      await initDirectorCourseStudio();
      loadPublicAcademyCurriculum();
      loadAgentDashboard();
      setTimeout(() => {
        if (bottomStatus) bottomStatus.textContent = "";
      }, 3500);
    } else {
      setStatus(`✖ SAVE FAILED // ${data.error || "Unknown server error"}`, true);
    }
  } catch (err) {
    setStatus("✖ Network error saving course to Directorate database.", true);
  }
}

async function deleteStudioCourse() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return;
  const courseId = document.getElementById("st-id")?.value.trim();
  if (!courseId) return;

  if (!confirm(`Are you sure you want to permanently delete track "${courseId}"?`)) {
    return;
  }

  try {
    const res = await fetch("/api/admin/courses/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ course_id: courseId })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Track ${courseId} deleted.`);
      currentStudioCourseId = null;
      await initDirectorCourseStudio();
      loadPublicAcademyCurriculum();
      loadAgentDashboard();
    } else {
      alert(`Delete failed: ${data.error || "Error"}`);
    }
  } catch (err) {
    alert("Network error during track deletion.");
  }
}

async function runAiIngestion() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return;

  const topic = document.getElementById("ai-ingest-topic")?.value.trim();
  const division = document.getElementById("ai-ingest-division")?.value.trim();
  const rawMaterial = document.getElementById("ai-ingest-raw")?.value.trim();
  const statusEl = document.getElementById("ai-ingest-status");

  if (!topic) {
    if (statusEl) {
      statusEl.style.color = "var(--accent-amber)";
      statusEl.textContent = "Please provide a Course Topic or Title.";
    }
    return;
  }

  if (statusEl) {
    statusEl.style.color = "var(--text-accent)";
    statusEl.textContent = "🤖 Synthesizing 5 chapters, objectives, code samples, Cyber Range lab, and exam bank...";
  }

  try {
    const res = await fetch("/api/admin/courses/ai-ingest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        topic,
        division,
        raw_material: rawMaterial
      })
    });
    const data = await res.json();
    if (res.ok && data.course) {
      if (statusEl) {
        statusEl.style.color = "var(--accent-green)";
        statusEl.textContent = "✔ Course synthesized! Populating studio...";
      }
      loadCourseIntoStudio(data.course);
      setTimeout(() => {
        document.getElementById("studio-ai-drawer").style.display = "none";
        if (statusEl) statusEl.textContent = "";
      }, 1200);
    } else {
      if (statusEl) {
        statusEl.style.color = "var(--accent-red)";
        statusEl.textContent = `✖ Ingestion failed: ${data.error || "Error"}`;
      }
    }
  } catch (err) {
    if (statusEl) {
      statusEl.style.color = "var(--accent-red)";
      statusEl.textContent = "Network error communicating with AI ingestion API.";
    }
  }
}

function exportStudioJson() {
  const course = collectStudioCourseData();
  const jsonStr = JSON.stringify(course, null, 2);
  navigator.clipboard.writeText(jsonStr);
  const btn = document.getElementById("btn-studio-export");
  if (btn) {
    const old = btn.textContent;
    btn.textContent = "✔ Copied JSON!";
    setTimeout(() => (btn.textContent = old), 1600);
  }
}



// ===== BILLING & CLEARANCE UPGRADE =====

async function startClearanceCheckout(planTier) {
  const token = localStorage.getItem(TOKEN_KEY);
  const statusEl = document.getElementById("dossier-plan-status");
  if (statusEl) {
    statusEl.textContent = "Connecting to Directorate billing...";
    statusEl.style.color = "var(--text-accent)";
  }
  try {
    const res = await fetch("/api/billing/create-checkout-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ plan_tier: planTier })
    });
    const data = await res.json();
    if (data.checkout_url) {
      window.location.href = data.checkout_url;
    } else if (data.simulated) {
      // Sandbox mode — offer instant activation for testing
      const tierName = data.tier_name || planTier;
      const confirmed = confirm(
        `\u26a0 SANDBOX MODE (No Stripe key configured)\n\nInstantly activate "${tierName}" clearance for testing?`
      );
      if (confirmed && token) {
        await simulateClearanceUpgrade(planTier);
      } else if (!token) {
        alert("Sign in first to upgrade your clearance.");
      }
    } else if (data.error) {
      if (statusEl) { statusEl.style.color = "var(--accent-red)"; statusEl.textContent = `Billing error: ${data.error}`; }
    }
  } catch (err) {
    console.error("Billing error:", err);
    if (statusEl) { statusEl.style.color = "var(--accent-red)"; statusEl.textContent = "Billing connection error \u2014 try again."; }
  }
}
window.startClearanceCheckout = startClearanceCheckout;

async function simulateClearanceUpgrade(planTier) {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    alert("Sign in first to upgrade clearance.");
    return;
  }
  try {
    const res = await fetch("/api/billing/simulate-upgrade", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ plan_tier: planTier })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`\u2714 ${data.message || "Clearance upgraded!"}\n\nReloading Agent HQ...`);
      loadAgentDashboard();
    } else {
      alert(`Error: ${data.error || "Upgrade failed."}`);
    }
  } catch (err) {
    console.error("Simulate upgrade error:", err);
    alert("Upgrade connection error \u2014 try again.");
  }
}
window.simulateClearanceUpgrade = simulateClearanceUpgrade;

async function handlePaymentReturn() {
  const urlParams = new URLSearchParams(window.location.search);
  const paymentStatus = urlParams.get("payment");
  const sessionId = urlParams.get("session_id");

  if (paymentStatus === "success" && sessionId) {
    const statusEl = document.getElementById("dossier-plan-status");
    if (statusEl) statusEl.textContent = "Verifying clearance payment with Stripe...";
    try {
      const res = await fetch("/api/billing/verify-checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await res.json();
      if (res.ok) {
        alert(`🎖 PAYMENT VERIFIED!\n\nYour clearance has been escalated to ${data.clearance_level} (${data.plan_tier}).\nAll academy courses, practical cyber ranges, and certification exams are unlocked!`);
      } else {
        console.warn("Session verification warning:", data);
      }
    } catch (err) {
      console.error("Payment return error:", err);
    } finally {
      window.history.replaceState({}, document.title, window.location.pathname);
      loadAgentDashboard();
    }
  } else if (paymentStatus === "cancelled") {
    alert("Clearance transaction cancelled. Your current standing remains unchanged.");
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}
window.handlePaymentReturn = handlePaymentReturn;

async function openBillingPortal() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    alert("Authentication expired. Please sign in again.");
    return;
  }
  const statusEl = document.getElementById("dossier-plan-status");
  if (statusEl) statusEl.textContent = "Connecting to Stripe Billing Portal...";
  try {
    const res = await fetch("/api/billing/customer-portal", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      }
    });
    const data = await res.json();
    if (data.portal_url) {
      window.location.href = data.portal_url;
    } else {
      alert(data.error || "Unable to open billing portal.");
      if (statusEl) statusEl.textContent = "Status: Active • Verifiable Cryptographic Access";
    }
  } catch (err) {
    console.error("Portal error:", err);
    alert("Connection error opening billing portal.");
    if (statusEl) statusEl.textContent = "Status: Active • Verifiable Cryptographic Access";
  }
}
window.openBillingPortal = openBillingPortal;
