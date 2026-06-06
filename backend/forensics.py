import os
import re
import datetime
import fitz  # PyMuPDF
import pikepdf
import cv2
import numpy as np
from PIL import Image, ImageChops

def parse_pdf_date(date_str):
    """
    Parses PDF date formats like D:20260606195727+05'30' or D:20260606195727Z.
    Returns datetime object or None if parsing fails.
    """
    if not date_str:
        return None
    if date_str.startswith("D:"):
        date_str = date_str[2:]
    
    # Extract year, month, day, hour, minute, second
    match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", date_str)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc)
        except ValueError:
            pass
            
    # Try simpler YYYYMMDD
    match = re.match(r"^(\d{4})(\d{2})(\d{2})", date_str)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime.datetime(year, month, day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        except ValueError:
            pass
            
    return None

def run_ela(pil_img: Image.Image, output_path: str) -> float:
    """
    Error Level Analysis (ELA). Saves image at 90% quality, computes absolute difference,
    amplifies it by 20x, saves the heatmap, and computes a risk score.
    """
    original = pil_img.convert("RGB")
    
    # Save as JPEG quality 90 to temporary file
    temp_path = output_path + ".temp.jpg"
    original.save(temp_path, "JPEG", quality=90)
    
    # Re-open the compressed image
    resaved = Image.open(temp_path)
    
    # Compute absolute difference
    diff = ImageChops.difference(original, resaved)
    
    # Clean up temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    # Amplify difference by 20x and save heatmap
    amplified = diff.point(lambda p: min(255, p * 20))
    amplified.save(output_path)
    
    # Convert diff to grayscale to calculate statistics for scoring
    diff_gray = diff.convert("L")
    diff_arr = np.array(diff_gray)
    
    mean_val = float(np.mean(diff_arr))
    std_val = float(np.std(diff_arr))
    
    # Calculate ELA risk score
    # For a clean, uniform compression image, std & mean are low.
    # Editing creates sharp boundaries that increase the std of errors.
    ela_risk = min(100.0, mean_val * 2.0 + std_val * 8.0)
    return round(ela_risk, 2)

def run_copy_move(pil_img: Image.Image, output_path: str) -> float:
    """
    Copy-Move detection. Finds identical regions in the image using ORB features and brute-force
    matching. Filters out repeat characters by requiring a minimum spatial translation cluster size.
    """
    # Convert PIL Image to OpenCV format
    cv_img = np.array(pil_img.convert("RGB"))
    img_bgr = cv_img[:, :, ::-1].copy()
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Extract ORB keypoints and descriptors
    orb = cv2.ORB_create(nfeatures=3000)
    kp, des = orb.detectAndCompute(img_gray, None)
    
    # If not enough descriptors, copy-move risk is 0
    if des is None or len(des) < 10:
        cv2.imwrite(output_path, img_bgr)
        return 0.0
        
    # Brute force matcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        # Match descriptors against themselves; k=2 because k=1 is the descriptor itself (distance 0)
        matches = bf.knnMatch(des, des, k=2)
    except Exception:
        cv2.imwrite(output_path, img_bgr)
        return 0.0
        
    valid_matches = []
    for match_pair in matches:
        if len(match_pair) < 2:
            continue
        m, n = match_pair
        
        # n is the match to a different descriptor in the image
        if n.distance < 52:  # Threshold for descriptor similarity
            pt1 = kp[n.queryIdx].pt
            pt2 = kp[n.trainIdx].pt
            
            # Require spatial separation to avoid matching immediate neighbors
            spatial_dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
            if spatial_dist > 60:
                # Compute translation vector (dx, dy)
                dx = pt2[0] - pt1[0]
                dy = pt2[1] - pt1[1]
                
                # Standardize vector direction so reverse directions match
                if dx < 0 or (dx == 0 and dy < 0):
                    dx, dy = -dx, -dy
                    pt1, pt2 = pt2, pt1
                    
                valid_matches.append({
                    'queryIdx': n.queryIdx,
                    'trainIdx': n.trainIdx,
                    'pt1': pt1,
                    'pt2': pt2,
                    'dx': dx,
                    'dy': dy
                })
                
    # Translation shift clustering: group matches that have the same displacement vector (tolerance +/- 20 pixels)
    clustered_matches = []
    for m1 in valid_matches:
        neighbors = []
        for m2 in valid_matches:
            if abs(m1['dx'] - m2['dx']) < 20 and abs(m1['dy'] - m2['dy']) < 20:
                neighbors.append(m2)
        if len(neighbors) >= 12:  # Require at least 12 matches to share the shift vector
            # Spatial standard deviation check: require stamp keypoints to be localized
            pts1 = np.array([n['pt1'] for n in neighbors])
            pts2 = np.array([n['pt2'] for n in neighbors])
            
            std_y1 = np.std(pts1[:, 1])
            std_y2 = np.std(pts2[:, 1])
            std_x1 = np.std(pts1[:, 0])
            std_x2 = np.std(pts2[:, 0])
            
            if std_y1 < 45.0 and std_y2 < 45.0 and std_x1 > 30.0 and std_x2 > 30.0 and std_x1 < 120.0 and std_x2 < 120.0:
                clustered_matches.append(m1)
            
    # Draw matches on the image
    overlay = img_bgr.copy()
    for m in clustered_matches:
        p1 = (int(m['pt1'][0]), int(m['pt1'][1]))
        p2 = (int(m['pt2'][0]), int(m['pt2'][1]))
        cv2.circle(overlay, p1, 5, (0, 0, 255), -1)
        cv2.circle(overlay, p2, 5, (0, 0, 255), -1)
        cv2.line(overlay, p1, p2, (255, 0, 0), 2)
        
    cv2.imwrite(output_path, overlay)
    
    # Calculate copy-move risk
    # Based on the number of unique keypoints involved in the cluster matches
    unique_keypoint_indices = set()
    for m in clustered_matches:
        unique_keypoint_indices.add(m['queryIdx'])
        unique_keypoint_indices.add(m['trainIdx'])
        
    copy_move_risk = min(100.0, len(unique_keypoint_indices) * 8.0)
    return round(copy_move_risk, 2)

def run_metadata_audit(pdf_path: str) -> tuple[float, list[dict]]:
    """
    Audits PDF metadata and structure. Flags suspicious mod/creation date gaps,
    known editing software, incremental saves, and unembedded fonts.
    """
    flags = []
    severity_weights = {"LOW": 10, "MEDIUM": 20, "HIGH": 40}
    total_severity = 0
    
    # 1. Metadata check via PyMuPDF
    doc = fitz.open(pdf_path)
    meta = doc.metadata
    
    # Check date gap
    creation_date_str = meta.get("creationDate")
    mod_date_str = meta.get("modDate")
    
    creation_dt = parse_pdf_date(creation_date_str)
    mod_dt = parse_pdf_date(mod_date_str)
    
    if creation_dt and mod_dt:
        time_diff = (mod_dt - creation_dt).total_seconds()
        if time_diff > 180:  # Gap greater than 3 minutes
            flags.append({
                "flag": "Modified Date Delay",
                "detail": f"Document modified {int(time_diff)} seconds after creation (Creation: {creation_date_str}, Mod: {mod_date_str}).",
                "severity": "LOW"
            })
            total_severity += severity_weights["LOW"]
            
    # Check suspicious software strings in Creator / Producer / Author
    editors = ["ilovepdf", "smallpdf", "pdf2go", "soda pdf", "pdf-xchange", "photoshop",
               "illustrator", "inkscape", "canva", "nitro", "pdfescape", "pdfsam", "pdfill",
               "liberation", "ghostscript", "pdf creator", "phantom", "acrobat re-save"]
    
    creator = (meta.get("creator") or "").lower()
    producer = (meta.get("producer") or "").lower()
    author = (meta.get("author") or "").lower()
    
    matched_editors = []
    for editor in editors:
        if editor in creator or editor in producer or editor in author:
            matched_editors.append(editor)
            
    if matched_editors:
        flags.append({
            "flag": "Suspicious Editor Metadata",
            "detail": f"Document metadata indicates editing via: {', '.join(matched_editors)}.",
            "severity": "HIGH"
        })
        total_severity += severity_weights["HIGH"]
        
    # Check font subsetting anomalies
    # Standard PDFs subset fonts (e.g., AAAAAA+FontName). Mix of subsets and un-embedded system fonts is suspicious.
    base14 = {
        "courier", "courier-bold", "courier-oblique", "courier-boldoblique",
        "helvetica", "helvetica-bold", "helvetica-oblique", "helvetica-boldoblique",
        "times-roman", "times-bold", "times-italic", "times-bolditalic",
        "symbol", "zapfdingbats"
    }
    
    unique_fonts = set()
    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        for font in page.get_fonts():
            fontname = font[3]
            unique_fonts.add(fontname)
            
    anomalous_fonts = []
    for fontname in unique_fonts:
        has_subset = False
        parts = fontname.split("+")
        if len(parts) > 1:
            prefix = parts[0]
            if len(prefix) == 6 and prefix.isupper():
                has_subset = True
        
        clean_name = parts[-1].lower()
        if not has_subset and clean_name not in base14:
            anomalous_fonts.append(fontname)
            
    if anomalous_fonts:
        flags.append({
            "flag": "Unembedded/Non-subsetted Fonts",
            "detail": f"Anomalous fonts detected without subsetting: {', '.join(anomalous_fonts)}.",
            "severity": "MEDIUM"
        })
        total_severity += severity_weights["MEDIUM"]
        
    doc.close()
    
    # 2. Check multiple incremental-saves (multiple startxref markers in file bytes)
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
            xref_count = content.count(b"startxref")
            
        if xref_count > 1:
            flags.append({
                "flag": "Multiple Incremental Saves",
                "detail": f"The PDF file contains {xref_count} incremental revisions. This indicates modifications after creation.",
                "severity": "MEDIUM"
            })
            total_severity += severity_weights["MEDIUM"]
    except Exception as e:
        pass
        
    metadata_risk = min(100.0, total_severity)
    return round(metadata_risk, 2), flags

def analyze_document(file_path: str, static_dir: str) -> dict:
    """
    Main analysis orchestrator. Detects file type, runs ELA, Copy-Move,
    and Metadata audit, generates overlays, and fuses scores.
    """
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    
    # Generate unique output filenames for overlays
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ela_filename = f"ela_{base_name}_{timestamp}.jpg"
    copymove_filename = f"copymove_{base_name}_{timestamp}.jpg"
    
    ela_output_path = os.path.join(static_dir, ela_filename)
    copymove_output_path = os.path.join(static_dir, copymove_filename)
    
    is_pdf = file_path.lower().endswith(".pdf")
    
    # Load first page as Pillow Image
    pil_img = None
    if is_pdf:
        try:
            doc = fitz.open(file_path)
            if doc.is_encrypted:
                doc.close()
                raise ValueError("Encrypted or password-protected PDF files are not supported.")
            if len(doc) == 0:
                doc.close()
                raise ValueError("The PDF document has no pages.")
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=150)
            pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError("Corrupted or invalid PDF file.") from e
    else:
        # Assumed image format
        try:
            with Image.open(file_path) as verify_img:
                verify_img.verify()
            pil_img = Image.open(file_path).convert("RGB")
        except Exception as e:
            raise ValueError("Corrupted or invalid image file.") from e
        
    # Save original page image for display comparison
    original_filename = f"original_{base_name}_{timestamp}.jpg"
    original_output_path = os.path.join(static_dir, original_filename)
    pil_img.save(original_output_path, "JPEG", quality=95)
    
    # Run ELA and Copy-Move
    ela_risk = run_ela(pil_img, ela_output_path)
    
    # Sharp vector text edges produce false-positive ringing compression errors in ELA.
    # If the PDF contains native vector text, we scale down the ELA risk score.
    if is_pdf:
        try:
            doc = fitz.open(file_path)
            v_text = ""
            for p in doc:
                v_text += p.get_text()
            doc.close()
            if len(v_text.strip()) > 100:
                ela_risk = round(ela_risk / 4.0, 2)
        except Exception:
            pass
            
    copymove_risk = run_copy_move(pil_img, copymove_output_path)
    
    # Run Metadata Audit for PDFs only
    if is_pdf:
        metadata_risk, metadata_flags = run_metadata_audit(file_path)
    else:
        metadata_risk = 0.0
        metadata_flags = []
        
    # Trust Score Fusion
    # Weights: ELA 0.35, Copy-Move 0.35, Metadata 0.30
    fused_risk = (0.35 * ela_risk) + (0.35 * copymove_risk) + (0.30 * metadata_risk)
    trust_score = max(0.0, min(100.0, 100.0 - fused_risk))
    
    return {
        "filename": filename,
        "trust_score": round(trust_score, 1),
        "original_url": f"/static/{original_filename}",
        "signals": {
            "ela": {
                "risk": ela_risk,
                "overlay_url": f"/static/{ela_filename}"
            },
            "copy_move": {
                "risk": copymove_risk,
                "overlay_url": f"/static/{copymove_filename}"
            },
            "metadata": {
                "risk": metadata_risk,
                "flags": metadata_flags
            }
        }
    }
