# VeriLedger

VeriLedger is a working prototype of a real-time document forgery and tampering detection system designed for bank loan underwriting. 

It provides an automated forensic layer that runs image and structural checks on uploaded financial documents (like payslips and bank statements), generates heatmaps/overlays for visual inspections, registers files in a cryptographically chained tamper-evident ledger, and provides cross-document OCR reconciliation.

---

## 🚀 Live Demo & Presentation Assets

* **Live Demo (GitHub Pages)**: **[https://tanishqvarshney.github.io/VeriLedger/](https://tanishqvarshney.github.io/VeriLedger/)**
  > [!NOTE]
  > The GitHub Pages live site operates in a **hybrid client-side fallback mode**. If the backend server is unreachable, you can still fully test the document forensic engine, slider workspaces, and OCR reconciliation by uploading the pre-generated sample files (`clean_salary_slip.pdf` and `tampered_salary_slip.pdf`). Custom file audits require running the FastAPI backend locally or via Docker.
* **Recorded Live Walkthrough Video**: [VeriLedger_Live_Walkthrough.mp4](VeriLedger_Live_Walkthrough.mp4) (50.1 MB browser walkthrough showing all tabs, ELA compression heatmaps, ORB clone matching, cross-doc reconciliation, and database chain audit)
* **PowerPoint Pitch Deck**: [VeriLedger_Pitch_Deck.pptx](VeriLedger_Pitch_Deck.pptx) (11-slide presentation explaining prototype architecture, forensic math, database integrity, and fraud business cases)
* **Interactive Snapshots Index**: See the step-by-step screenshots in the [real_snapshots/](real_snapshots/) and [snapshots/](snapshots/) folders.

---

## Features & Forensic Checks

1. **Error Level Analysis (ELA)**: Rasterizes PDF pages, resaves them as JPEG at 90% quality, and computes the absolute pixel difference. Localized image splices, painted shapes, or edited text fields leave a high-contrast grid mismatch (glowing bright spots) on the ELA heatmap.
2. **Copy-Move Clone Detection**: Uses OpenCV's ORB keypoint detector to match visually identical regions (like duplicated signatures, stamps, or numeric digits) within the same page. Applies translation vector clustering to prevent false positives from repeating text letters.
3. **Metadata & Structure Audit**: Scans PDF headers for editing signatures (e.g., iLovePDF, Adobe Photoshop, etc.), checks for time delays between `/CreationDate` and `/ModDate`, counts incremental save revisions, and flags unembedded or non-subsetted system fonts.
4. **Tamper-Evident Ledger**: Registers every file ingestion with a SHA-256 hash in a SQLite database. Blocks are chained together using `chain_hash = SHA-256(doc_hash + prev_row_hash)`. The system provides an audit API to verify chain integrity.
5. **Cross-Document Reconciliation**: Uses a hybrid vector text extractor with Tesseract OCR fallback to parse Employee Name and Net Pay from a payslip, verifying that they reconcile with the names and deposit transaction logs in a bank statement.

---

## Directory Structure

```
VeriLedger/
├── backend/
│   ├── main.py              # FastAPI app & endpoint routing
│   ├── database.py          # SQLite ledger operations & hash chain audit
│   ├── forensics.py         # ELA, Copy-Move, and Metadata audit math
│   ├── requirements.txt     # Python backend dependencies
│   ├── Dockerfile           # Backend container (installs OpenCV, Tesseract, PyMuPDF)
│   ├── static/              # Stores generated forensic overlays
│   └── uploads/             # Temp directory for processing uploads
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx          # React SPA Dashboard (Tailwind CSS v4)
│   │   └── index.css        # Base Tailwind styling & dark-theme configurations
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile           # Frontend container (Vite dev server)
│   └── index.html
├── samples/
│   ├── generate_samples.py  # Script to generate clean & tampered payslips
│   ├── clean_salary_slip.pdf
│   └── tampered_salary_slip.pdf
├── docker-compose.yml       # Orchestrates frontend & backend containers
└── README.md                # Quickstart instructions
```

---

## Quickstart (Docker Compose)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Running the Application

To build and launch the backend and frontend services, run:

```bash
docker-compose up --build
```

Once running:
- **Frontend Dashboard**: Access at [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend Swagger Docs (Local)**: Access at [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI Backend Swagger Docs (Production)**: Access at [https://veriledger.onrender.com/docs](https://veriledger.onrender.com/docs)

---

## Testing the Prototype (Demo Guide)

The project includes pre-generated sample PDFs in the `samples/` folder. Use them to test both the forensic engine and the cross-document reconciliation features.

### Test 1: Single Document Forensic Audit
1. Open [http://localhost:3000](http://localhost:3000) and select the **Document Forensic Auditor** tab.
2. Drag and drop `samples/clean_salary_slip.pdf`:
   - **Expectation**: Trust Score will be high ($\ge 90$). ELA and Copy-Move overlays will be clean. No metadata alerts.
3. Drag and drop `samples/tampered_salary_slip.pdf`:
   - **Expectation**: Trust Score will drop dramatically ($< 40$).
   - Toggle to **ELA Heatmap** in the inspector to see the modified Basic Salary (`$15,000.00` instead of `$5,000.00`) and Net Pay (`$15,400.00` instead of `$5,400.00`) glow bright white.
   - Toggle to **Copy-Move Overlay** to see blue lines linking the copied signature stamp from the bottom right to the top right of the page.
   - Review the **Metadata Logs** table showing flags for the `iLovePDF` editing signature, the `Adobe Photoshop` producer string, and the long modifications date delay.
4. Scroll to the **Tamper-Evident Ledger** section at the bottom. You will see blocks for both files appended.
5. Click **Audit Chain Integrity**. The banner will glow green: **"Ledger Audit: Chained Verification Intact"**.

### Test 2: Cross-Document Reconciliation (Phase 2)
1. In the dashboard, click the **Cross-Document Reconciliation** tab.
2. Under **Salary Payslip**, upload `samples/clean_salary_slip.pdf` (this file has Name: *John Doe*, Net Pay: *5,400.00*).
3. Under **Bank Statement**, upload `samples/tampered_salary_slip.pdf` (representing a client who tampered with their bank records to inflate Net Pay to *15,400.00*).
4. Click **Execute Reconciliation**:
   - **Expectation**: The system will extract the declared payslip values and report a **"Missing Salary Deposit"** discrepancy, indicating that the payslip Net Pay of `$5,400.00` was not found in the statement records (which now show `$15,400.00`).
   - The match score will decrease, and a warning status will be triggered.

---

## Local Development (Optional)

If you wish to run the components locally without Docker:

### Running the Backend
1. Create a virtual environment and activate it:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```

### Running the Frontend
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser to the URL displayed in the terminal (usually `http://localhost:3000`).
