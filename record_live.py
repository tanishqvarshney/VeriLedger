"""
VeriLedger — Real Browser Screenshot & Video Recorder (Fixed v2)
Uses exact button text from App.jsx. Robust try/except on every interaction.
"""

import asyncio, os
from pathlib import Path
from playwright.async_api import async_playwright
import cv2, numpy as np

CLEAN_PDF   = "/Users/tanishqvarshney/Personal/VeriLedger/samples/clean_salary_slip.pdf"
TAMPERED    = "/Users/tanishqvarshney/Personal/VeriLedger/samples/tampered_salary_slip.pdf"
SNAP_DIR    = Path("/Users/tanishqvarshney/Personal/VeriLedger/real_snapshots")
VIDEO_OUT   = "/Users/tanishqvarshney/Personal/VeriLedger/VeriLedger_Live_Walkthrough.mp4"
SNAP_DIR.mkdir(exist_ok=True)
VIEWPORT    = {"width": 1920, "height": 1080}

shots = []

def snap_save(data, name, caption):
    p = SNAP_DIR / name
    p.write_bytes(data)
    shots.append((str(p), caption))
    print(f"  📸  {name}")

async def ss(page, name, caption, delay=1.2):
    await asyncio.sleep(delay)
    data = await page.screenshot(type="jpeg", quality=93, full_page=False)
    snap_save(data, name, caption)

async def click_btn(page, text, timeout=8000):
    """Click first visible button with matching text. Returns True if clicked."""
    try:
        btn = page.get_by_role("button", name=text).first
        await btn.wait_for(state="visible", timeout=timeout)
        await btn.scroll_into_view_if_needed()
        await btn.click()
        return True
    except Exception as e:
        print(f"  ⚠️  Could not click '{text}': {e}")
        return False

async def run():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-infobars"]
        )
        ctx = await browser.new_context(viewport=VIEWPORT)
        page = await ctx.new_page()

        # ── 1. LANDING PAGE ──────────────────────────────────────────────────
        print("\n── 1. LANDING ─────────────────────────────────────────────")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await asyncio.sleep(2.5)
        await ss(page, "01_landing.jpg", "Dashboard landing page", delay=0)

        # Scroll to reveal ledger section
        await page.mouse.wheel(0, 1200)
        await ss(page, "02_ledger_preview.jpg", "Scrolled — ledger timeline preview", delay=1.5)
        await page.mouse.wheel(0, -1200)
        await asyncio.sleep(0.5)

        # ── 2. CLEAN DOCUMENT ────────────────────────────────────────────────
        print("\n── 2. CLEAN DOCUMENT AUDIT ─────────────────────────────────")
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(CLEAN_PDF)
        await ss(page, "03_clean_uploading.jpg", "Clean PDF uploading — scanner active", delay=1.5)

        # Wait for Trust Score to appear
        print("  ⏳ Waiting for analysis…")
        try:
            await page.wait_for_selector("text=Trust Score", timeout=20000)
        except:
            pass
        await asyncio.sleep(2.5)
        await ss(page, "04_clean_result.jpg", "Clean document — Trust Score high, green ring", delay=0)

        # Scroll into workspace
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(0.5)

        # ELA Split
        await click_btn(page, "ELA Split")
        await ss(page, "05_clean_ela.jpg", "ELA Split — clean, uniform dark heatmap", delay=1.5)

        # Clone Split
        await click_btn(page, "Clone Split")
        await ss(page, "06_clean_clone.jpg", "Clone Split — no copy-move detected on clean", delay=1.5)

        # Scroll to metadata section
        await page.mouse.wheel(0, 600)
        await ss(page, "07_clean_metadata.jpg", "Metadata & diagnostic console — all clear", delay=1.2)

        # ── 3. TAMPERED DOCUMENT ─────────────────────────────────────────────
        print("\n── 3. TAMPERED DOCUMENT AUDIT ──────────────────────────────")
        await page.mouse.wheel(0, -1500)
        await asyncio.sleep(0.6)

        # Switch back to Original view first
        await click_btn(page, "Original")
        await asyncio.sleep(0.5)

        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(TAMPERED)
        await ss(page, "08_tampered_uploading.jpg", "Tampered PDF uploading — forensic scan running", delay=1.5)

        print("  ⏳ Waiting for analysis…")
        try:
            await page.wait_for_selector("text=Trust Score", timeout=20000)
        except:
            pass
        await asyncio.sleep(2.5)
        await ss(page, "09_tampered_result.jpg", "REJECTED — low trust score, red ring, forgery detected", delay=0)

        # Scroll to workspace
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(0.5)

        # ELA Split — should show bright hotspot
        await click_btn(page, "ELA Split")
        await ss(page, "10_tampered_ela.jpg", "ELA Heatmap — bright hotspot at tampered Net Pay field", delay=1.5)

        # Clone Split — should show keypoint match lines
        await click_btn(page, "Clone Split")
        await ss(page, "11_tampered_clone.jpg", "Clone Split — blue keypoint lines on stamp duplicates", delay=1.5)

        # Scroll to metadata
        await page.mouse.wheel(0, 600)
        await ss(page, "12_tampered_metadata.jpg", "Metadata — iLovePDF, Photoshop, ModDate delta flagged", delay=1.2)

        # ── 4. CROSS-DOCUMENT RECONCILIATION ─────────────────────────────────
        print("\n── 4. CROSS-DOC RECONCILIATION ─────────────────────────────")
        await page.mouse.wheel(0, -2000)
        await asyncio.sleep(0.5)

        # Click "Cross-Doc Reconciliation" tab
        await click_btn(page, "Cross-Doc Reconciliation")
        await asyncio.sleep(1)
        await ss(page, "13_cross_doc_tab.jpg", "Cross-Document tab — dual upload interface", delay=0)

        # Upload both files
        all_inputs = page.locator('input[type="file"]')
        count = await all_inputs.count()
        print(f"  Found {count} file inputs")
        if count >= 2:
            await all_inputs.nth(0).set_input_files(CLEAN_PDF)
            await asyncio.sleep(0.4)
            await all_inputs.nth(1).set_input_files(TAMPERED)
        else:
            # Try setting both on first input
            await all_inputs.nth(0).set_input_files(CLEAN_PDF)
        await ss(page, "14_cross_files_selected.jpg", "Both documents selected — payslip + bank statement", delay=1.0)

        # Click Reconcile Fields
        await click_btn(page, "Reconcile Fields")
        await ss(page, "15_cross_reconciling.jpg", "Reconciliation running — OCR in progress", delay=1.5)

        print("  ⏳ Waiting for cross-doc result…")
        try:
            await page.wait_for_selector("text=Match Score", timeout=25000)
        except:
            await asyncio.sleep(8)
        await asyncio.sleep(2)
        await ss(page, "16_cross_result.jpg", "Reconciliation result — missing deposit flagged", delay=0)

        # Scroll to see link map
        await page.mouse.wheel(0, 400)
        await ss(page, "17_cross_link_map.jpg", "Reconciliation link map — connecting payslip to bank", delay=1.2)

        # ── 5. LEDGER INTEGRITY ───────────────────────────────────────────────
        print("\n── 5. LEDGER INTEGRITY ─────────────────────────────────────")
        await page.mouse.wheel(0, 2000)
        await asyncio.sleep(1)
        await ss(page, "18_ledger_timeline.jpg", "Ledger timeline — SHA-256 block chain", delay=0)

        # Click Audit Chain Integrity
        await click_btn(page, "Audit Chain Integrity")
        await asyncio.sleep(3.5)
        await ss(page, "19_ledger_intact.jpg", "Ledger audit — INTACT, green verification banner", delay=0)

        # Click a block card to open inspector
        try:
            block = page.locator("text=Block #").first
            await block.scroll_into_view_if_needed()
            await block.click()
            await asyncio.sleep(1)
            await ss(page, "20_block_inspector.jpg", "Block inspector modal — hash details and chain link", delay=0)
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Block inspector: {e}")

        # ── 6. FINAL WIDE OVERVIEW ────────────────────────────────────────────
        print("\n── 6. FINAL OVERVIEW ───────────────────────────────────────")
        await page.mouse.wheel(0, -3000)
        await asyncio.sleep(1)
        # Switch to single tab to show results
        await click_btn(page, "Single Document Audit")
        await asyncio.sleep(1)
        await ss(page, "21_final_overview.jpg", "Final overview — full forensic console", delay=0)

        await browser.close()

    print(f"\n✅  Captured {len(shots)} real screenshots → {SNAP_DIR}")
    return shots


# ── Video Assembly ─────────────────────────────────────────────────────────────
def make_video(shot_list):
    W, H = 1920, 1080
    fps  = 24
    vw   = cv2.VideoWriter(VIDEO_OUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    EMERALD_BGR = (48, 209, 88)  # BGR for cv2
    SLATE_BGR   = (16, 13, 11)

    captions = {
        "01_": "VeriLedger Dashboard",
        "02_": "Ledger Timeline Preview",
        "03_": "Clean Document — Uploading",
        "04_": "Clean Document — TRUSTED ✓",
        "05_": "ELA Heatmap — Clean",
        "06_": "Clone Detection — Clean",
        "07_": "Metadata — All Clear",
        "08_": "Tampered Document — Uploading",
        "09_": "Tampered Document — REJECTED ✗",
        "10_": "ELA Heatmap — Hotspot Detected",
        "11_": "Clone Detection — Stamp Duplication",
        "12_": "Metadata — 3 Flags Found",
        "13_": "Cross-Document Tab",
        "14_": "Both Documents Selected",
        "15_": "Reconciliation Running…",
        "16_": "Reconciliation — Missing Deposit",
        "17_": "Link Map — Discrepancy Visual",
        "18_": "Ledger — Block Timeline",
        "19_": "Ledger Integrity — INTACT",
        "20_": "Block Inspector Modal",
        "21_": "Final Dashboard Overview",
    }

    def title_card(text, sub=""):
        f = np.full((H, W, 3), SLATE_BGR, dtype=np.uint8)
        cv2.line(f, (0, H//2-2), (W, H//2-2), EMERALD_BGR, 3)
        cv2.putText(f, text, (80, H//2-30), cv2.FONT_HERSHEY_DUPLEX, 1.8, (245,245,247), 2)
        cv2.putText(f, sub,  (80, H//2+55), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (100,100,110), 1)
        return f

    def load_frame(path):
        img = cv2.imread(path)
        if img is None:
            return np.full((H, W, 3), SLATE_BGR, dtype=np.uint8)
        return cv2.resize(img, (W, H))

    def fade(a, b, n=20):
        for i in range(n):
            yield cv2.addWeighted(a, 1 - i/n, b, i/n, 0)

    def hold(frm, secs):
        for _ in range(secs * fps): yield frm

    # Intro
    intro = title_card("VeriLedger", "Real-Time Document Forgery Detection  •  Live Demo")
    for f in hold(intro, 3): vw.write(f)

    prev = intro
    for path, caption in shot_list:
        name   = Path(path).name
        prefix = name[:3]
        title  = next((v for k,v in captions.items() if name.startswith(k)), caption[:55])

        tc = title_card(title)
        for f in fade(prev, tc, 20): vw.write(f)
        for f in hold(tc, 2): vw.write(f)

        snap = load_frame(path)
        for f in fade(tc, snap, 20): vw.write(f)
        for f in hold(snap, 5): vw.write(f)
        prev = snap

    outro = title_card("VeriLedger", "github.com/tanishqvarshney/VeriLedger")
    for f in fade(prev, outro, 20): vw.write(f)
    for f in hold(outro, 3): vw.write(f)

    vw.release()
    mb = os.path.getsize(VIDEO_OUT) / 1e6
    print(f"🎬  Video: {VIDEO_OUT}  ({mb:.1f} MB, {len(shot_list)} scenes)")


if __name__ == "__main__":
    result = asyncio.run(run())
    if result:
        print("\n🎬  Compiling video…")
        make_video(result)
        print("\n🏁  All done!")
    else:
        print("❌  No screenshots captured — check errors above")
