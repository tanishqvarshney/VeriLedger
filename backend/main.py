import os
import shutil
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import init_db, add_to_ledger, get_ledger, verify_ledger
from forensics import analyze_document

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "veriledger.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Ensure required directories exist at module load time
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="VeriLedger Forensic Backend")

# Enable CORS for React frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
def startup_event():
    init_db(DB_PATH)

# Serve static files for ELA and Copy-Move overlays
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_root():
    return {
        "status": "healthy",
        "service": "VeriLedger Forensic Backend",
        "endpoints": ["/analyze", "/ledger", "/ledger/verify", "/analyze-cross"]
    }

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    """
    Ingests an uploaded document, saves it temporarily, performs forensic audits,
    appends it to the tamper-evident ledger, and returns the results.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or image (PNG, JPG, JPEG).")
        
    # Check file size (limit 10MB) and empty files
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
        
    temp_file_path = os.path.join(UPLOADS_DIR, file.filename)
    
    try:
        # 1. Save uploaded file to temp path
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Read file bytes for ledger hashing
        with open(temp_file_path, "rb") as f:
            file_bytes = f.read()
            
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
            
        # 3. Perform forensic engine analysis
        analysis_result = analyze_document(temp_file_path, STATIC_DIR)
        
        # 4. Insert raw document hash into SQLite ledger
        ledger_entry = add_to_ledger(DB_PATH, file.filename, file_bytes)
        analysis_result["ledger_entry"] = ledger_entry
        
        return analysis_result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/ledger")
async def read_ledger():
    """
    Returns all entries stored in the tamper-evident ledger database.
    """
    try:
        return get_ledger(DB_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/ledger/verify")
async def audit_ledger():
    """
    Audits the database ledger and reports whether the chain is fully intact.
    """
    try:
        return verify_ledger(DB_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failure: {str(e)}")

# --- PHASE 2: CROSS-DOCUMENT RECONCILIATION ---

def extract_text_from_document(file_path: str) -> str:
    """
    Extracts text from PDF or Image using a hybrid approach:
    First tries direct vector text extraction (PyMuPDF). If empty, falls back to OCR (pytesseract).
    """
    is_pdf = file_path.lower().endswith(".pdf")
    text = ""
    
    if is_pdf:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        
    # If text is empty, it could be a scanned document or image. Fallback to OCR.
    if not text.strip():
        # Render PDF pages to images for OCR or load image directly
        try:
            if is_pdf:
                doc = fitz.open(file_path)
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(img) + "\n"
                doc.close()
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
        except (pytesseract.TesseractNotFoundError, FileNotFoundError):
            raise ValueError(
                "OCR engine (Tesseract) is not installed on the system. "
                "Please install Tesseract (e.g., 'brew install tesseract' on macOS) "
                "to reconcile scanned PDFs or image documents."
            )
        except Exception as e:
            print(f"OCR failed: {e}")
                
    return text

def parse_salary_slip_details(text: str) -> dict:
    """
    Parses Employee Name and Net Pay from the salary slip text.
    """
    details = {"name": None, "net_pay": None}
    
    # 1. Search for Employee Name
    # Match: "Employee Name: [Name]" or "Name: [Name]"
    name_match = re.search(r"(?:Employee\s+)?Name\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if name_match:
        details["name"] = name_match.group(1).strip()
    else:
        # Fallback search: look for "John Doe" or names in common format if name labels are missing
        pass
        
    # 2. Search for Net Pay
    # Match: "Net Pay [Amount]" or "Net Pay (A - B) [Amount]" or "Total Net [Amount]"
    # Followed by standard currency format (e.g. $5,400.00 or 5,400.00)
    net_pay_match = re.search(r"Net\s+Pay(?:\s*\(.*?\))?\s*[:\-]?\s*[\$]?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if net_pay_match:
        # Clean amount string
        details["net_pay"] = float(net_pay_match.group(1).replace(",", ""))
        
    return details

def check_bank_statement_details(text: str, salary_name: str, salary_net_pay: float) -> list[dict]:
    """
    Scans bank statement text to find name matches and deposits matching the net pay.
    """
    flags = []
    
    # 1. Name Reconciliation
    if salary_name:
        # Check if the employee's name appears anywhere in the bank statement
        # Convert both to lowercase and remove spaces for fuzzy comparison
        clean_salary_name = re.sub(r"\s+", "", salary_name.lower())
        clean_statement_text = re.sub(r"\s+", "", text.lower())
        
        if clean_salary_name not in clean_statement_text:
            flags.append({
                "flag": "Name Mismatch",
                "detail": f"Employee name '{salary_name}' was not found in the bank statement. This suggests the bank statement belongs to a different individual.",
                "severity": "HIGH"
            })
            
    # 2. Credit Deposit Reconciliation
    # Find all float values in the bank statement and check if any matches the salary net pay
    if salary_net_pay:
        # Find amounts in the format: e.g. 5,400.00 or 5400.00 or $5,400.00
        # Check if salary net pay exists in statement text
        target_amount_str_with_comma = f"{salary_net_pay:,.2f}"
        target_amount_str_no_comma = f"{salary_net_pay:.2f}"
        
        found = (target_amount_str_with_comma in text) or (target_amount_str_no_comma in text)
        
        if not found:
            flags.append({
                "flag": "Missing Salary Deposit",
                "detail": f"No deposit matching the Payslip Net Pay of ${salary_net_pay:,.2f} was detected in the bank statement transaction logs.",
                "severity": "HIGH"
            })
            
    return flags

@app.post("/analyze-cross")
async def analyze_cross_documents(
    salary_slip: UploadFile = File(...),
    bank_statement: UploadFile = File(...)
):
    """
    Phase 2: Compares two documents (Payslip + Bank Statement) for name mismatches and deposit reconciliations.
    """
    temp_sal_path = os.path.join(UPLOADS_DIR, f"sal_{salary_slip.filename}")
    temp_bank_path = os.path.join(UPLOADS_DIR, f"bank_{bank_statement.filename}")
    
    try:
        # Save files temporarily
        with open(temp_sal_path, "wb") as buffer:
            shutil.copyfileobj(salary_slip.file, buffer)
        with open(temp_bank_path, "wb") as buffer:
            shutil.copyfileobj(bank_statement.file, buffer)
            
        # Extract texts
        sal_text = extract_text_from_document(temp_sal_path)
        bank_text = extract_text_from_document(temp_bank_path)
        
        # Parse details
        sal_details = parse_salary_slip_details(sal_text)
        
        # Reconcile details
        reconciliation_flags = []
        
        if not sal_details["name"] and not sal_details["net_pay"]:
            reconciliation_flags.append({
                "flag": "Payslip Parsing Failure",
                "detail": "Failed to extract Employee Name or Net Pay from the payslip. Ensure the payslip is clear and standard.",
                "severity": "MEDIUM"
            })
        else:
            reconciliation_flags = check_bank_statement_details(
                bank_text,
                sal_details["name"],
                sal_details["net_pay"]
            )
            
        # Compute dynamic cross-doc trust score
        # Base score starts at 100, drops by 45 for each HIGH severity discrepancy, and 20 for MEDIUM
        cross_risk = 0
        for flag in reconciliation_flags:
            if flag["severity"] == "HIGH":
                cross_risk += 45
            elif flag["severity"] == "MEDIUM":
                cross_risk += 20
        cross_trust_score = max(0, 100 - cross_risk)
        
        return {
            "payslip_extracted": {
                "employee_name": sal_details["name"],
                "net_pay": sal_details["net_pay"]
            },
            "reconciliation_flags": reconciliation_flags,
            "cross_trust_score": cross_trust_score,
            "status": "success" if not reconciliation_flags else "warning"
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cross-document analysis failed: {str(e)}")
    finally:
        # Clean up files
        if os.path.exists(temp_sal_path):
            os.remove(temp_sal_path)
        if os.path.exists(temp_bank_path):
            os.remove(temp_bank_path)
