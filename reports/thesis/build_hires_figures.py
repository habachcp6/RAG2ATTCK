import pathlib
import subprocess
import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = pathlib.Path(r"C:\Users\hahoa\.gemini\antigravity\brain\8a3ff726-a1a3-499b-a40d-9a2226b3a57c\scratch\figures_hires")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.edgecolor"] = "#334155"
plt.rcParams["axes.linewidth"] = 1.1

# ---------------------------------------------------------------------------
# Figure 1: High-res System Architecture (fixed terminology & provenance)
# ---------------------------------------------------------------------------
def build_fig1():
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 500" width="860" height="500">
  <defs>
    <style>
      @page { size: 860px 500px; margin: 0; }
      .title { font-family: "Segoe UI", Arial, sans-serif; font-size: 15.5px; font-weight: bold; fill: #0f172a; text-anchor: middle; }
      .subtitle { font-family: "Segoe UI", Arial, sans-serif; font-size: 11.5px; fill: #475569; text-anchor: middle; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="430" y="30" class="title">Figure 1: RAG2ATT&amp;CK Dual-View Attribution Architecture</text>
  <text x="430" y="50" class="subtitle">Controlled evaluation pipeline across 5 conditions (N = 1,280 TEST views; 718 scorable mapped-positive views)</text>

  <!-- Boxes -->
  <rect x="35" y="92" width="175" height="122" rx="8" ry="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
  <text x="122" y="116" font-family="Segoe UI, Arial" font-size="12.5" font-weight="bold" fill="#1d4ed8" text-anchor="middle">Windows Endpoint Telemetry</text>
  <line x1="45" y1="125" x2="200" y2="125" stroke="#2563eb" stroke-width="1" opacity="0.45"/>
  <text x="122" y="146" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">Single &amp; Contextual Views</text>
  <text x="122" y="166" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">640 TEST Pairs (1,280 Views)</text>
  <text x="122" y="186" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569" text-anchor="middle">INFERENCE_ALLOWLIST Scrubbed</text>

  <rect x="255" y="92" width="175" height="122" rx="8" ry="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/>
  <text x="342" y="116" font-family="Segoe UI, Arial" font-size="12.5" font-weight="bold" fill="#6d28d9" text-anchor="middle">Dense Vector Retrieval</text>
  <line x1="265" y1="125" x2="420" y2="125" stroke="#7c3aed" stroke-width="1" opacity="0.45"/>
  <text x="342" y="146" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">all-MiniLM-L6-v2 (384-d L2)</text>
  <text x="342" y="166" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">FAISS IndexFlatIP (474 Docs)</text>
  <text x="342" y="186" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569" text-anchor="middle">Candidate Depths k in {1, 3, 5, 10}</text>

  <rect x="475" y="92" width="175" height="122" rx="8" ry="8" fill="#ecfdf5" stroke="#059669" stroke-width="2"/>
  <text x="562" y="116" font-family="Segoe UI, Arial" font-size="12.5" font-weight="bold" fill="#047857" text-anchor="middle">LLM Reasoning Engine</text>
  <line x1="485" y1="125" x2="640" y2="125" stroke="#059669" stroke-width="1" opacity="0.45"/>
  <text x="562" y="146" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">OpenAI gpt-5.6-luna Alias</text>
  <text x="562" y="166" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">reasoning_effort = "xhigh"</text>
  <text x="562" y="186" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569" text-anchor="middle">Symmetric Prompt &amp; Schema</text>

  <rect x="690" y="92" width="140" height="122" rx="8" ry="8" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="760" y="116" font-family="Segoe UI, Arial" font-size="12.5" font-weight="bold" fill="#b45309" text-anchor="middle">Attribution Output</text>
  <line x1="700" y1="125" x2="820" y2="125" stroke="#d97706" stroke-width="1" opacity="0.45"/>
  <text x="760" y="146" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">Single Technique ID</text>
  <text x="760" y="166" font-family="Segoe UI, Arial" font-size="11" fill="#1e293b" text-anchor="middle">ANY_MATCH Scoring</text>
  <text x="760" y="186" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569" text-anchor="middle">474-Class Macro-F1</text>

  <!-- Arrows -->
  <line x1="210" y1="153" x2="253" y2="153" stroke="#475569" stroke-width="2.2"/>
  <polygon points="255,153 247,148 247,158" fill="#475569"/>
  <line x1="430" y1="153" x2="473" y2="153" stroke="#475569" stroke-width="2.2"/>
  <polygon points="475,153 467,148 467,158" fill="#475569"/>
  <line x1="650" y1="153" x2="688" y2="153" stroke="#475569" stroke-width="2.2"/>
  <polygon points="690,153 682,148 682,158" fill="#475569"/>

  <!-- No-RAG Bypass -->
  <path d="M 122 92 L 122 68 L 562 68 L 562 92" fill="none" stroke="#2563eb" stroke-width="2" stroke-dasharray="5,4"/>
  <polygon points="562,92 557,85 567,85" fill="#2563eb"/>
  <rect x="242" y="57" width="215" height="22" rx="4" ry="4" fill="#dbeafe" stroke="#2563eb" stroke-width="1.2"/>
  <text x="349" y="72" font-family="Segoe UI, Arial" font-size="10.5" font-weight="bold" fill="#1d4ed8" text-anchor="middle">No-RAG Baseline Bypass (k = 0)</text>

  <!-- Governance Box -->
  <rect x="35" y="238" width="795" height="235" rx="8" ry="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5" stroke-dasharray="5,5"/>
  <text x="432" y="262" font-family="Segoe UI, Arial" font-size="13" font-weight="bold" fill="#1e293b" text-anchor="middle">Frozen Scientific Protocol v1.1 &amp; Financial Ledger Governance (Decisions D1–D7)</text>

  <!-- Left col -->
  <circle cx="60" cy="291" r="3.5" fill="#2563eb"/>
  <text x="72" y="295" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D1: RECORD_ONLY Prompt &amp; Output Policy</text>
  <text x="72" y="311" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Raw model completions recorded verbatim with secret scrubbing</text>
  <text x="72" y="325" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Byte-identical prompt template across No-RAG and RAG</text>

  <circle cx="60" cy="351" r="3.5" fill="#2563eb"/>
  <text x="72" y="355" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D2a–D2j: Scoring, Universe &amp; NULL Semantics</text>
  <text x="72" y="371" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">ANY_MATCH accuracy on 718 mapped views (311 ambig / 251 unmapped excl.)</text>
  <text x="72" y="385" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">474-class Windows universe (D2d); zero denominators export as null (D2j)</text>

  <circle cx="60" cy="411" r="3.5" fill="#2563eb"/>
  <text x="72" y="415" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D3 &amp; D4: Provenance &amp; Sequential Execution</text>
  <text x="72" y="431" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Sequential execution (concurrency = 1); fixed model alias &amp; settings</text>
  <text x="72" y="445" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Timestamped response IDs retained (backend version/fingerprints null)</text>

  <!-- Right col -->
  <circle cx="450" cy="291" r="3.5" fill="#2563eb"/>
  <text x="462" y="295" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D5: Financial Guard &amp; Worst-Case Reservation</text>
  <text x="462" y="311" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">USD 19.99 hard study ceiling; USD 0.53974560 pre-dispatch attempt hold</text>
  <text x="462" y="325" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Missing usage receipts retain full worst-case hold in settled ledger</text>

  <circle cx="450" cy="351" r="3.5" fill="#2563eb"/>
  <text x="462" y="355" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D6 &amp; D7: Synthetic Paired Benchmark Boundary</text>
  <text x="462" y="371" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Task 2 forensic stop on Mendeley v3 (15,713 discrepancies); T15 deferred</text>
  <text x="462" y="385" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">All claims strictly bounded to synthetic-paired-v1 (640 TEST pairs)</text>

  <circle cx="450" cy="411" r="3.5" fill="#2563eb"/>
  <text x="462" y="415" font-family="Segoe UI, Arial" font-size="11.5" font-weight="bold" fill="#0f172a">D2h &amp; D2i: Retrieval Hit vs. Recall &amp; Failure Axes</text>
  <text x="462" y="431" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">Hit@k (Y_i ∩ R_{i,k} ≠ ∅) distinguished from multi-label Macro Recall@k</text>
  <text x="462" y="445" font-family="Segoe UI, Arial" font-size="10.5" fill="#475569">5 non-mutually-exclusive failure axes evaluated without forced causality</text>
</svg>'''
    svg_path = OUT_DIR / "fig1_system_architecture.svg"
    pdf_path = OUT_DIR / "fig1_system_architecture.pdf"
    png_path = OUT_DIR / "fig1_system_architecture.png"
    svg_path.write_text(svg, encoding="utf-8")
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    subprocess.run([edge, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", str(svg_path)], check=True)
    doc = fitz.open(str(pdf_path))
    pix = doc[0].get_pixmap(dpi=360)
    pix.save(str(png_path))
    doc.close()
    print("Built fig1:", png_path.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 2: Accuracy vs k (Two-panel: Full 0-100% scale + Point & 95% CI view)
# ---------------------------------------------------------------------------
def build_fig2():
    import json
    bundle_path = pathlib.Path(r"C:\Users\hahoa\.codex\artifacts\rag2attck\finalization_repo_20261003\artifacts\results\canonical_metric_bundle_v2.json")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    cond_keys = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["No-RAG\n(k=0)", "RAG\n(k=1)", "RAG\n(k=3)", "RAG\n(k=5)", "RAG\n(k=10)"]
    accs = [bundle["conditions"][c]["rq1_attribution"]["accuracy_end_to_end"] * 100.0 for c in cond_keys]
    ci_lows = [bundle["conditions"][c]["rq1_attribution"]["accuracy_e2e_ci_95"][0] * 100.0 for c in cond_keys]
    ci_highs = [bundle["conditions"][c]["rq1_attribution"]["accuracy_e2e_ci_95"][1] * 100.0 for c in cond_keys]
    yerr_low = [a - l for a, l in zip(accs, ci_lows)]
    yerr_high = [h - a for a, h in zip(accs, ci_highs)]
    x = np.arange(len(labels))
    colors = ["#64748b", "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=360, gridspec_kw={"width_ratios": [1.0, 1.35]})
    fig.suptitle("Figure 2: End-to-End Technique Attribution Accuracy vs. Retrieval Depth (k)", fontsize=13.5, fontweight="bold", y=0.98, color="#0f172a")
    fig.text(0.5, 0.915, "Evaluated on N = 718 scorable mapped-positive TEST views (440 scenario clusters; 1,000 cluster-bootstrap resamples)", ha="center", fontsize=10, color="#475569")

    # Panel A: Full 0-100% Zero-Baseline Scale
    bars = ax1.bar(x, accs, width=0.52, color=colors, alpha=0.88, edgecolor="#1e293b", linewidth=0.8)
    ax1.errorbar(x, accs, yerr=[yerr_low, yerr_high], fmt="none", ecolor="#0f172a", elinewidth=1.5, capsize=4, capthick=1.3)
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("End-to-End Attribution Accuracy (%)", fontsize=10.5, fontweight="bold", color="#1e293b")
    ax1.set_title("(a) Full-Scale Zero-Baseline View (0%–100%)", fontsize=10.5, fontweight="bold", color="#1e293b", pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    for b, a in zip(bars, accs):
        ax1.text(b.get_x() + b.get_width()/2, a + 4.2, f"{a:.2f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a")

    # Panel B: Point Estimate & 95% Cluster-Bootstrap CI View (70%-86%)
    ax2.axhline(accs[0], color="#64748b", linestyle=":", linewidth=1.3, label="No-RAG Baseline (77.99%)")
    ax2.plot(x[1:], accs[1:], color="#1d4ed8", linewidth=1.6, linestyle="--", alpha=0.65, zorder=2)
    ax2.errorbar(x, accs, yerr=[yerr_low, yerr_high], fmt="o", color="#1e3a8a", ecolor="#0f172a", markersize=7, elinewidth=1.8, capsize=5, capthick=1.5, zorder=3, label="Point Estimate & 95% Cluster-Bootstrap CI")
    for xi, a, lo, hi in zip(x, accs, ci_lows, ci_highs):
        ax2.text(xi, hi + 0.35, f"{a:.2f}%\n[{lo:.2f}, {hi:.2f}]", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#0f172a")
    ax2.set_ylim(71.5, 86.2)
    ax2.set_ylabel("Attribution Accuracy (%) [Zoomed Interval View]", fontsize=10.5, fontweight="bold", color="#1e293b")
    ax2.set_title("(b) Point Estimates & 95% Cluster-Bootstrap CIs", fontsize=10.5, fontweight="bold", color="#1e293b", pad=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    ax2.text(0.03, 0.93, "rag_k10 vs. no_rag: ΔAcc = +1.532 pp (95% CI [-2.355, +5.300] pp)\nUnclustered exact McNemar p = 0.4219 (c=72 vs. b=83; Not Significant)", transform=ax2.transAxes, va="top", ha="left", fontsize=8.3, bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0fdf4", edgecolor="#22c55e", lw=1))

    plt.tight_layout(rect=[0, 0, 1, 0.89])
    out_p = OUT_DIR / "fig2_accuracy_vs_k.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig2:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 3: 474-Class Macro-F1 & Delta Bootstrap CIs
# ---------------------------------------------------------------------------
def build_fig3():
    labels = ["No-RAG\n(k=0)", "RAG\n(k=1)", "RAG\n(k=3)", "RAG\n(k=5)", "RAG\n(k=10)"]
    f1_vals = [0.012608, 0.012668, 0.013643, 0.013891, 0.014024]
    deltas = [0.0, 0.000060, 0.001034, 0.001282, 0.001415]
    d_low = [0.0, -0.000242, 0.000632, 0.000860, 0.001011]
    d_high = [0.0, 0.000363, 0.001424, 0.001679, 0.001792]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), dpi=360, gridspec_kw={"width_ratios": [1.1, 1.15]})
    fig.suptitle("Figure 3: 474-Class Macro-F1 and Paired Bootstrap Differences Across Retrieval Depths", fontsize=13, fontweight="bold", y=0.98, color="#0f172a")
    fig.text(0.5, 0.915, "Frozen 474-technique Windows universe (8 supported classes, 466 zero-support classes; support-based upper bound = 8/474 ≈ 0.01688)", ha="center", fontsize=9.8, color="#475569")

    # Left: Macro-F1 from 0 to support-based upper bound
    bars = ax1.bar(x, f1_vals, width=0.5, color=["#64748b", "#8b5cf6", "#7c3aed", "#6d28d9", "#5b21b6"], alpha=0.88, edgecolor="#1e293b")
    ax1.axhline(8.0/474.0, color="#dc2626", linestyle="--", linewidth=1.3, label="Support-Based Upper Bound (8/474 = 0.01688)")
    ax1.set_ylim(0, 0.0190)
    ax1.set_ylabel("474-Class Macro-F1 (0–1 Scale)", fontsize=10, fontweight="bold")
    ax1.set_title("(a) Absolute 474-Class Macro-F1 (Zero-Baseline)", fontsize=10.5, fontweight="bold", pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax1.legend(loc="lower right", fontsize=8.3, framealpha=0.95)
    for b, v in zip(bars, f1_vals):
        ax1.text(b.get_x() + b.get_width()/2, v + 0.00035, f"{v:.4f}\n({v*100:.2f}%)", ha="center", va="bottom", fontsize=8.2, fontweight="bold")

    # Right: Delta Macro-F1 vs No-RAG with 95% Cluster-Bootstrap CI
    rx = np.arange(1, 5)
    r_deltas = deltas[1:]
    r_yerr_lo = [d - l for d, l in zip(r_deltas, d_low[1:])]
    r_yerr_hi = [h - d for d, h in zip(r_deltas, d_high[1:])]
    ax2.axhline(0.0, color="#dc2626", linestyle=":", linewidth=1.4, label="Zero Difference (ΔMacro-F1 = 0)")
    ax2.errorbar(rx, r_deltas, yerr=[r_yerr_lo, r_yerr_hi], fmt="s", color="#6d28d9", ecolor="#0f172a", markersize=7, elinewidth=1.8, capsize=5, capthick=1.5, label="ΔMacro-F1 vs. No-RAG (95% Cluster CI)")
    for xi, d, lo, hi in zip(rx, r_deltas, d_low[1:], d_high[1:]):
        ax2.text(xi, hi + 0.00008, f"+{d:.6f}\n[{lo:+.4f}, {hi:+.4f}]", ha="center", va="bottom", fontsize=8.1, fontweight="bold", color="#0f172a")
    ax2.set_ylim(-0.00045, 0.00225)
    ax2.set_xlim(0.5, 4.5)
    ax2.set_xticks(rx)
    ax2.set_xticklabels(labels[1:], fontsize=9)
    ax2.set_ylabel("ΔMacro-F1 (RAG − No-RAG)", fontsize=10, fontweight="bold")
    ax2.set_title("(b) Macro-F1 Difference & 95% Cluster-Bootstrap CI", fontsize=10.5, fontweight="bold", pad=8)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax2.legend(loc="lower right", fontsize=8.3, framealpha=0.95)

    plt.tight_layout(rect=[0, 0, 1, 0.89])
    out_p = OUT_DIR / "fig3_macro_f1_vs_k.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig3:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 4: Standalone Hit@k vs. Multi-Label Macro Recall@k on N=718 TEST
# ---------------------------------------------------------------------------
def build_fig4():
    labels = ["k = 1", "k = 3", "k = 5", "k = 10"]
    hit_k = [3.7604, 16.4345, 24.0947, 44.7075]
    hit_counts = ["27/718", "118/718", "173/718", "321/718"]
    rec_k = [2.9480, 15.4828, 22.9573, 42.8041]
    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9.2, 4.5), dpi=360)
    b1 = ax.bar(x - w/2, hit_k, width=w, color="#0284c7", edgecolor="#0f172a", linewidth=0.8, label=r"Standalone Hit@k: $\mathbf{1}\{Y_i \cap R_{i,k} \neq \emptyset\}$ (ANY_GT_RETRIEVED)")
    b2 = ax.bar(x + w/2, rec_k, width=w, color="#38bdf8", edgecolor="#0f172a", linewidth=0.8, label=r"Macro Recall@k: $|Y_i \cap R_{i,k}| / |Y_i|$ (Multi-Label Fractional Recall)")

    for bar, val, cnt in zip(b1, hit_k, hit_counts):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.0, f"{val:.2f}%\n({cnt})", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0369a1")
    for bar, val in zip(b2, rec_k):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.0, f"{val:.2f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a")

    ax.set_ylim(0, 54)
    ax.set_ylabel("Retrieval Coverage on TEST Split (%)", fontsize=10.5, fontweight="bold")
    ax.set_title("Figure 4: Standalone Dense Retrieval Hit@k vs. Macro Recall@k on 718 Scorable TEST Views\n(40 TEST multi-label views: Hit@10 = 75.00% [30/40] vs. Macro Recall@10 = 40.83% [TEST+DEV N=44: 72.73% vs. 39.02%])", fontsize=10.0, fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    plt.tight_layout()
    out_p = OUT_DIR / "fig4_retrieval_hit_rate.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig4:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 5: Conditional Attribution Accuracy (Zero-Baseline 0%-108%)
# ---------------------------------------------------------------------------
def build_fig5():
    labels = ["k = 1\n(Hit N=27 | Miss N=691)", "k = 3\n(Hit N=118 | Miss N=600)", "k = 5\n(Hit N=173 | Miss N=545)", "k = 10\n(Hit N=321 | Miss N=397)"]
    p_hit = [100.00, 97.46, 97.11, 91.28]
    c_hit = ["27/27", "115/118", "168/173", "293/321"]
    p_miss = [76.12, 74.83, 73.03, 70.03]
    c_miss = ["526/691", "449/600", "398/545", "278/397"]
    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9.6, 4.7), dpi=360)
    b1 = ax.bar(x - w/2, p_hit, width=w, color="#10b981", edgecolor="#0f172a", linewidth=0.8, label=r"$P(\mathrm{Correct} \mid Y_i \cap R_{i,k} \neq \emptyset)$ [Ground Truth Retrieved in Top-k]")
    b2 = ax.bar(x + w/2, p_miss, width=w, color="#f59e0b", edgecolor="#0f172a", linewidth=0.8, label=r"$P(\mathrm{Correct} \mid Y_i \cap R_{i,k} = \emptyset)$ [Ground Truth Absent from Top-k]")

    for bar, val, cnt in zip(b1, p_hit, c_hit):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.5, f"{val:.2f}%\n({cnt})", ha="center", va="bottom", fontsize=8.4, fontweight="bold", color="#065f46")
    for bar, val, cnt in zip(b2, p_miss, c_miss):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1.5, f"{val:.2f}%\n({cnt})", ha="center", va="bottom", fontsize=8.4, fontweight="bold", color="#92400e")

    ax.set_ylim(0, 116)
    ax.set_ylabel("Conditional Attribution Accuracy (%) [Zero-Baseline]", fontsize=10.5, fontweight="bold")
    ax.set_title("Figure 5: Downstream Attribution Accuracy Conditioned on Retrieval Hit vs. Miss (0%–100% Scale)\n(Observational post-retrieval stratification across N = 718 scorable TEST views; retrieval hit/miss is not randomly assigned)", fontsize=11, fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.2, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="lower right", fontsize=8.8, framealpha=0.95)
    plt.tight_layout()
    out_p = OUT_DIR / "fig5_conditional_accuracy.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig5:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 6: Request Latency Scaling (Zero-Baseline 0 to 5,000 ms)
# ---------------------------------------------------------------------------
def build_fig6():
    labels = ["No-RAG\n(k=0)", "RAG\n(k=1)", "RAG\n(k=3)", "RAG\n(k=5)", "RAG\n(k=10)"]
    mean_ms = [2904.45, 3514.27, 4215.88, 4327.26, 4370.71]
    med_ms = [2302.82, 2617.14, 2743.17, 2873.74, 2667.00]
    x = np.arange(len(labels))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9.2, 4.5), dpi=360)
    b1 = ax.bar(x - w/2, mean_ms, width=w, color="#3b82f6", edgecolor="#0f172a", linewidth=0.8, label="Mean End-to-End Latency (ms)")
    b2 = ax.bar(x + w/2, med_ms, width=w, color="#14b8a6", edgecolor="#0f172a", linewidth=0.8, label="Median End-to-End Latency (ms)")

    for bar, val in zip(b1, mean_ms):
        ax.text(bar.get_x() + bar.get_width()/2, val + 80, f"{val:,.0f} ms\n({val/1000:.2f}s)", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#1e40af")
    for bar, val in zip(b2, med_ms):
        ax.text(bar.get_x() + bar.get_width()/2, val + 80, f"{val:,.0f} ms\n({val/1000:.2f}s)", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#0f766e")

    ax.set_ylim(0, 5200)
    ax.set_ylabel("Client End-to-End Latency (ms) [Zero-Baseline]", fontsize=10.5, fontweight="bold")
    ax.set_title("Figure 6: Request Inference Latency Scaling Across Conditions (0–5,000 ms Scale)\n(N = 1,280 TEST requests/condition including retry backoff; P95 withheld per Protocol v1.1)", fontsize=11, fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    plt.tight_layout()
    out_p = OUT_DIR / "fig6_latency_vs_k.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig6:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 7: Cost (Ledger vs Usage Estimate) & Token Consumption
# ---------------------------------------------------------------------------
def build_fig7():
    labels = ["No-RAG\n(k=0)", "RAG\n(k=1)*", "RAG\n(k=3)", "RAG\n(k=5)", "RAG\n(k=10)"]
    ledger_cost = [0.467144, 1.297234, 1.178880, 1.483118, 2.149384]
    usage_cost = [0.467144, 0.757488, 1.178880, 1.483118, 2.149384]
    tot_tokens_m = [1.072605, 1.894682, 3.183740, 4.336927, 6.973620]
    x = np.arange(len(labels))
    w = 0.26

    fig, ax1 = plt.subplots(figsize=(9.8, 4.7), dpi=360)
    ax2 = ax1.twinx()

    b1 = ax1.bar(x - w, ledger_cost, width=w, color="#f59e0b", edgecolor="#0f172a", linewidth=0.8, label="Conservative Ledger Spend ($ USD)")
    b2 = ax1.bar(x, usage_cost, width=w, color="#fbbf24", edgecolor="#0f172a", linewidth=0.8, hatch="//", label="Token-Usage Estimated Cost ($ USD, net of cache)")
    b3 = ax2.bar(x + w, tot_tokens_m, width=w, color="#6366f1", edgecolor="#0f172a", linewidth=0.8, label="Total Tokens Consumed (Millions: Input + Output)")

    for bar, val in zip(b1, ledger_cost):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.04, f"${val:.2f}", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#b45309")
    for bar, val in zip(b2, usage_cost):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.04, f"${val:.2f}", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#78350f")
    for bar, val in zip(b3, tot_tokens_m):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 0.12, f"{val:.2f}M", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color="#4338ca")

    ax1.set_ylim(0, 2.65)
    ax2.set_ylim(0, 8.2)
    ax1.set_ylabel("Financial Spend ($ USD)", fontsize=10.5, fontweight="bold", color="#b45309")
    ax2.set_ylabel("Total Tokens Consumed (Millions)", fontsize=10.5, fontweight="bold", color="#4338ca")
    ax1.set_title("Figure 7: Conservative Ledger Spend, Token-Usage Cost, and Token Volume Across Conditions\n(*rag_k1 ledger spend [$1.30] includes a $0.5397 worst-case hold for 1 retry attempt lacking a usage receipt; usage cost = $0.76)", fontsize=10.5, fontweight="bold", pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", fontsize=8.4, framealpha=0.95)
    plt.tight_layout()
    out_p = OUT_DIR / "fig7_cost_and_tokens_vs_k.png"
    fig.savefig(out_p, dpi=360)
    plt.close(fig)
    print("Built fig7:", out_p.stat().st_size)

# ---------------------------------------------------------------------------
# Figure 8: High-res render from canonical PDF (360 DPI)
# ---------------------------------------------------------------------------
def build_fig8():
    src_pdf = pathlib.Path(r"C:\Users\hahoa\.codex\artifacts\rag2attck\finalization_repo_20261003\docs\report\figures\fig8_failure_decomposition.pdf")
    out_p = OUT_DIR / "fig8_failure_decomposition.png"
    doc = fitz.open(str(src_pdf))
    pix = doc[0].get_pixmap(dpi=360)
    pix.save(str(out_p))
    doc.close()
    print("Built fig8:", out_p.stat().st_size)

if __name__ == "__main__":
    build_fig1()
    build_fig2()
    build_fig3()
    build_fig4()
    build_fig5()
    build_fig6()
    build_fig7()
    build_fig8()
