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
  } catch (err) {
    console.error("Dashboard load error:", err);
  }
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
      : `<span style="color:var(--accent-amber); font-size:0.78rem;">+${c.xp} XP &bull; ${escapeHtml(c.ceu_credits.split("(")[0].trim())} ▾</span>`;

    const modulesHtml = (c.modules || [])
      .map(
        (m) => `
        <div class="module-block">
          <div style="color:var(--text-accent); font-weight:700; font-size:0.86rem; margin-bottom:0.35rem;">${escapeHtml(m.title)}</div>
          <p style="color:var(--text-primary); font-size:0.81rem; margin-bottom:0.45rem; white-space:pre-line;">${escapeHtml(m.content)}</p>
          <div class="cipher-box" style="margin:0.35rem 0 0 0; font-size:0.78rem;">${escapeHtml(m.code_sample)}</div>
        </div>
      `
      )
      .join("");

    let examSectionHtml = "";
    if (c.completed && c.certificate) {
      examSectionHtml = `
        <div style="margin-top:1rem; padding:0.85rem; background:#071914; border:1px solid var(--accent-green); color:var(--accent-green); font-size:0.83rem;">
          ✔ <strong>CERTIFICATION COMPLETE:</strong> You have earned <strong>${escapeHtml(c.credential_title)}</strong> (Certificate ID: <code>${escapeHtml(c.certificate.cert_id)}</code>).
        </div>
      `;
    } else {
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

      examSectionHtml = `
        <div style="margin-top:1.1rem; border-top:1px solid #1b3659; padding-top:0.9rem;">
          <h4 style="color:var(--accent-amber); font-size:0.9rem; margin-bottom:0.55rem;">📝 HANDS-ON CERTIFICATION EXAM // ${escapeHtml(c.credential_title)}</h4>
          ${questionsHtml}
          <div style="display:flex; flex-wrap:wrap; align-items:center; gap:0.65rem; margin-top:0.65rem;">
            <button type="button" class="btn btn-green" onclick="submitAcademyExam('${escapeHtml(c.id)}')">🎓 Submit Exam &amp; Issue Certificate (+${c.xp} XP)</button>
            <span id="exam-status-${escapeHtml(c.id)}" style="font-size:0.82rem;"></span>
          </div>
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
        ${modulesHtml}
        ${examSectionHtml}
      </div>
    `;
    coursesContainer.appendChild(details);
  });
}

async function submitAcademyExam(courseId) {
  const statusEl = document.getElementById(`exam-status-${courseId}`);
  const token = localStorage.getItem(TOKEN_KEY);
  if (!statusEl || !token) return;

  const answers = {};
  ["q1", "q2", "q3"].forEach((qid) => {
    const checked = document.querySelector(`input[name="exam-${courseId}-${qid}"]:checked`);
    if (checked) answers[qid] = checked.value;
  });

  if (Object.keys(answers).length < 3) {
    statusEl.style.color = "var(--accent-amber)";
    statusEl.textContent = "Please select an answer for all 3 exam questions before submitting.";
    return;
  }

  statusEl.style.color = "var(--text-accent)";
  statusEl.textContent = "Grading examination & signing credential...";

  const res = await fetch("/api/academy/exam", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ course_id: courseId, answers })
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
// 5. Event Listeners & PWA Install Prompt
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  runCriticalSoftworksSplash();
  initDialogLightDismissFallbacks();
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

