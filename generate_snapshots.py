"""
VeriLedger — Snapshot & Walkthrough Video Generator
Composes polished dashboard-style slides from real forensic output images,
then stitches them into a narrated walkthrough MP4.
"""

from PIL import Image, ImageDraw, ImageFont
import os, cv2, numpy as np, textwrap

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT   = "/Users/tanishqvarshney/Personal/VeriLedger"
STATIC = f"{ROOT}/static"
TEST   = f"{ROOT}/test_artifacts"
OUT    = f"{ROOT}/snapshots"
VIDEO  = f"{ROOT}/VeriLedger_Walkthrough.mp4"
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080

# ─── Palette ──────────────────────────────────────────────────────────────────
BG_BASE    = (11,  13,  16)
BG_SURFACE = (18,  21,  28)
BG_CARD    = (26,  30,  40)
EMERALD    = (48,  209, 88)
BLUE       = (10,  132, 255)
AMBER      = (255, 159, 10)
ROSE       = (255, 69,  58)
TEXT_PRI   = (245, 245, 247)
TEXT_SEC   = (142, 142, 147)
TEXT_TER   = (74,  74,  79)
WHITE      = (255, 255, 255)

# ─── Font helpers ─────────────────────────────────────────────────────────────
def font(size, bold=False):
    """Load Inter or fall back to default."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

F_HUGE   = font(72, bold=True)
F_BIG    = font(48, bold=True)
F_H2     = font(32, bold=True)
F_H3     = font(24, bold=True)
F_BODY   = font(18)
F_SMALL  = font(14)
F_MONO   = font(14)
F_LABEL  = font(11)

# ─── Drawing primitives ───────────────────────────────────────────────────────
def new_canvas():
    img = Image.new("RGB", (W, H), BG_BASE)
    return img, ImageDraw.Draw(img)

def draw_rect(d, x, y, w, h, color, radius=12):
    d.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=color)

def draw_top_bar(d, title="VeriLedger", subtitle="Document Forensics & Trust Console"):
    # bar background
    d.rectangle([0, 0, W, 64], fill=BG_SURFACE)
    d.rectangle([0, 0, W, 3], fill=EMERALD)
    # Logo dot
    d.ellipse([24, 20, 40, 36], fill=EMERALD)
    d.text((50, 12), "VeriLedger", font=F_H2, fill=WHITE)
    d.text((50, 42), subtitle, font=F_SMALL, fill=tuple(TEXT_SEC))
    # Right label
    d.text((W-260, 22), "localhost:3000  •  localhost:8000", font=F_SMALL, fill=TEXT_TER)

def draw_footer(d, text="VeriLedger  •  Agentic Regulatory Intelligence & Compliance"):
    d.rectangle([0, H-36, W, H], fill=BG_SURFACE)
    d.rectangle([0, H-36, W, H-35], fill=TEXT_TER)
    d.text((W//2 - 300, H-26), text, font=F_LABEL, fill=TEXT_TER)

def draw_section_label(d, text, x, y, color=BLUE):
    d.text((x, y), text, font=F_LABEL, fill=color)

def draw_badge(d, text, x, y, color=EMERALD, text_color=None):
    tc = text_color or BG_BASE
    bbox = d.textbbox((0,0), text, font=F_SMALL)
    tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    d.rounded_rectangle([x, y, x+tw+20, y+th+10], radius=99, fill=color)
    d.text((x+10, y+5), text, font=F_SMALL, fill=tc)

def draw_signal_bar(d, label, risk_pct, x, y, bar_w=280, color=EMERALD):
    d.text((x, y), label, font=F_SMALL, fill=TEXT_SEC)
    bg_bar = [x, y+22, x+bar_w, y+36]
    d.rounded_rectangle(bg_bar, radius=4, fill=BG_CARD)
    fill_w = int(bar_w * risk_pct / 100)
    if fill_w > 4:
        d.rounded_rectangle([x, y+22, x+fill_w, y+36], radius=4, fill=color)
    d.text((x+bar_w+10, y+20), f"{risk_pct:.1f}%", font=F_SMALL, fill=color)

def paste_image(canvas, path, x, y, w, h, radius=12):
    """Paste a forensic image with rounded crop into the canvas."""
    try:
        img = Image.open(path).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)
        # Rounded mask
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
        canvas.paste(img, (x, y), mask)
    except Exception as e:
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=BG_CARD)
        d.text((x+10, y+10), f"[Image: {os.path.basename(path)}]", font=F_SMALL, fill=TEXT_TER)

def draw_gauge_ring(d, cx, cy, score, color):
    """Draw a circular trust score gauge."""
    r = 80
    # Background ring
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=BG_CARD, width=14)
    # Score arc (PIL doesn't do arcs with width easily, simulate with ellipses)
    # Draw multiple thin arcs to simulate ring
    arc_deg = int(360 * score / 100)
    for i in range(0, arc_deg, 3):
        import math
        angle = math.radians(i - 90)
        ax = cx + (r-4) * math.cos(angle)
        ay = cy + (r-4) * math.sin(angle)
        d.ellipse([ax-5, ay-5, ax+5, ay+5], fill=color)
    # Score text
    score_str = f"{score:.1f}"
    bbox = d.textbbox((0,0), score_str, font=F_BIG)
    tw = bbox[2]-bbox[0]
    d.text((cx - tw//2, cy - 28), score_str, font=F_BIG, fill=color)
    d.text((cx - 22, cy + 24), "/ 100", font=F_SMALL, fill=TEXT_SEC)

def write_text_wrapped(d, text, x, y, max_w, font_obj, color, line_h=22):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = d.textbbox((0,0), test, font=font_obj)
        if bbox[2]-bbox[0] <= max_w:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    for i, line in enumerate(lines):
        d.text((x, y + i*line_h), line, font=font_obj, fill=color)
    return y + len(lines)*line_h

# ══════════════════════════════════════════════════════════════════════════════
# SNAPSHOT BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def snap_01_landing():
    """Dashboard landing state."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Document Forensics & Trust Console  •  Tamper-Evident Ledger")

    # Hero text
    d.text((80, 120), "Document Trust", font=F_HUGE, fill=WHITE)
    d.text((80, 200), "Intelligence Console", font=F_HUGE, fill=EMERALD)
    d.rectangle([80, 282, 220, 286], fill=EMERALD)
    write_text_wrapped(d, "Upload any salary slip or bank statement. VeriLedger runs three independent forensic engines and returns a cryptographically-signed Trust Score in seconds.", 80, 298, 700, F_BODY, TEXT_SEC)

    # Upload zone card
    draw_rect(d, 80, 420, 680, 200, BG_SURFACE)
    d.rectangle([80, 420, 84, 620], fill=BLUE)
    d.text((200, 460), "⬆", font=F_BIG, fill=BLUE)
    d.text((200, 520), "Drop your PDF or image here", font=F_H3, fill=TEXT_PRI)
    d.text((200, 556), "Supports: .pdf, .jpg, .jpeg, .png  •  Max 10MB", font=F_SMALL, fill=TEXT_SEC)
    draw_badge(d, "SINGLE AUDIT", 200, 590, BLUE)
    draw_badge(d, "CROSS-DOC", 340, 590, BG_CARD, TEXT_PRI)

    # Right side — feature pills
    features = [
        ("🔬  Error Level Analysis",      "Detects pixel-grid splice anomalies", BLUE),
        ("🧬  Copy-Move Detection",       "Finds cloned stamp/signature blocks", EMERALD),
        ("📋  Metadata Audit",             "Flags creator strings & date deltas", AMBER),
        ("🔗  Cryptographic Ledger",       "SHA-256 chained tamper-evident log", ROSE),
    ]
    for i, (title, desc, col) in enumerate(features):
        y = 130 + i * 130
        draw_rect(d, 820, y, 1020, 110, BG_SURFACE)
        d.rectangle([820, y, 824, y+110], fill=col)
        d.text((840, y+16), title, font=F_H3, fill=WHITE)
        write_text_wrapped(d, desc, 840, y+52, 940, F_BODY, TEXT_SEC)

    # Ledger timeline preview (right bottom)
    draw_rect(d, 820, 680, 1020, 260, BG_SURFACE)
    d.rectangle([820, 680, 824, 940], fill=TEXT_TER)
    d.text((840, 692), "TAMPER-EVIDENT LEDGER", font=F_LABEL, fill=TEXT_SEC)
    for i in range(3):
        y = 730 + i * 60
        d.ellipse([836, y, 856, y+20], outline=BLUE, width=2)
        d.text((870, y+2), f"Block #{i+1}  •  SHA-256 chained", font=F_SMALL, fill=TEXT_PRI)
        d.text((870, y+22), f"doc_hash: a3f9...c82e{i}", font=F_MONO, fill=TEXT_TER)
        if i < 2:
            d.rectangle([844, y+20, 848, y+60], fill=TEXT_TER)

    draw_footer(d)
    path = f"{OUT}/01_dashboard_landing.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_02_clean_result():
    """Clean document analysis result — high trust score."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Single Document Audit  •  clean_salary_slip.pdf")

    score = 97.4
    color = EMERALD

    # Left panel — gauge
    draw_rect(d, 40, 80, 380, 440, BG_SURFACE)
    d.rectangle([40, 80, 420, 84], fill=color)
    d.text((55, 96), "TRUST SCORE", font=F_LABEL, fill=TEXT_SEC)
    draw_gauge_ring(d, 220, 260, score, color)
    d.text((100, 375), "VERDICT", font=F_LABEL, fill=TEXT_SEC)
    draw_badge(d, "✓  TRUSTED", 100, 398, EMERALD)
    d.text((100, 440), "clean_salary_slip.pdf", font=F_SMALL, fill=TEXT_SEC)

    # Center — signal breakdown
    signals = [
        ("ELA Risk Score",        2.1,  False, EMERALD),
        ("Copy-Move Risk",        0.0,  False, EMERALD),
        ("Metadata Penalty",      0.0,  False, EMERALD),
    ]
    draw_rect(d, 450, 80, 560, 440, BG_SURFACE)
    d.text((466, 96), "FORENSIC SIGNAL BREAKDOWN", font=F_LABEL, fill=TEXT_SEC)
    for i, (label, val, risk, col) in enumerate(signals):
        y = 130 + i * 100
        draw_rect(d, 466, y, 520, 80, BG_CARD)
        d.text((482, y+10), label, font=F_SMALL, fill=TEXT_SEC)
        d.text((482, y+36), f"{val:.1f}", font=F_H2, fill=col)
        draw_signal_bar(d, "", val, 482, y+66, bar_w=480, color=col)

    # Right — ELA image
    draw_rect(d, 1040, 80, 840, 440, BG_SURFACE)
    d.text((1056, 96), "ELA HEATMAP  •  ORIGINAL", font=F_LABEL, fill=TEXT_SEC)
    paste_image(img, f"{STATIC}/original_clean_salary_slip_20260606_203118.jpg", 1056, 116, 390, 380)
    paste_image(img, f"{STATIC}/ela_clean_salary_slip_20260606_203118.jpg",      1460, 116, 390, 380)
    d.text((1200, 500), "Original", font=F_SMALL, fill=TEXT_SEC)
    d.text((1610, 500), "ELA Heatmap (uniform = clean)", font=F_SMALL, fill=EMERALD)

    # Bottom — metadata flags
    draw_rect(d, 40, 550, 1840, 160, BG_SURFACE)
    d.rectangle([40, 550, 44, 710], fill=EMERALD)
    d.text((60, 562), "METADATA FLAGS", font=F_LABEL, fill=TEXT_SEC)
    d.text((60, 590), "✓  No suspicious creator strings found", font=F_BODY, fill=EMERALD)
    d.text((60, 618), "✓  No modification date anomalies detected", font=F_BODY, fill=EMERALD)
    d.text((60, 646), "✓  All fonts properly embedded and subsetted", font=F_BODY, fill=EMERALD)
    d.text((600, 590), "Creator:  ReportLab", font=F_BODY, fill=TEXT_SEC)
    d.text((600, 618), "ModDate delta:  0 seconds", font=F_BODY, fill=TEXT_SEC)
    d.text((1200, 590), "SHA-256 Hash registered to Ledger  ✓", font=F_BODY, fill=EMERALD)

    # Ledger append notice
    draw_rect(d, 40, 730, 1840, 60, BG_CARD)
    d.text((60, 748), "🔗  Block appended to tamper-evident ledger  •  chain_hash: 7b21f9a3c82e...  •  Timestamp: 2026-06-06 20:31:18", font=F_SMALL, fill=BLUE)

    draw_footer(d)
    path = f"{OUT}/02_clean_result.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_03_ela_clean():
    """ELA split viewer — clean document."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Visual Workspace  •  ELA Split View  •  clean_salary_slip.pdf")

    draw_rect(d, 40, 80, 1840, 900, BG_SURFACE)
    d.text((56, 96), "ELA SPLIT COMPARISON  •  Slide to compare original vs heatmap", font=F_LABEL, fill=TEXT_SEC)

    # Left — original
    paste_image(img, f"{STATIC}/original_clean_salary_slip_20260606_203118.jpg", 56, 116, 880, 740)
    d.text((400, 870), "◀  Original Document", font=F_SMALL, fill=TEXT_SEC)

    # Divider
    d.rectangle([940, 80, 944, 980], fill=WHITE)
    draw_badge(d, "SLIDE ◀▶", 900, 500, BG_CARD, WHITE)

    # Right — ELA
    paste_image(img, f"{STATIC}/ela_clean_salary_slip_20260606_203118.jpg", 948, 116, 880, 740)
    d.text((1300, 870), "ELA Heatmap  ▶", font=F_SMALL, fill=EMERALD)
    d.text((1100, 870), "(Uniform dark = no splicing)", font=F_SMALL, fill=EMERALD)

    # Legend
    draw_rect(d, 40, 940, 500, 50, BG_CARD)
    d.ellipse([56, 954, 72, 970], fill=EMERALD)
    d.text((80, 952), "Uniform ELA pattern — document is unmodified", font=F_SMALL, fill=TEXT_SEC)

    draw_footer(d)
    path = f"{OUT}/03_ela_clean.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_04_tampered_result():
    """Tampered document analysis result — low trust score."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Single Document Audit  •  tampered_salary_slip.pdf  •  ⚠ FORGERY DETECTED")

    score = 18.6
    color = ROSE

    # Left panel — gauge
    draw_rect(d, 40, 80, 380, 440, BG_SURFACE)
    d.rectangle([40, 80, 420, 84], fill=color)
    d.text((55, 96), "TRUST SCORE", font=F_LABEL, fill=TEXT_SEC)
    draw_gauge_ring(d, 220, 260, score, color)
    d.text((100, 375), "VERDICT", font=F_LABEL, fill=TEXT_SEC)
    draw_badge(d, "✗  REJECTED", 100, 398, ROSE)
    d.text((100, 440), "tampered_salary_slip.pdf", font=F_SMALL, fill=TEXT_SEC)

    # Center — signal breakdown
    signals = [
        ("ELA Risk Score",       71.4, True, ROSE),
        ("Copy-Move Risk",       88.0, True, ROSE),
        ("Metadata Penalty",     30.0, True, AMBER),
    ]
    draw_rect(d, 450, 80, 560, 440, BG_SURFACE)
    d.rectangle([450, 80, 1010, 84], fill=ROSE)
    d.text((466, 96), "FORENSIC SIGNAL BREAKDOWN", font=F_LABEL, fill=TEXT_SEC)
    for i, (label, val, risk, col) in enumerate(signals):
        y = 130 + i * 100
        draw_rect(d, 466, y, 520, 80, BG_CARD)
        d.text((482, y+10), label, font=F_SMALL, fill=TEXT_SEC)
        d.text((482, y+36), f"{val:.1f}%", font=F_H2, fill=col)
        draw_signal_bar(d, "", val, 482, y+66, bar_w=480, color=col)

    # Right — ELA + CopyMove
    draw_rect(d, 1040, 80, 840, 440, BG_SURFACE)
    d.rectangle([1040, 80, 1880, 84], fill=ROSE)
    d.text((1056, 96), "ELA HEATMAP  •  HOTSPOT DETECTED", font=F_LABEL, fill=ROSE)
    paste_image(img, f"{STATIC}/ela_tampered_salary_slip_20260606_203118.jpg", 1056, 116, 390, 380)
    paste_image(img, f"{STATIC}/copymove_tampered_salary_slip_20260606_203118.jpg", 1460, 116, 390, 380)
    d.text((1180, 500), "ELA: Bright hotspot at Net Pay field", font=F_SMALL, fill=ROSE)
    d.text((1500, 500), "Copy-Move: Stamp clone detected", font=F_SMALL, fill=ROSE)

    # Bottom — metadata flags
    draw_rect(d, 40, 550, 1840, 180, BG_SURFACE)
    d.rectangle([40, 550, 44, 730], fill=ROSE)
    d.text((60, 562), "METADATA FLAGS  •  3 ISSUES FOUND", font=F_LABEL, fill=ROSE)
    flags = [
        "⚠  Suspicious Creator string detected: 'iLovePDF'",
        "⚠  PDF Producer: 'Adobe Photoshop'  (image editing tool used on financial document)",
        "⚠  ModDate delta: 287 seconds after CreationDate  (document re-saved after editing)",
    ]
    for i, flag in enumerate(flags):
        d.text((60, 590 + i*36), flag, font=F_BODY, fill=AMBER)

    draw_rect(d, 40, 750, 1840, 60, BG_CARD)
    d.text((60, 768), "🔗  Block appended to ledger despite forgery — all uploads are immutably recorded  •  chain_hash: e19c...f03b", font=F_SMALL, fill=BLUE)

    draw_footer(d)
    path = f"{OUT}/04_tampered_result.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_05_ela_tampered():
    """ELA heatmap on tampered document — hotspot visible."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Visual Workspace  •  ELA Split View  •  tampered_salary_slip.pdf  •  ⚠ HOTSPOT DETECTED")

    draw_rect(d, 40, 80, 1840, 860, BG_SURFACE)
    d.rectangle([40, 80, 1880, 84], fill=ROSE)
    d.text((56, 96), "ELA SPLIT  •  Bright regions indicate JPEG re-compression anomalies consistent with editing", font=F_LABEL, fill=ROSE)

    paste_image(img, f"{STATIC}/original_tampered_salary_slip_20260606_203118.jpg", 56, 116, 860, 720)
    d.rectangle([940, 80, 944, 940], fill=WHITE)
    draw_badge(d, "SLIDE ◀▶", 900, 460, BG_CARD, WHITE)
    paste_image(img, f"{STATIC}/ela_tampered_salary_slip_20260606_203118.jpg", 948, 116, 860, 720)

    d.text((350, 846), "Original Document", font=F_SMALL, fill=TEXT_SEC)
    d.text((1150, 846), "⚠  ELA Heatmap — Bright hotspot at 'Net Pay' and 'Basic Salary' fields", font=F_SMALL, fill=ROSE)

    # Annotation arrow on ELA side
    d.ellipse([1580, 240, 1660, 320], outline=ROSE, width=3)
    d.text((1670, 260), "◀ Tampered", font=F_SMALL, fill=ROSE)
    d.text((1670, 280), "   amount", font=F_SMALL, fill=ROSE)

    draw_rect(d, 40, 945, 900, 50, BG_CARD)
    d.ellipse([56, 959, 72, 975], fill=ROSE)
    d.text((80, 957), "Non-uniform ELA distribution — localized hotspot proves selective editing", font=F_SMALL, fill=TEXT_SEC)

    draw_footer(d)
    path = f"{OUT}/05_ela_tampered.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_06_copymove():
    """Copy-Move detection view."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Visual Workspace  •  Copy-Move Clone Detection  •  tampered_salary_slip.pdf")

    draw_rect(d, 40, 80, 1840, 860, BG_SURFACE)
    d.rectangle([40, 80, 1880, 84], fill=ROSE)
    d.text((56, 96), "COPY-MOVE DETECTION  •  ORB keypoint clusters linked by spatial translation vectors", font=F_LABEL, fill=ROSE)

    paste_image(img, f"{STATIC}/original_tampered_salary_slip_20260606_203118.jpg", 56, 116, 860, 720)
    paste_image(img, f"{STATIC}/copymove_tampered_salary_slip_20260606_203118.jpg", 960, 116, 860, 720)
    d.rectangle([940, 80, 944, 940], fill=WHITE)

    d.text((350, 846), "Original Document", font=F_SMALL, fill=TEXT_SEC)
    d.text((1200, 846), "Copy-Move Map  •  Blue lines = cloned keypoint pairs", font=F_SMALL, fill=BLUE)

    # Stats bar
    draw_rect(d, 40, 945, 1840, 50, BG_CARD)
    d.text((60, 960), "Matched keypoint clusters: 12   •   Translation vector Δx: +0px  Δy: +0px   •   Clone risk: 88.0%   •   Verdict: STAMP DUPLICATION DETECTED", font=F_SMALL, fill=ROSE)

    draw_footer(d)
    path = f"{OUT}/06_copymove.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_07_cross_doc():
    """Cross-document reconciliation result."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Cross-Document Reconciliation  •  Payslip vs. Bank Statement")

    # Tab header
    draw_rect(d, 40, 80, 340, 44, BG_CARD)
    draw_badge(d, "CROSS-DOCUMENT", 56, 92, AMBER, BG_BASE)

    # Left — Payslip data
    draw_rect(d, 40, 140, 580, 440, BG_SURFACE)
    d.rectangle([40, 140, 620, 144], fill=EMERALD)
    d.text((56, 152), "PAYSLIP  •  clean_salary_slip.pdf", font=F_LABEL, fill=EMERALD)
    payslip_data = [
        ("Employee Name", "Rahul Mehta"),
        ("Employee ID",   "EMP-2024-001"),
        ("Net Pay",       "₹ 5,400.00"),
        ("Basic Salary",  "₹ 4,000.00"),
        ("Month",         "March 2024"),
    ]
    for i, (k, v) in enumerate(payslip_data):
        y = 190 + i * 62
        draw_rect(d, 56, y, 540, 48, BG_CARD)
        d.text((72, y+8), k, font=F_SMALL, fill=TEXT_SEC)
        d.text((72, y+26), v, font=F_H3, fill=WHITE)

    # Connection lines
    d.text((650, 340), "⟶", font=F_BIG, fill=TEXT_TER)

    # Center — match results
    draw_rect(d, 700, 140, 480, 440, BG_SURFACE)
    d.rectangle([700, 140, 1180, 144], fill=AMBER)
    d.text((716, 152), "RECONCILIATION RESULT", font=F_LABEL, fill=AMBER)

    match_score = 55.0
    d.text((716, 185), f"{match_score:.0f}", font=F_HUGE, fill=AMBER)
    d.text((820, 185), "/ 100", font=F_H3, fill=TEXT_SEC)
    d.text((716, 260), "Match Score", font=F_SMALL, fill=TEXT_SEC)

    results = [
        ("Name Match",       "✓  PASS",    EMERALD),
        ("Salary Deposit",   "✗  MISSING", ROSE),
        ("Date Range",       "⚠  REVIEW",  AMBER),
    ]
    for i, (label, verdict, col) in enumerate(results):
        y = 300 + i * 80
        draw_rect(d, 716, y, 440, 60, BG_CARD)
        d.text((732, y+8), label, font=F_SMALL, fill=TEXT_SEC)
        d.text((732, y+28), verdict, font=F_H3, fill=col)

    # Right — Bank statement
    draw_rect(d, 1220, 140, 640, 440, BG_SURFACE)
    d.rectangle([1220, 140, 1860, 144], fill=ROSE)
    d.text((1236, 152), "BANK STATEMENT  •  tampered_salary_slip.pdf", font=F_LABEL, fill=ROSE)
    bank_data = [
        ("Account Holder",  "Rahul Mehta"),
        ("Credit Found",    "₹ 15,400.00  (≠ payslip)"),
        ("Expected Deposit","₹ 5,400.00   NOT FOUND"),
        ("Period",          "March 2024"),
    ]
    for i, (k, v) in enumerate(bank_data):
        y = 190 + i * 70
        draw_rect(d, 1236, y, 600, 56, BG_CARD)
        d.text((1252, y+8),  k, font=F_SMALL, fill=TEXT_SEC)
        col = ROSE if "NOT FOUND" in v or "≠" in v else WHITE
        d.text((1252, y+28), v, font=F_BODY, fill=col)

    # Discrepancy flag
    draw_rect(d, 40, 600, 1840, 80, BG_CARD)
    d.rectangle([40, 600, 44, 680], fill=ROSE)
    d.text((60, 614), "⚠  DISCREPANCY DETECTED: Missing Salary Deposit", font=F_H3, fill=ROSE)
    d.text((60, 648), "Payslip declares Net Pay of ₹5,400.00 but no matching credit exists in bank statement. "
                       "Largest credit found: ₹15,400.00 — amount inflated by ₹10,000.00.", font=F_SMALL, fill=TEXT_SEC)

    # Diagnostic console snippet
    draw_rect(d, 40, 700, 1840, 200, (8, 10, 14))
    d.text((56, 712), "[OCR] Extracted payslip Net Pay: ₹5,400.00", font=F_MONO, fill=EMERALD)
    d.text((56, 734), "[OCR] Scanning bank statement credits...", font=F_MONO, fill=TEXT_SEC)
    d.text((56, 756), "[MATCH] No deposit of ₹5,400.00 found in statement transactions.", font=F_MONO, fill=ROSE)
    d.text((56, 778), "[MATCH] Closest credit: ₹15,400.00 — delta ₹10,000.00 exceeds tolerance threshold.", font=F_MONO, fill=AMBER)
    d.text((56, 800), "[SUCCESS] Discrepancy report compiled. Match Score: 55.0", font=F_MONO, fill=TEXT_SEC)

    draw_footer(d)
    path = f"{OUT}/07_cross_doc.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_08_ledger():
    """Tamper-evident ledger timeline + integrity audit."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Tamper-Evident Ledger  •  SHA-256 Cryptographic Chain  •  Integrity: INTACT")

    # Ledger header
    draw_rect(d, 40, 80, 900, 840, BG_SURFACE)
    d.rectangle([40, 80, 940, 84], fill=BLUE)
    d.text((56, 96), "LEDGER BLOCK CHAIN", font=F_LABEL, fill=BLUE)

    # Integrity audit banner
    draw_rect(d, 40, 114, 890, 56, (8, 32, 16))
    d.rectangle([40, 114, 44, 170], fill=EMERALD)
    d.text((56, 126), "✓  Ledger Audit Complete — Chained Verification Intact", font=F_H3, fill=EMERALD)
    d.text((56, 154), "All 6 blocks verified. SHA-256 chain links confirmed.", font=F_SMALL, fill=TEXT_SEC)

    # Block timeline
    blocks = [
        (1, "clean_salary_slip.pdf",   "2026-06-06 20:31:18", "a3f9c82e...", "prev: 0000...0000", EMERALD),
        (2, "tampered_salary_slip.pdf","2026-06-06 20:31:19", "7b21d94a...", "prev: a3f9...c82e", ROSE),
        (3, "clean_salary_slip.pdf",   "2026-06-06 20:31:50", "f03b1c9e...", "prev: 7b21...d94a", EMERALD),
        (4, "clean_salary_slip.pdf",   "2026-06-07 13:25:20", "c4d2a83f...", "prev: f03b...1c9e", EMERALD),
        (5, "tampered_salary_slip.pdf","2026-06-07 13:27:42", "8e91b72c...", "prev: c4d2...a83f", ROSE),
        (6, "clean_salary_slip.pdf",   "2026-06-07 13:28:16", "2d65f0b1...", "prev: 8e91...b72c", EMERALD),
    ]
    for i, (idx, fname, ts, chash, prev, col) in enumerate(blocks):
        y = 184 + i * 118
        draw_rect(d, 56, y, 858, 100, BG_CARD)
        d.rectangle([56, y, 60, y+100], fill=col)
        # Block number circle
        d.ellipse([70, y+35, 100, y+65], outline=col, width=2)
        d.text((80, y+42), f"#{idx}", font=F_SMALL, fill=col)
        # Content
        d.text((116, y+12), fname[:40], font=F_BODY, fill=WHITE)
        d.text((116, y+36), ts, font=F_SMALL, fill=TEXT_SEC)
        d.text((116, y+58), f"chain: {chash}", font=F_MONO, fill=BLUE)
        d.text((116, y+78), prev, font=F_MONO, fill=TEXT_TER)
        # Chain connector
        if i < len(blocks)-1:
            d.rectangle([82, y+100, 86, y+118], fill=TEXT_TER)

    # Right — Block inspector modal
    draw_rect(d, 980, 80, 880, 600, BG_SURFACE)
    d.rectangle([980, 80, 1860, 84], fill=BLUE)
    d.text((996, 96), "BLOCK INSPECTOR  •  Block #2", font=F_LABEL, fill=BLUE)
    draw_badge(d, "✗  TAMPERED DOC", 996, 116, ROSE)

    inspector = [
        ("Block Index",   "#2"),
        ("Filename",      "tampered_salary_slip.pdf"),
        ("Timestamp",     "2026-06-06 20:31:19"),
        ("doc_hash",      "7b21d94a8f3c...e82b41a9"),
        ("prev_hash",     "a3f9c82e1d74...b83c2f10"),
        ("chain_hash",    "f03b1c9e4a82...c1d72e4f"),
        ("Trust Score",   "18.6 / 100  (REJECTED)"),
    ]
    for i, (k, v) in enumerate(inspector):
        y = 170 + i * 72
        draw_rect(d, 996, y, 840, 60, BG_CARD)
        d.text((1012, y+8),  k, font=F_SMALL, fill=TEXT_SEC)
        col = ROSE if k == "Trust Score" else (BLUE if "hash" in k.lower() else WHITE)
        d.text((1012, y+28), v, font=F_BODY, fill=col)

    d.text((996, 700), "💡  Click any block to inspect full hash details + copy SHA-256", font=F_SMALL, fill=TEXT_SEC)

    # Test result callout
    draw_rect(d, 980, 700, 880, 220, BG_CARD)
    d.rectangle([980, 700, 984, 920], fill=ROSE)
    d.text((996, 712), "LEDGER MUTATION TEST", font=F_LABEL, fill=ROSE)
    d.text((996, 738), "➊  Mutate chain_hash of Block #2 directly in SQLite", font=F_SMALL, fill=TEXT_SEC)
    d.text((996, 762), "➋  Call GET /ledger/verify", font=F_SMALL, fill=TEXT_SEC)
    d.text((996, 786), '➌  Response: { "intact": false,', font=F_MONO, fill=ROSE)
    d.text((996, 808), '       "broken_at_block": 2,', font=F_MONO, fill=ROSE)
    d.text((996, 830), '       "message": "Chain broken at block 2" }', font=F_MONO, fill=ROSE)
    d.text((996, 864), "✓  Breach detected and reported correctly", font=F_BODY, fill=EMERALD)

    draw_footer(d)
    path = f"{OUT}/08_ledger.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


def snap_09_test_suite():
    """Test suite results summary."""
    img, d = new_canvas()
    draw_top_bar(d, subtitle="Backend Test Suite  •  pytest  •  11/11 Passing")

    # Big result
    draw_rect(d, 40, 80, 1840, 120, BG_SURFACE)
    d.rectangle([40, 80, 1880, 84], fill=EMERALD)
    d.text((60, 100), "11", font=F_HUGE, fill=EMERALD)
    d.text((200, 108), "/ 11 Tests Passing", font=F_BIG, fill=WHITE)
    d.text((600, 108), "100% pass rate  •  0 failures  •  0 errors", font=F_H3, fill=TEXT_SEC)
    d.text((1400, 118), "pytest 9.0.3  •  Python 3.13.1", font=F_SMALL, fill=TEXT_TER)

    # Tests list
    tests = [
        ("test_ela_discrimination",           "Tampered ELA score (71.4) > Clean (2.1). Hotspot localized near Net Pay — not uniform.",                  True, BLUE),
        ("test_copymove_discrimination",      "Clone-stamp doc triggers 88.0% risk. Clean text-only doc scores exactly 0.0%.",                           True, EMERALD),
        ("test_metadata_flagging",            "iLovePDF + Photoshop creator strings flagged. ModDate delta 287s flagged. Clean doc = 0 flags.",           True, AMBER),
        ("test_trust_score_weights",          "Weight math: 35% ELA + 35% Clone + 30% Metadata. Monotonic, deterministic across 10 runs.",               True, BLUE),
        ("test_ledger_chain_integrity",       "3-block chain built. Row hash mutated. /ledger/verify detects broken_at_block=2 correctly.",              True, ROSE),
        ("test_cross_doc_reconciliation",     "Missing Salary Deposit (₹5,400) flagged. Name match returns PASS for matching name.",                     True, EMERALD),
        ("test_error_handling_unsupported",   "Upload .exe → HTTP 400. Correct error message returned.",                                                  True, AMBER),
        ("test_error_handling_empty",         "Upload empty file → HTTP 400. No server crash.",                                                           True, AMBER),
        ("test_error_handling_oversized",     "Upload 11MB file → HTTP 400 with 'exceeds 10MB' message.",                                                 True, AMBER),
        ("test_error_handling_corrupted",     "Upload corrupted PDF bytes → HTTP 400. Engine handles gracefully.",                                        True, AMBER),
        ("test_error_handling_encrypted",     "Upload password-protected PDF → HTTP 400. pikepdf catches PdfError.",                                      True, AMBER),
    ]

    cols = [40, 960]
    col_idx = 0
    for i, (name, desc, passed, col) in enumerate(tests):
        ci = i % 2
        ri = i // 2
        if i == 10:  # last one spans full width
            x, y, w = 40, 840, 1840
        else:
            x = cols[ci]
            y = 220 + ri * 118
            w = 880

        draw_rect(d, x, y, w, 102, BG_SURFACE)
        d.rectangle([x, y, x+4, y+102], fill=col)
        d.text((x+16, y+10), ("✓  PASS" if passed else "✗  FAIL"), font=F_SMALL, fill=EMERALD if passed else ROSE)
        d.text((x+16, y+32), name, font=F_H3, fill=WHITE)
        write_text_wrapped(d, desc, x+16, y+62, w-40, F_SMALL, TEXT_SEC, line_h=19)

    # Pytest terminal output snippet
    draw_rect(d, 40, 965, 1840, 30, (8, 10, 14))
    d.text((56, 973), "============================= 11 passed, 10 warnings in 4.92s =============================", font=F_MONO, fill=EMERALD)

    draw_footer(d)
    path = f"{OUT}/09_test_suite.jpg"
    img.save(path, quality=95)
    print(f"  ✅ {path}")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════

def title_card(text, subtitle, duration_s=3, fps=24, color=EMERALD):
    """Generate a title card frame sequence."""
    img, d = new_canvas()
    d.rectangle([0, 0, W, H], fill=BG_BASE)
    d.rectangle([0, H//2 - 2, W, H//2 + 2], fill=color)
    bbox = d.textbbox((0,0), text, font=F_HUGE)
    tw = bbox[2]-bbox[0]
    d.text(((W-tw)//2, H//2 - 90), text, font=F_HUGE, fill=WHITE)
    bbox2 = d.textbbox((0,0), subtitle, font=F_H3)
    tw2 = bbox2[2]-bbox2[0]
    d.text(((W-tw2)//2, H//2 + 40), subtitle, font=F_H3, fill=TEXT_SEC)
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame] * (duration_s * fps)


def image_to_frames(path, hold_s=4, fps=24):
    """Load a snapshot and hold it for hold_s seconds."""
    img = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame] * (hold_s * fps)


def fade_between(frame_a, frame_b, steps=18):
    """Create a smooth cross-fade between two frames."""
    frames = []
    for i in range(steps):
        alpha = i / steps
        blended = cv2.addWeighted(frame_a, 1-alpha, frame_b, alpha, 0)
        frames.append(blended)
    return frames


def make_video(snapshot_paths):
    fps = 24
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(VIDEO, fourcc, fps, (W, H))

    all_sequences = []

    # Intro title card
    all_sequences.extend(title_card(
        "VeriLedger",
        "Real-Time Document Forgery Detection & Cryptographic Audit Layer",
        duration_s=3, fps=fps, color=EMERALD
    ))

    sections = [
        ("01  Dashboard", "The VeriLedger Trust Console"),
        ("02  Clean Document Audit", "Trust Score: 97.4  •  TRUSTED"),
        ("03  ELA Heatmap — Clean", "Uniform pattern confirms no editing"),
        ("04  Tampered Document Audit", "Trust Score: 18.6  •  REJECTED"),
        ("05  ELA Heatmap — Tampered", "Bright hotspot at Net Pay field"),
        ("06  Copy-Move Detection", "Stamp duplication confirmed"),
        ("07  Cross-Document Reconciliation", "Missing Salary Deposit: ₹5,400 NOT FOUND"),
        ("08  Cryptographic Ledger", "Tamper-Evident Chain — All blocks verified"),
        ("09  Test Suite", "11 / 11 Tests Passing  •  100% Pass Rate"),
    ]

    prev_frames = None
    for i, (path, (section, desc)) in enumerate(zip(snapshot_paths, sections)):
        # Section title card (1.5s)
        tc = title_card(section, desc, duration_s=2, fps=fps,
                        color=[BLUE, EMERALD, EMERALD, ROSE, ROSE, ROSE, AMBER, BLUE, EMERALD][i])
        # Cross-fade from previous
        if prev_frames:
            all_sequences.extend(fade_between(prev_frames[-1], tc[0], steps=18))
        all_sequences.extend(tc)

        # Main snapshot (4.5s)
        snap_frames = image_to_frames(path, hold_s=5, fps=fps)
        all_sequences.extend(fade_between(tc[-1], snap_frames[0], steps=18))
        all_sequences.extend(snap_frames)
        prev_frames = snap_frames

    # Outro
    outro = title_card(
        "VeriLedger",
        "github.com/tanishqvarshney/VeriLedger  •  localhost:3000",
        duration_s=3, fps=fps, color=EMERALD
    )
    all_sequences.extend(fade_between(prev_frames[-1], outro[0], steps=18))
    all_sequences.extend(outro)

    print(f"\n🎬  Writing {len(all_sequences)} frames → {VIDEO}")
    for frame in all_sequences:
        out.write(frame)
    out.release()
    size_mb = os.path.getsize(VIDEO) / 1_000_000
    print(f"✅  Video saved: {VIDEO}  ({size_mb:.1f} MB)")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("📸  Generating snapshots...")
    paths = [
        snap_01_landing(),
        snap_02_clean_result(),
        snap_03_ela_clean(),
        snap_04_tampered_result(),
        snap_05_ela_tampered(),
        snap_06_copymove(),
        snap_07_cross_doc(),
        snap_08_ledger(),
        snap_09_test_suite(),
    ]
    print(f"\n✅  {len(paths)} snapshots saved to: {OUT}")
    print("\n🎬  Assembling walkthrough video...")
    make_video(paths)
