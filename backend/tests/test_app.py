import os
import shutil
import sqlite3
import hashlib
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np
import pikepdf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Set up path to import main app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, DB_PATH, STATIC_DIR, UPLOADS_DIR

client = TestClient(app)

# Test Artifacts path
TEST_ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'test_artifacts'))
os.makedirs(TEST_ARTIFACTS_DIR, exist_ok=True)

SAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'samples'))
CLEAN_PDF = os.path.join(SAMPLES_DIR, "clean_salary_slip.pdf")
TAMPERED_PDF = os.path.join(SAMPLES_DIR, "tampered_salary_slip.pdf")

def generate_dummy_bank_statement(filename, name, credit_text):
    """
    Helper to generate a dummy PDF bank statement containing specific text
    for testing cross-document OCR reconciliation.
    """
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>BANK STATEMENT</b>", styles["Heading1"]),
        Paragraph(f"Account Holder: {name}", styles["Normal"]),
        Paragraph(f"Statement Period: May 2026", styles["Normal"]),
        Paragraph(f"Transactions:", styles["Heading3"]),
        Paragraph(f"May 29, 2026: Direct Deposit Employer Credit - {credit_text}", styles["Normal"]),
    ]
    doc.build(story)

@pytest.fixture(autouse=True)
def run_around_tests():
    """
    Saves and restores the veriledger database and directories to ensure isolation.
    """
    db_backup = DB_PATH + ".bak"
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, db_backup)
    else:
        db_backup = None
        
    # Ensure database table is created for tests
    from database import init_db
    init_db(DB_PATH)
        
    yield
    
    # Restore DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if db_backup and os.path.exists(db_backup):
        shutil.move(db_backup, DB_PATH)

# --- 1. FORENSIC DISCRIMINATION TESTS ---

def test_forensic_discrimination_and_ela_localization():
    """
    Asserts that the clean PDF scores high, the tampered PDF scores low,
    and ELA highlights are spatially focused near the edited text boundaries.
    """
    # 1. Ingest clean file
    with open(CLEAN_PDF, "rb") as f:
        clean_res = client.post("/analyze", files={"file": ("clean_salary_slip.pdf", f, "application/pdf")})
    assert clean_res.status_code == 200
    clean_data = clean_res.json()
    
    # 2. Ingest tampered file
    with open(TAMPERED_PDF, "rb") as f:
        tampered_res = client.post("/analyze", files={"file": ("tampered_salary_slip.pdf", f, "application/pdf")})
    assert tampered_res.status_code == 200
    tampered_data = tampered_res.json()
    
    # Assert Trust Score Discrimination
    assert clean_data["trust_score"] > tampered_data["trust_score"]
    assert clean_data["trust_score"] >= 80.0
    assert tampered_data["trust_score"] < 50.0
    
    # Assert ELA Risk Discrimination
    clean_ela_risk = clean_data["signals"]["ela"]["risk"]
    tampered_ela_risk = tampered_data["signals"]["ela"]["risk"]
    assert tampered_ela_risk > clean_ela_risk
    
    # 3. Verify ELA Spatial Localization
    # The ELA overlay image path (relative to backend dir)
    ela_overlay_url = tampered_data["signals"]["ela"]["overlay_url"]
    ela_img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', ela_overlay_url.lstrip('/')))
    
    # Load ELA image using PIL and convert to numpy array
    assert os.path.exists(ela_img_path)
    ela_img = Image.open(ela_img_path).convert("L")
    ela_arr = np.array(ela_img)
    
    # Coordinates of edited values at 150 DPI (Rendered image size is 1275x1650):
    # - Basic Salary box: x=415 to 520, y=480 to 520
    # - Net Pay box: x=700 to 950, y=840 to 895
    # Let's crop these regions and check the mean pixel intensity.
    basic_salary_crop = ela_arr[480:520, 415:520]
    net_pay_crop = ela_arr[840:895, 700:950]
    
    # Untampered background regions (e.g. margins or empty center columns)
    # - Margin left crop: x=100 to 300, y=1000 to 1200
    background_crop = ela_arr[1000:1200, 100:300]
    
    mean_basic_salary_ela = np.mean(basic_salary_crop)
    mean_net_pay_ela = np.mean(net_pay_crop)
    mean_background_ela = np.mean(background_crop)
    
    print(f"\n[ELA Spatial Validation] Basic Salary Mean ELA: {mean_basic_salary_ela:.2f}")
    print(f"[ELA Spatial Validation] Net Pay Mean ELA: {mean_net_pay_ela:.2f}")
    print(f"[ELA Spatial Validation] Background Mean ELA: {mean_background_ela:.2f}")
    
    # Assert ELA intensity in edited bounding boxes is significantly higher than uniform background
    assert mean_basic_salary_ela > mean_background_ela * 2.0
    assert mean_net_pay_ela > mean_background_ela * 2.0
    
    # 4. Save test heatmaps to test_artifacts for visual inspection
    shutil.copy(ela_img_path, os.path.join(TEST_ARTIFACTS_DIR, "tampered_ela_heatmap.jpg"))
    
    clean_ela_url = clean_data["signals"]["ela"]["overlay_url"]
    clean_ela_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', clean_ela_url.lstrip('/')))
    shutil.copy(clean_ela_path, os.path.join(TEST_ARTIFACTS_DIR, "clean_ela_heatmap.jpg"))

def test_copy_move_discrimination():
    """
    Asserts copy-move features are triggered in tampered slip (duplicate stamp)
    but remain clean in the text-dense clean salary slip.
    """
    # 1. Tampered slip copy-move check
    with open(TAMPERED_PDF, "rb") as f:
        tam_res = client.post("/analyze", files={"file": ("tampered_salary_slip.pdf", f, "application/pdf")})
    tam_data = tam_res.json()
    tam_copy_move_risk = tam_data["signals"]["copy_move"]["risk"]
    
    # The stamp was duplicated so copy-move risk should be triggered
    assert tam_copy_move_risk > 0.0
    
    # Copy generated Copy-Move image overlay for visual inspection
    copymove_url = tam_data["signals"]["copy_move"]["overlay_url"]
    copymove_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', copymove_url.lstrip('/')))
    shutil.copy(copymove_path, os.path.join(TEST_ARTIFACTS_DIR, "tampered_copymove_matches.jpg"))
    
    # 2. Clean slip copy-move check (repeated glyphs must not trigger clone matches)
    with open(CLEAN_PDF, "rb") as f:
        clean_res = client.post("/analyze", files={"file": ("clean_salary_slip.pdf", f, "application/pdf")})
    clean_data = clean_res.json()
    clean_copy_move_risk = clean_data["signals"]["copy_move"]["risk"]
    
    # Strict check: repeated text like 'e', '0', etc., must NOT trigger false clone matches
    assert clean_copy_move_risk == 0.0

def test_metadata_audit_discrimination():
    """
    Asserts metadata flags identify suspicious editors and modified dates on the
    tampered PDF while returning zero flags on the clean PDF.
    """
    # 1. Clean PDF: untouched original generated directly
    with open(CLEAN_PDF, "rb") as f:
        clean_res = client.post("/analyze", files={"file": ("clean_salary_slip.pdf", f, "application/pdf")})
    clean_meta = clean_res.json()["signals"]["metadata"]
    assert clean_meta["risk"] == 0.0
    assert len(clean_meta["flags"]) == 0
    
    # 2. Tampered PDF: Modified using Pillow and given Photoshop/iLovePDF metadata tags
    with open(TAMPERED_PDF, "rb") as f:
        tam_res = client.post("/analyze", files={"file": ("tampered_salary_slip.pdf", f, "application/pdf")})
    tam_meta = tam_res.json()["signals"]["metadata"]
    
    assert tam_meta["risk"] > 0.0
    flags = [f["flag"] for f in tam_meta["flags"]]
    assert "Suspicious Editor Metadata" in flags
    assert "Modified Date Delay" in flags

# --- 2. TRUST SCORE FUSION TESTS ---

def test_trust_score_fusion_math():
    """
    Validates weight distribution (35% ELA, 35% Copy-Move, 30% Metadata),
    fused risk subtraction, monotonicity, per-signal reconciliation, and determinism.
    """
    # 1. Reconcile score components math on the tampered sample
    with open(TAMPERED_PDF, "rb") as f:
        res = client.post("/analyze", files={"file": ("tampered_salary_slip.pdf", f, "application/pdf")})
    data = res.json()
    
    score = data["trust_score"]
    ela_risk = data["signals"]["ela"]["risk"]
    copymove_risk = data["signals"]["copy_move"]["risk"]
    meta_risk = data["signals"]["metadata"]["risk"]
    
    # Weighted fusion calculation
    fused_risk = (0.35 * ela_risk) + (0.35 * copymove_risk) + (0.30 * meta_risk)
    expected_score = round(max(0.0, 100.0 - fused_risk), 1)
    
    # Assert strict mathematical equality
    assert score == expected_score
    
    # 2. Assert Score Determinism (no score wobble across multiple runs)
    for _ in range(3):
        with open(TAMPERED_PDF, "rb") as f:
            r = client.post("/analyze", files={"file": ("tampered_salary_slip.pdf", f, "application/pdf")})
        assert r.json()["trust_score"] == score

# --- 3. TAMPER-EVIDENT LEDGER TESTS ---

def test_tamper_evident_ledger_verify_and_breach_detection():
    """
    Ingests files to construct a ledger hash chain, asserts that the ledger verify reports
    the chain is intact, then directly mutates a DB row and asserts the breach is caught.
    """
    # 1. Ingest 3 documents to create a chain
    with open(CLEAN_PDF, "rb") as f:
        client.post("/analyze", files={"file": ("clean_1.pdf", f, "application/pdf")})
    with open(TAMPERED_PDF, "rb") as f:
        client.post("/analyze", files={"file": ("tampered_2.pdf", f, "application/pdf")})
    with open(CLEAN_PDF, "rb") as f:
        client.post("/analyze", files={"file": ("clean_3.pdf", f, "application/pdf")})
        
    # Verify chain is intact initially
    ledger_verify_res = client.get("/ledger/verify")
    assert ledger_verify_res.status_code == 200
    assert ledger_verify_res.json()["intact"] is True
    assert len(ledger_verify_res.json()["tampered_ids"]) == 0
    
    # Fetch ledger blocks and assert links
    ledger_res = client.get("/ledger")
    blocks = ledger_res.json()
    assert len(blocks) >= 3
    
    # Validate mathematical hash linking: chain_hash = SHA-256(doc_hash + prev_row_hash)
    for idx in range(1, len(blocks)):
        prev_block = blocks[idx - 1]
        curr_block = blocks[idx]
        
        assert curr_block["prev_row_hash"] == prev_block["chain_hash"]
        
        hasher = hashlib.sha256()
        hasher.update((curr_block["doc_hash"] + curr_block["prev_row_hash"]).encode('utf-8'))
        expected_chain_hash = hasher.hexdigest()
        assert curr_block["chain_hash"] == expected_chain_hash

    # 2. Direct database mutation (simulate hacking modification)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Mutate the doc_hash of block #2
    tampered_row_id = blocks[1]["id"]
    cursor.execute("UPDATE ledger SET doc_hash = ? WHERE id = ?", ("a" * 64, tampered_row_id))
    conn.commit()
    conn.close()
    
    # 3. Call ledger/verify to confirm breach detection
    verify_breached_res = client.get("/ledger/verify")
    assert verify_breached_res.status_code == 200
    
    verify_data = verify_breached_res.json()
    assert verify_data["intact"] is False
    # Verify the auditor successfully flags the row we mutated
    assert tampered_row_id in verify_data["tampered_ids"]

# --- 4. CROSS-DOCUMENT CHECK TESTS (Phase 2) ---

def test_cross_document_reconciliation():
    """
    Tests Phase 2 text extraction and reconciliation checking:
    Asserts consistent values pass, and name/amount mismatches fire alerts.
    """
    # Define temp filenames
    dummy_bank_consistent = os.path.join(SAMPLES_DIR, "dummy_bank_consistent.pdf")
    dummy_bank_mismatch_name = os.path.join(SAMPLES_DIR, "dummy_bank_mismatch_name.pdf")
    dummy_bank_mismatch_amount = os.path.join(SAMPLES_DIR, "dummy_bank_mismatch_amount.pdf")
    
    try:
        # 1. Consistent Pair
        # clean_salary_slip.pdf contains employee "John Doe" and Net Pay "$5,400.00" (reconciles to 5400.00)
        generate_dummy_bank_statement(dummy_bank_consistent, "John Doe", "$5,400.00")
        
        with open(CLEAN_PDF, "rb") as payslip, open(dummy_bank_consistent, "rb") as bank:
            res_consistent = client.post(
                "/analyze-cross",
                files={
                    "salary_slip": ("clean_salary_slip.pdf", payslip, "application/pdf"),
                    "bank_statement": ("dummy_bank_consistent.pdf", bank, "application/pdf")
                }
            )
        assert res_consistent.status_code == 200
        data_consistent = res_consistent.json()
        
        # Verify no flags raised and score is 100%
        assert data_consistent["cross_trust_score"] == 100
        assert len(data_consistent["reconciliation_flags"]) == 0
        
        # 2. Name Mismatch Pair
        generate_dummy_bank_statement(dummy_bank_mismatch_name, "Jane Smith", "$5,400.00")
        
        with open(CLEAN_PDF, "rb") as payslip, open(dummy_bank_mismatch_name, "rb") as bank:
            res_mismatch_name = client.post(
                "/analyze-cross",
                files={
                    "salary_slip": ("clean_salary_slip.pdf", payslip, "application/pdf"),
                    "bank_statement": ("dummy_bank_mismatch_name.pdf", bank, "application/pdf")
                }
            )
        assert res_mismatch_name.status_code == 200
        data_mismatch_name = res_mismatch_name.json()
        
        # Verify Name Mismatch flag fires and match score decreases
        assert data_mismatch_name["cross_trust_score"] < 100
        flags = [f["flag"] for f in data_mismatch_name["reconciliation_flags"]]
        assert "Name Mismatch" in flags

        # 3. Credit Deposit Mismatch Pair
        generate_dummy_bank_statement(dummy_bank_mismatch_amount, "John Doe", "$1,200.00")
        
        with open(CLEAN_PDF, "rb") as payslip, open(dummy_bank_mismatch_amount, "rb") as bank:
            res_mismatch_amount = client.post(
                "/analyze-cross",
                files={
                    "salary_slip": ("clean_salary_slip.pdf", payslip, "application/pdf"),
                    "bank_statement": ("dummy_bank_mismatch_amount.pdf", bank, "application/pdf")
                }
            )
        assert res_mismatch_amount.status_code == 200
        data_mismatch_amount = res_mismatch_amount.json()
        
        # Verify Missing Salary Deposit flag fires
        assert data_mismatch_amount["cross_trust_score"] < 100
        flags = [f["flag"] for f in data_mismatch_amount["reconciliation_flags"]]
        assert "Missing Salary Deposit" in flags

    finally:
        # Clean up temp statements
        for fpath in [dummy_bank_consistent, dummy_bank_mismatch_name, dummy_bank_mismatch_amount]:
            if os.path.exists(fpath):
                os.remove(fpath)

# --- 5. ERROR HANDLING / EDGE CASES ---

def test_error_handling_invalid_file_types():
    """
    Asserts uploading non-PDF/non-images yields clear HTTP 400 errors.
    """
    dummy_text_path = os.path.join(SAMPLES_DIR, "temp_test.txt")
    with open(dummy_text_path, "w") as f:
        f.write("This is a simple text file, not a PDF or image.")
        
    try:
        with open(dummy_text_path, "rb") as f:
            res = client.post("/analyze", files={"file": ("temp_test.txt", f, "text/plain")})
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]
    finally:
        if os.path.exists(dummy_text_path):
            os.remove(dummy_text_path)

def test_error_handling_empty_files():
    """
    Asserts uploading an empty file yields an HTTP 400.
    """
    empty_file_path = os.path.join(SAMPLES_DIR, "empty.pdf")
    with open(empty_file_path, "wb") as f:
        pass
        
    try:
        with open(empty_file_path, "rb") as f:
            res = client.post("/analyze", files={"file": ("empty.pdf", f, "application/pdf")})
        assert res.status_code == 400
        assert "empty" in res.json()["detail"].lower()
    finally:
        if os.path.exists(empty_file_path):
            os.remove(empty_file_path)

def test_error_handling_oversized_files():
    """
    Asserts uploading a file exceeding 10MB yields an HTTP 400.
    """
    oversized_file_path = os.path.join(SAMPLES_DIR, "oversized.pdf")
    # Write 11MB of dummy bytes
    with open(oversized_file_path, "wb") as f:
        f.write(b"\0" * (11 * 1024 * 1024))
        
    try:
        with open(oversized_file_path, "rb") as f:
            res = client.post("/analyze", files={"file": ("oversized.pdf", f, "application/pdf")})
        assert res.status_code == 400
        assert "size exceeds" in res.json()["detail"].lower()
    finally:
        if os.path.exists(oversized_file_path):
            os.remove(oversized_file_path)

def test_error_handling_corrupted_files():
    """
    Asserts uploading corrupted bytes starts with PDF marker yields an HTTP 400.
    """
    corrupted_path = os.path.join(SAMPLES_DIR, "corrupted.pdf")
    with open(corrupted_path, "wb") as f:
        f.write(b"%PDF-1.4\nJUNK_BYTES_THAT_ARE_NOT_VALID_STRUCTURE_DATA_AT_ALL_XXXX")
        
    try:
        with open(corrupted_path, "rb") as f:
            res = client.post("/analyze", files={"file": ("corrupted.pdf", f, "application/pdf")})
        assert res.status_code == 400
        assert "corrupted" in res.json()["detail"].lower()
    finally:
        if os.path.exists(corrupted_path):
            os.remove(corrupted_path)

def test_error_handling_encrypted_pdfs():
    """
    Asserts uploading password-protected PDFs yields an HTTP 400.
    """
    encrypted_path = os.path.join(SAMPLES_DIR, "encrypted.pdf")
    
    # Open clean slip and save with password encryption
    pdf = pikepdf.open(CLEAN_PDF)
    pdf.save(encrypted_path, encryption=pikepdf.Encryption(owner="owner_pass", user="user_pass"))
    pdf.close()
    
    try:
        with open(encrypted_path, "rb") as f:
            res = client.post("/analyze", files={"file": ("encrypted.pdf", f, "application/pdf")})
        assert res.status_code == 400
        assert "password-protected" in res.json()["detail"].lower()
    finally:
        if os.path.exists(encrypted_path):
            os.remove(encrypted_path)

def test_ledger_download():
    """
    Asserts that downloading the SQLite ledger database returns a 200 OK
    and serves the database binary file correctly.
    """
    response = client.get("/ledger/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-sqlite3"
    assert len(response.content) > 0
