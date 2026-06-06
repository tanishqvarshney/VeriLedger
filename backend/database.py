import sqlite3
import hashlib
import datetime

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def init_db(db_path: str):
    """
    Initializes the SQLite database and creates the ledger table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            doc_hash TEXT NOT NULL,
            prev_row_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_to_ledger(db_path: str, filename: str, file_bytes: bytes) -> dict:
    """
    Computes the SHA-256 of raw bytes, retrieves the previous row's chain hash,
    computes the new chain hash, inserts into SQLite, and returns the inserted row.
    """
    # 1. Compute document hash
    doc_hash = hashlib.sha256(file_bytes).hexdigest()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Get previous row's chain_hash
    cursor.execute("SELECT chain_hash FROM ledger ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        prev_row_hash = row[0]
    else:
        # First entry in the ledger
        prev_row_hash = GENESIS_HASH
        
    # 3. Compute chain_hash = SHA-256(doc_hash + prev_row_hash)
    hasher = hashlib.sha256()
    hasher.update((doc_hash + prev_row_hash).encode('utf-8'))
    chain_hash = hasher.hexdigest()
    
    # 4. Insert row
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO ledger (filename, doc_hash, prev_row_hash, chain_hash, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (filename, doc_hash, prev_row_hash, chain_hash, timestamp))
    
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": inserted_id,
        "filename": filename,
        "doc_hash": doc_hash,
        "prev_row_hash": prev_row_hash,
        "chain_hash": chain_hash,
        "timestamp": timestamp
    }

def get_ledger(db_path: str) -> list[dict]:
    """
    Returns all ledger entries ordered by id.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, doc_hash, prev_row_hash, chain_hash, timestamp FROM ledger ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def verify_ledger(db_path: str) -> dict:
    """
    Recomputes and verifies the hash chain for all entries.
    Returns whether the ledger is intact and the list of tampered row IDs.
    """
    entries = get_ledger(db_path)
    if not entries:
        return {"intact": True, "tampered_ids": []}
        
    tampered_ids = []
    expected_prev_hash = GENESIS_HASH
    
    for entry in entries:
        row_id = entry["id"]
        doc_hash = entry["doc_hash"]
        prev_row_hash = entry["prev_row_hash"]
        chain_hash = entry["chain_hash"]
        
        # Verify previous row hash matches expectation
        if prev_row_hash != expected_prev_hash:
            tampered_ids.append(row_id)
            # Synchronize expectation to continue auditing subsequent rows
            expected_prev_hash = chain_hash
            continue
            
        # Recompute chain_hash = SHA-256(doc_hash + prev_row_hash)
        hasher = hashlib.sha256()
        hasher.update((doc_hash + prev_row_hash).encode('utf-8'))
        computed_chain_hash = hasher.hexdigest()
        
        # Verify computed chain hash matches stored chain hash
        if computed_chain_hash != chain_hash:
            tampered_ids.append(row_id)
            
        expected_prev_hash = chain_hash
        
    return {
        "intact": len(tampered_ids) == 0,
        "tampered_ids": tampered_ids
    }
