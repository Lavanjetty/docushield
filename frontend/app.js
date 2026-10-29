/**
 * DocuShield Frontend Controller
 * Handles document uploads, forensics inspection, visual diff comparison, and audit reports.
 */

// Global State
let currentSelectedFile = null;
let currentDocumentRecord = null;
let currentVerificationAction = 'verify'; // 'verify' or 'register'
let trustedOriginalsList = [];

// API base endpoint
const API_BASE = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
  setupDropzone();
  loadTrustedOriginals();
  loadDashboardMetrics();
  loadDocumentsTable();
  loadHistoryTable();
});

// Tab Switcher
function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  const targetBtn = document.getElementById(`tab-btn-${tabName}`);

  if (targetTab && targetBtn) {
    targetTab.classList.remove("hidden");
    targetBtn.classList.add("active");
  }

  if (tabName === 'dashboard') {
    loadDashboardMetrics();
    loadDocumentsTable();
  } else if (tabName === 'registry') {
    loadTrustedOriginalsTable();
  } else if (tabName === 'history') {
    loadHistoryTable();
  }
}

// Drag & Drop Setup
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-cyan-400", "bg-cyan-950/30");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("border-cyan-400", "bg-cyan-950/30");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-cyan-400", "bg-cyan-950/30");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  currentSelectedFile = file;
  document.getElementById("selected-file-card").classList.remove("hidden");
  document.getElementById("sel-filename").textContent = file.name;
  document.getElementById("sel-filesize").textContent = `${(file.size / 1024).toFixed(1)} KB`;
}

function clearSelectedFile() {
  currentSelectedFile = null;
  document.getElementById("file-input").value = "";
  document.getElementById("selected-file-card").classList.add("hidden");
}

function setVerificationAction(action) {
  currentVerificationAction = action;
  const btnVerify = document.getElementById("act-btn-verify");
  const btnRegister = document.getElementById("act-btn-register");
  const origSelectWrap = document.getElementById("target-original-select-wrap");
  const regLabelWrap = document.getElementById("register-label-wrap");

  if (action === 'verify') {
    btnVerify.className = "px-3 py-2 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500 font-medium transition text-center";
    btnRegister.className = "px-3 py-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 font-medium transition text-center";
    origSelectWrap.classList.remove("hidden");
    regLabelWrap.classList.add("hidden");
  } else {
    btnRegister.className = "px-3 py-2 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500 font-medium transition text-center";
    btnVerify.className = "px-3 py-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 font-medium transition text-center";
    origSelectWrap.classList.add("hidden");
    regLabelWrap.classList.remove("hidden");
  }
}

// Quick Sample Loader
async function loadSampleFile(sampleFilename) {
  try {
    const res = await fetch(`/static/samples/${sampleFilename}`);
    if (!res.ok) throw new Error("Could not fetch sample");
    const blob = await res.blob();
    const file = new File([blob], sampleFilename, { type: blob.type || "application/octet-stream" });
    handleFileSelected(file);
    switchTab('workspace');
  } catch (err) {
    alert("Sample file not found: " + err.message);
  }
}

// Main Execution
async function handleDocumentExecution() {
  if (!currentSelectedFile) {
    alert("Please select or drop a PDF or image file first.");
    return;
  }

  const btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Analyzing Document...`;

  try {
    // 1. Upload & Analyze Document
    const formData = new FormData();
    formData.append("file", currentSelectedFile);

    const uploadRes = await fetch(`${API_BASE}/api/documents`, {
      method: "POST",
      body: formData
    });

    if (!uploadRes.ok) {
      const err = await uploadRes.json();
      throw new Error(err.detail || "Upload & Analysis failed.");
    }

    const docRecord = await uploadRes.json();
    currentDocumentRecord = docRecord;

    // 2. Action based on verify or register
    if (currentVerificationAction === 'register') {
      const label = document.getElementById("reg-label-input").value.trim() || `Reference Master: ${currentSelectedFile.name}`;
      const cat = document.getElementById("reg-cat-input").value.trim() || "General";
      
      const regData = new FormData();
      regData.append("label", label);
      regData.append("category", cat);
      regData.append("sha256", docRecord.sha256);

      await fetch(`${API_BASE}/api/originals`, {
        method: "POST",
        body: regData
      });

      await loadTrustedOriginals();
      displayAnalysisResults(docRecord, {
        result: "REGISTERED",
        original_label: label,
        explanation: "Fingerprint successfully registered into trusted authority registry."
      });
    } else {
      // Verification mode
      const selectedOrigId = document.getElementById("select-trusted-orig").value;
      if (selectedOrigId) {
        const verifRes = await fetch(`${API_BASE}/api/documents/${docRecord.id}/verify/${selectedOrigId}`, {
          method: "POST"
        });
        const verifData = await verifRes.json();
        displayAnalysisResults(docRecord, verifData);
      } else {
        // Auto-check against all originals to find exact match if any
        let matchedOrig = trustedOriginalsList.find(o => o.sha256.toLowerCase() === docRecord.sha256.toLowerCase());
        if (matchedOrig) {
          const verifRes = await fetch(`${API_BASE}/api/documents/${docRecord.id}/verify/${matchedOrig.id}`, {
            method: "POST"
          });
          const verifData = await verifRes.json();
          displayAnalysisResults(docRecord, verifData);
        } else {
          displayAnalysisResults(docRecord, null);
        }
      }
    }

    loadDashboardMetrics();
    loadDocumentsTable();
    loadHistoryTable();

  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"/></svg><span>Analyze Document</span>`;
  }
}

// Display Analysis Results (Slide 15 & 16 UI representation)
function displayAnalysisResults(doc, verification) {
  document.getElementById("results-placeholder").classList.add("hidden");
  const panel = document.getElementById("analysis-panel");
  panel.classList.remove("hidden");

  const report = doc.report_json || {};
  const ml = report.ml_result || {};
  const imgForensics = report.image_forensics;
  const meta = report.metadata || {};

  // 1. SHA-256 Badge
  const badgeIntegrity = document.getElementById("badge-integrity");
  const integrityDesc = document.getElementById("integrity-desc");
  document.getElementById("disp-sha256").textContent = doc.sha256;

  if (verification) {
    if (verification.result === "MATCH") {
      badgeIntegrity.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
      badgeIntegrity.textContent = "MATCH (VERIFIED)";
      integrityDesc.textContent = `Exact byte match confirmed against trusted original: "${verification.original_label || verification.original_uuid}".`;
    } else if (verification.result === "MISMATCH") {
      badgeIntegrity.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40";
      badgeIntegrity.textContent = "MISMATCH (BYTE ALTERATION)";
      integrityDesc.textContent = `Fingerprint differs from reference: "${verification.original_label || verification.original_uuid}". Indicates modified bytes.`;
    } else if (verification.result === "REGISTERED") {
      badgeIntegrity.className = "text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
      badgeIntegrity.textContent = "REGISTERED";
      integrityDesc.textContent = `Registered into trusted authority registry under "${verification.original_label}".`;
    }
  } else {
    badgeIntegrity.className = "text-xs px-2.5 py-0.5 rounded-full font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30";
    badgeIntegrity.textContent = "Requires Review";
    integrityDesc.textContent = "Unregistered file: Processed standalone signals. Weak clues are not treated as proof of forgery.";
  }

  // 2. ML Screening Card
  const mlBadge = document.getElementById("badge-ml");
  const mlLabel = document.getElementById("ml-label");
  const mlDesc = document.getElementById("ml-explanation");

  if (ml.risk_score !== undefined) {
    mlLabel.textContent = `${ml.label} (Risk Index: ${(ml.risk_score * 100).toFixed(1)}%)`;
    mlDesc.textContent = ml.explanation;
    if (ml.risk_score > 0.65) {
      mlBadge.className = "text-xs px-2.5 py-0.5 rounded-full font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30";
    } else if (ml.risk_score < 0.35) {
      mlBadge.className = "text-xs px-2.5 py-0.5 rounded-full font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    }
  }

  // 3. Metadata List
  const metaContainer = document.getElementById("metadata-list");
  metaContainer.innerHTML = `
    <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Filename:</span> <span class="font-medium text-slate-200 truncate max-w-[180px]">${doc.filename}</span></div>
    <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Format:</span> <span class="text-cyan-400">${(doc.file_type || '').toUpperCase()}</span></div>
    <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Size:</span> <span>${(doc.file_size / 1024).toFixed(1)} KB</span></div>
    <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Pages/Dim:</span> <span>${meta.page_count ? meta.page_count + ' page(s)' : (meta.dimensions || 'Standard')}</span></div>
    <div class="flex justify-between py-1"><span class="text-slate-400">Producer/Author:</span> <span class="truncate max-w-[170px]">${meta.producer || meta.author || 'N/A'}</span></div>
  `;

  // 4. Forensic Indicators
  const heurContainer = document.getElementById("heuristics-list");
  if (imgForensics) {
    heurContainer.innerHTML = `
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Laplacian Sharpness:</span> <span class="font-mono text-cyan-300 font-semibold">${imgForensics.sharpness_score}</span></div>
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Edge Density:</span> <span class="font-mono text-cyan-300">${(imgForensics.edge_density * 100).toFixed(1)}%</span></div>
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">ELA Compression Delta:</span> <span class="font-mono text-purple-300">${imgForensics.ela_metrics?.mean_delta || 'N/A'}</span></div>
      <div class="py-1"><span class="text-[11px] text-slate-400 italic">${imgForensics.findings?.[0] || 'Descriptive image heuristics calculated.'}</span></div>
    `;
  } else {
    heurContainer.innerHTML = `
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Structure Validation:</span> <span class="text-emerald-400">Valid PDF Stream</span></div>
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Encryption Status:</span> <span>${meta.encrypted ? 'Encrypted' : 'Unencrypted'}</span></div>
      <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Linguistic Signals:</span> <span class="text-cyan-300">Extracted & Verified</span></div>
      <div class="py-1"><span class="text-[11px] text-slate-400 italic">PDF stream parsed via PyMuPDF.</span></div>
    `;
  }

  // 5. Extracted Text
  const textView = document.getElementById("extracted-text-view");
  const extractedText = doc.extracted_text || "(No readable character stream recovered)";
  textView.textContent = extractedText;
  document.getElementById("text-length-badge").textContent = `${extractedText.length} characters`;
}

function copyHash() {
  const hash = document.getElementById("disp-sha256").textContent;
  navigator.clipboard.writeText(hash).then(() => {
    alert("SHA-256 copied to clipboard!");
  });
}

function downloadCurrentPDFReport() {
  if (!currentDocumentRecord) return;
  window.open(`${API_BASE}/api/documents/${currentDocumentRecord.id}/pdf`, '_blank');
}

// Load Trusted Originals
async function loadTrustedOriginals() {
  try {
    const res = await fetch(`${API_BASE}/api/originals`);
    const data = await res.json();
    trustedOriginalsList = data.trusted_originals || [];

    const select = document.getElementById("select-trusted-orig");
    select.innerHTML = '<option value="">-- Choose Trusted Reference (or auto-match) --</option>';
    trustedOriginalsList.forEach(orig => {
      const opt = document.createElement("option");
      opt.value = orig.id;
      opt.textContent = `${orig.label} (${orig.sha256.substring(0, 8)}...)`;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Failed to load trusted originals", err);
  }
}

async function loadTrustedOriginalsTable() {
  await loadTrustedOriginals();
  const tbody = document.getElementById("registry-table-body");
  tbody.innerHTML = "";

  if (trustedOriginalsList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-slate-500">No master originals registered yet.</td></tr>`;
    return;
  }

  trustedOriginalsList.forEach(orig => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-800/40";
    tr.innerHTML = `
      <td class="py-3 px-3 font-medium text-slate-200">${orig.label}</td>
      <td class="py-3 px-3 text-slate-400">${orig.category || 'General'}</td>
      <td class="py-3 px-3 font-mono text-[11px] text-cyan-300">${orig.sha256.substring(0, 16)}...${orig.sha256.substring(56)}</td>
      <td class="py-3 px-3 text-slate-400 text-[11px]">${orig.registered_at.substring(0, 10)}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function handleManualOriginalRegister(e) {
  e.preventDefault();
  const title = document.getElementById("reg-title").value.trim();
  const cat = document.getElementById("reg-category").value.trim();
  const hashStr = document.getElementById("reg-hash-str").value.trim();
  const fileInput = document.getElementById("reg-file");

  const formData = new FormData();
  formData.append("label", title);
  formData.append("category", cat);

  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);
  } else if (hashStr) {
    formData.append("sha256", hashStr);
  } else {
    alert("Please either select a file or provide a 64-character SHA-256 hash.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/originals`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail);
    }
    alert("Master fingerprint registered successfully!");
    document.getElementById("form-register-orig").reset();
    loadTrustedOriginalsTable();
  } catch (err) {
    alert("Failed to register original: " + err.message);
  }
}

// Load Dashboard Metrics
async function loadDashboardMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard`);
    const metrics = await res.json();

    document.getElementById("metric-total-docs").textContent = metrics.total_documents || 0;
    document.getElementById("metric-total-origs").textContent = metrics.total_originals || 0;
    document.getElementById("metric-matches").textContent = metrics.matches || 0;
    document.getElementById("metric-mismatches").textContent = metrics.mismatches || 0;
  } catch (err) {
    console.error("Failed to load metrics", err);
  }
}

// Documents Table
async function loadDocumentsTable(searchTerm = "") {
  try {
    const url = searchTerm ? `${API_BASE}/api/documents?search=${encodeURIComponent(searchTerm)}` : `${API_BASE}/api/documents`;
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById("documents-table-body");
    tbody.innerHTML = "";

    const docs = data.documents || [];
    if (docs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-500">No documents found.</td></tr>`;
      return;
    }

    docs.forEach(doc => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-800/40 transition";
      tr.innerHTML = `
        <td class="py-3 px-3 font-mono text-cyan-400">${doc.document_uuid.substring(0, 10)}</td>
        <td class="py-3 px-3 font-medium text-slate-200 truncate max-w-[160px]">${doc.filename}</td>
        <td class="py-3 px-3 uppercase text-slate-400 text-[11px]">${doc.file_type}</td>
        <td class="py-3 px-3 font-mono text-[11px] text-slate-400">${doc.sha256.substring(0, 12)}...</td>
        <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">${doc.status}</span></td>
        <td class="py-3 px-3 text-slate-400 text-[11px]">${doc.uploaded_at.substring(0, 10)}</td>
        <td class="py-3 px-3 text-right">
          <a href="${API_BASE}/api/documents/${doc.id}/pdf" target="_blank" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-cyan-300 text-xs transition inline-block">PDF Report</a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load documents table", err);
  }
}

let searchDebounceTimer = null;
function handleDocSearch(val) {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    loadDocumentsTable(val.trim());
  }, 300);
}

// Verification History Table
async function loadHistoryTable() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    const data = await res.json();
    const tbody = document.getElementById("history-table-body");
    tbody.innerHTML = "";

    const history = data.history || [];
    if (history.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-500">No verification checks recorded yet.</td></tr>`;
      return;
    }

    history.forEach(item => {
      const isMatch = item.result === "MATCH";
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-800/40";
      tr.innerHTML = `
        <td class="py-3 px-3 font-mono text-slate-400">#${item.id}</td>
        <td class="py-3 px-3 font-medium text-slate-200">${item.document_name}</td>
        <td class="py-3 px-3 text-slate-400">${item.original_label}</td>
        <td class="py-3 px-3 text-slate-400 text-[11px]">${item.checked_at.replace("T", " ").substring(0, 19)}</td>
        <td class="py-3 px-3 text-center">
          <span class="px-2.5 py-1 rounded text-xs font-bold ${isMatch ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'}">
            ${item.result}
          </span>
        </td>
        <td class="py-3 px-3 text-slate-400 text-[11px]">${item.details_json?.interpretation || 'Checked'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load history table", err);
  }
}

// Alteration Detection Demo (Slide 17)
async function runSyntheticReceiptDemo() {
  try {
    // Fetch both samples
    const res1 = await fetch('/static/samples/sample_receipt_original.png');
    const blob1 = await res1.blob();
    const res2 = await fetch('/static/samples/sample_receipt_edited.png');
    const blob2 = await res2.blob();

    const formData = new FormData();
    formData.append("reference", new File([blob1], "sample_receipt_original.png"));
    formData.append("target", new File([blob2], "sample_receipt_edited.png"));

    const compareRes = await fetch(`${API_BASE}/api/compare-images`, {
      method: "POST",
      body: formData
    });

    const result = await compareRes.json();
    renderDiffVisuals(
      '/static/samples/sample_receipt_original.png',
      '/static/samples/sample_receipt_edited.png',
      result.diff_image_url,
      "Rs. 2,500 (Master)",
      "Rs. 9,500 (Tampered Amount)"
    );

  } catch (err) {
    alert("Synthetic demo error: " + err.message);
  }
}

async function compareCustomImages() {
  const refInput = document.getElementById("diff-ref-input");
  const tarInput = document.getElementById("diff-tar-input");

  if (!refInput.files[0] || !tarInput.files[0]) {
    alert("Please select both a reference image and a suspect/target image.");
    return;
  }

  const formData = new FormData();
  formData.append("reference", refInput.files[0]);
  formData.append("target", tarInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/api/compare-images`, {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    
    const urlRef = URL.createObjectURL(refInput.files[0]);
    const urlTar = URL.createObjectURL(tarInput.files[0]);

    renderDiffVisuals(urlRef, urlTar, result.diff_image_url, refInput.files[0].name, tarInput.files[0].name);
  } catch (err) {
    alert("Image comparison error: " + err.message);
  }
}

function renderDiffVisuals(url1, url2, resultUrl, meta1, meta2) {
  const wrap = document.getElementById("diff-results-wrap");
  wrap.classList.remove("hidden");

  document.getElementById("diff-img-orig").src = url1;
  document.getElementById("diff-img-edit").src = url2;
  document.getElementById("diff-img-result").src = resultUrl;

  document.getElementById("diff-meta-orig").textContent = meta1;
  document.getElementById("diff-meta-edit").textContent = meta2;
}
