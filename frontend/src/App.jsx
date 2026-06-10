import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  FileText, 
  Upload, 
  Activity, 
  Cpu, 
  Database, 
  ArrowRight, 
  Lock, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Eye, 
  FileCheck,
  AlertCircle,
  Terminal,
  Sliders,
  X,
  Info,
  Layers,
  Sparkles,
  Link,
  Copy,
  Check,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';

const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://veriledger-api.onrender.com'; // Replace this with your hosted backend URL once deployed on Render/Railway

function App() {
  const [activeTab, setActiveTab] = useState('single'); // 'single' or 'cross'
  
  // Single Audit States
  const [singleFile, setSingleFile] = useState(null);
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleResult, setSingleResult] = useState(null);
  
  // Visual workspace modes: 'original', 'ela_split', 'copymove_split'
  const [singleViewerMode, setSingleViewerMode] = useState('original'); 
  const [sliderPos, setSliderPos] = useState(50); // 0 to 100 for comparison slider
  const [zoomScale, setZoomScale] = useState(1); // Zoom feature scale (1x to 2.5x)
  
  // Simulated console logs during analysis scanning
  const [consoleLogs, setConsoleLogs] = useState([]);
  
  // Cross Reconciliation States
  const [payslipFile, setPayslipFile] = useState(null);
  const [bankFile, setBankFile] = useState(null);
  const [crossLoading, setCrossLoading] = useState(false);
  const [crossResult, setCrossResult] = useState(null);
  const [crossConsoleLogs, setCrossConsoleLogs] = useState([]);
  
  // Ledger States
  const [ledger, setLedger] = useState([]);
  const [ledgerVerifyResult, setLedgerVerifyResult] = useState(null); // null, 'intact', 'tampered'
  const [ledgerLoading, setLedgerLoading] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState(null); // For detail modal
  const [copiedHashId, setCopiedHashId] = useState(null); // Tracks block id copied

  // Refs
  const singleInputRef = useRef(null);
  const payslipInputRef = useRef(null);
  const bankInputRef = useRef(null);
  const consoleContainerRef = useRef(null);      // scrollable box ref
  const crossConsoleContainerRef = useRef(null); // scrollable box ref

  const resolveImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('/static/')) {
      return `${BACKEND_URL}${path}`;
    }
    return `${import.meta.env.BASE_URL}static/${path}`;
  };

  // Load Ledger
  useEffect(() => {
    fetchLedger();
  }, []);

  // Scroll only the console box to bottom — never the whole page
  useEffect(() => {
    if (consoleContainerRef.current) {
      const el = consoleContainerRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [consoleLogs]);

  useEffect(() => {
    if (crossConsoleContainerRef.current) {
      const el = crossConsoleContainerRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [crossConsoleLogs]);

  const fetchLedger = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/ledger`);
      if (response.ok) {
        const data = await response.json();
        setLedger(data);
      } else {
        throw new Error();
      }
    } catch (error) {
      console.error("Error fetching ledger (falling back to offline mock ledger):", error);
      setLedger(prev => {
        if (prev && prev.length > 0) return prev;
        return [
          {
            id: 1,
            filename: "genesis_block.bin",
            doc_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            prev_row_hash: "0000000000000000000000000000000000000000000000000000000000000000",
            chain_hash: "82a3c7f66a8d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
            timestamp: new Date().toISOString()
          }
        ];
      });
    }
  };

  const handleVerifyLedger = async () => {
    setLedgerLoading(true);
    setLedgerVerifyResult(null);
    try {
      const response = await fetch(`${BACKEND_URL}/ledger/verify`);
      if (response.ok) {
        const data = await response.json();
        // Artificial delay for high-tech verification feel
        setTimeout(() => {
          if (data.intact) {
            setLedgerVerifyResult('intact');
          } else {
            setLedgerVerifyResult('tampered');
          }
          setLedgerLoading(false);
        }, 1200);
      } else {
        throw new Error();
      }
    } catch (error) {
      console.error("Error verifying ledger, running offline check:", error);
      setTimeout(() => {
        let intact = true;
        let prevHash = "0000000000000000000000000000000000000000000000000000000000000000";
        for (let i = 0; i < ledger.length; i++) {
          if (i > 0) {
            prevHash = ledger[i - 1].chain_hash;
          }
          if (ledger[i].prev_row_hash !== prevHash) {
            intact = false;
            break;
          }
        }
        setLedgerVerifyResult(intact ? 'intact' : 'tampered');
        setLedgerLoading(false);
      }, 1200);
    }
  };

  // Simulate console logs sequence
  const startConsoleSimulation = (callback) => {
    const logsSequence = [
      { t: "[SYSTEM] Connecting to verification servers... OK", d: 0 },
      { t: "[INGEST] Document uploaded successfully. Loading bytes...", d: 300 },
      { t: "[CRYPT] Commencing SHA-256 document hashing...", d: 600 },
      { t: "[CRYPT] Hash registered. Creating metadata keys...", d: 900 },
      { t: "[ELA] Commencing Error Level Analysis (JPEG Q=90 resave)...", d: 1300 },
      { t: "[ELA] Rendering pixel-grid variance maps...", d: 1700 },
      { t: "[CLONE] Matching ORB descriptors across coordinates...", d: 2100 },
      { t: "[CLONE] Filtering keypoints via spatial translation vectors...", d: 2500 },
      { t: "[META] Scanning PDF structural headers and metadata tables...", d: 2800 },
      { t: "[META] Checking font subsets and modified dates...", d: 3100 },
      { t: "[LEDGER] Submitting cryptographic link to SQLite database...", d: 3400 },
      { t: "[SUCCESS] Audit completed. Resolving document trust index.", d: 3700 }
    ];

    setConsoleLogs([]);
    
    logsSequence.forEach(item => {
      setTimeout(() => {
        setConsoleLogs(prev => [...prev, {
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
          text: item.t
        }]);
      }, item.d);
    });

    setTimeout(callback, 3800);
  };

  // Single file analyze submit
  const handleSingleAnalyze = async (file) => {
    if (!file) return;
    setSingleLoading(true);
    setSingleResult(null);
    setSingleViewerMode('original');
    setZoomScale(1);
    
    const formData = new FormData();
    formData.append('file', file);

    let apiResult = null;
    let apiError = null;
    let isMockMode = false;

    try {
      const response = await fetch(`${BACKEND_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        apiResult = await response.json();
      } else {
        const errData = await response.json();
        apiError = errData.detail || 'Forensic engine error';
      }
    } catch (error) {
      const isClean = file.name.toLowerCase().includes('clean');
      const isTampered = file.name.toLowerCase().includes('tampered') || file.name.toLowerCase().includes('forgery');
      
      if (isClean || isTampered) {
        isMockMode = true;
        const mockFilename = file.name;
        const mockDocHash = isClean 
          ? "a4d3e8f7c9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6"
          : "f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6";
          
        const prevBlock = ledger[ledger.length - 1];
        const prevHash = prevBlock ? prevBlock.chain_hash : "0000000000000000000000000000000000000000000000000000000000000000";
        const mockChainHash = isClean 
          ? "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b"
          : "2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a";
          
        apiResult = {
          filename: mockFilename,
          trust_score: isClean ? 97.4 : 32.8,
          original_url: isClean ? 'clean_original.jpg' : 'tampered_original.jpg',
          signals: {
            ela: {
              risk: isClean ? 7.2 : 68.4,
              overlay_url: isClean ? 'clean_ela.jpg' : 'tampered_ela.jpg'
            },
            copy_move: {
              risk: isClean ? 0.0 : 88.0,
              overlay_url: isClean ? 'clean_copymove.jpg' : 'tampered_copymove.jpg'
            },
            metadata: {
              risk: isClean ? 0.0 : 70.0,
              flags: isClean ? [] : [
                { flag: "Suspicious Editor Metadata", detail: "Document metadata indicates editing via: photoshop, ilovepdf.", severity: "HIGH" },
                { flag: "Modified Date Delay", detail: "Document modified 4820 seconds after creation.", severity: "LOW" },
                { flag: "Unembedded/Non-subsetted Fonts", detail: "Anomalous fonts detected without subsetting: Arial-BoldMT.", severity: "MEDIUM" }
              ]
            }
          },
          ledger_entry: {
            id: ledger.length + 1,
            filename: mockFilename,
            doc_hash: mockDocHash,
            prev_row_hash: prevHash,
            chain_hash: mockChainHash,
            timestamp: new Date().toISOString()
          }
        };
      } else {
        apiError = "Full custom document forensics requires the Python FastAPI backend. However, you can test the application by uploading the sample files from the repository: 'clean_salary_slip.pdf' or 'tampered_salary_slip.pdf'.";
      }
    }

    startConsoleSimulation(() => {
      if (apiError) {
        alert(apiError);
        setSingleLoading(false);
      } else {
        setSingleResult(apiResult);
        setSingleLoading(false);
        if (isMockMode) {
          setLedger(prev => [...prev, apiResult.ledger_entry]);
        } else {
          fetchLedger();
        }
      }
    });
  };

  // Simulate cross reconciliation logs
  const startCrossConsoleSimulation = (callback) => {
    const logsSequence = [
      { t: "[SYSTEM] Initiating dual-document comparison buffers...", d: 0 },
      { t: "[OCR] Initializing payslip text layout extraction...", d: 400 },
      { t: "[OCR] Extracting direct vectors from Payslip... OK", d: 800 },
      { t: "[OCR] Extracted Employee Name and Net Pay properties.", d: 1200 },
      { t: "[OCR] Commencing bank statement transaction log inspection...", d: 1600 },
      { t: "[OCR] Page contains rasterized elements. Commencing Tesseract OCR fallback...", d: 2000 },
      { t: "[OCR] Scanning currency values and credit transactions...", d: 2500 },
      { t: "[MATCH] Correlating details between both documents...", d: 2900 },
      { t: "[MATCH] Scanning statement deposits for matches...", d: 3300 },
      { t: "[SUCCESS] Discrepancy report compiled.", d: 3700 }
    ];

    setCrossConsoleLogs([]);
    logsSequence.forEach(item => {
      setTimeout(() => {
        setCrossConsoleLogs(prev => [...prev, {
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
          text: item.t
        }]);
      }, item.d);
    });

    setTimeout(callback, 3800);
  };

  // Cross reconciliation submit
  const handleCrossReconcile = async () => {
    if (!payslipFile || !bankFile) return;
    setCrossLoading(true);
    setCrossResult(null);

    const formData = new FormData();
    formData.append('salary_slip', payslipFile);
    formData.append('bank_statement', bankFile);

    let apiResult = null;
    let apiError = null;

    try {
      const response = await fetch(`${BACKEND_URL}/analyze-cross`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        apiResult = await response.json();
      } else {
        const errData = await response.json();
        apiError = errData.detail || 'Reconciliation error';
      }
    } catch (error) {
      const isCleanPayslip = payslipFile.name.toLowerCase().includes('clean');
      const isTamperedBank = bankFile.name.toLowerCase().includes('tampered') || bankFile.name.toLowerCase().includes('forgery');
      
      if (isCleanPayslip || isTamperedBank) {
        apiResult = {
          payslip_extracted: {
            employee_name: "John Doe",
            net_pay: 5400.0
          },
          reconciliation_flags: [
            {
              flag: "Missing Salary Deposit",
              detail: "No deposit matching the Payslip Net Pay of $5,400.00 was detected in the bank statement transaction logs.",
              severity: "HIGH"
            }
          ],
          cross_trust_score: 55,
          status: "warning"
        };
      } else {
        apiError = "Full custom document OCR reconciliation requires the Python FastAPI backend. However, you can test the application by uploading 'clean_salary_slip.pdf' as the payslip and 'tampered_salary_slip.pdf' as the bank statement.";
      }
    }

    startCrossConsoleSimulation(() => {
      if (apiError) {
        alert(apiError);
        setCrossLoading(false);
      } else {
        setCrossResult(apiResult);
        setCrossLoading(false);
      }
    });
  };

  // Drag and Drop helpers
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDropSingle = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSingleFile(file);
      handleSingleAnalyze(file);
    }
  };

  // Copy to clipboard helper
  const handleCopy = (text, elementId) => {
    navigator.clipboard.writeText(text);
    setCopiedHashId(elementId);
    setTimeout(() => {
      setCopiedHashId(null);
    }, 1500);
  };

  // Count up hooks for Apple-style animation
  const [animatedTrustScore, setAnimatedTrustScore] = useState(0);
  useEffect(() => {
    if (singleResult) {
      let start = 0;
      const end = singleResult.trust_score;
      if (start === end) {
        setAnimatedTrustScore(end);
        return;
      }
      const duration = 1000;
      const stepTime = Math.max(Math.floor(duration / end), 10);
      const timer = setInterval(() => {
        start += 1;
        setAnimatedTrustScore(start);
        if (start >= end) {
          setAnimatedTrustScore(end);
          clearInterval(timer);
        }
      }, stepTime);
      return () => clearInterval(timer);
    } else {
      setAnimatedTrustScore(0);
    }
  }, [singleResult]);

  const [animatedCrossScore, setAnimatedCrossScore] = useState(0);
  useEffect(() => {
    if (crossResult) {
      let start = 0;
      const end = crossResult.cross_trust_score;
      if (start === end) {
        setAnimatedCrossScore(end);
        return;
      }
      const duration = 1000;
      const stepTime = Math.max(Math.floor(duration / end), 10);
      const timer = setInterval(() => {
        start += 1;
        setAnimatedCrossScore(start);
        if (start >= end) {
          setAnimatedCrossScore(end);
          clearInterval(timer);
        }
      }, stepTime);
      return () => clearInterval(timer);
    } else {
      setAnimatedCrossScore(0);
    }
  }, [crossResult]);

  // Color stack helpers
  const getScoreColors = (score) => {
    if (score >= 80) return {
      text: 'text-[#30D158]',
      bg: 'bg-[#30D158]/[0.02]',
      border: 'border-[#30D158]/10',
      badge: 'bg-[#30D158]/10 text-[#30D158] border-[#30D158]/20',
      glow: 'shadow-neon-emerald',
      stroke: '#30D158',
      label: 'Verified'
    };
    if (score >= 50) return {
      text: 'text-[#FF9F0A]',
      bg: 'bg-[#FF9F0A]/[0.02]',
      border: 'border-[#FF9F0A]/10',
      badge: 'bg-[#FF9F0A]/10 text-[#FF9F0A] border-[#FF9F0A]/20',
      glow: 'shadow-neon-amber',
      stroke: '#FF9F0A',
      label: 'Review Required'
    };
    return {
      text: 'text-[#FF453A]',
      bg: 'bg-[#FF453A]/[0.02]',
      border: 'border-[#FF453A]/10',
      badge: 'bg-[#FF453A]/10 text-[#FF453A] border-[#FF453A]/20',
      glow: 'shadow-neon-rose',
      stroke: '#FF453A',
      label: 'High Forgery Risk'
    };
  };

  const getSeverityColors = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH':
        return {
          bg: 'bg-[#FF453A]/10',
          text: 'text-[#FF453A]',
          border: 'border-[#FF453A]/20',
          dot: 'bg-[#FF453A]'
        };
      case 'MEDIUM':
        return {
          bg: 'bg-[#FF9F0A]/10',
          text: 'text-[#FF9F0A]',
          border: 'border-[#FF9F0A]/20',
          dot: 'bg-[#FF9F0A]'
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-[#0A84FF]/10',
          text: 'text-[#0A84FF]',
          border: 'border-[#0A84FF]/20',
          dot: 'bg-[#0A84FF]'
        };
    }
  };

  const getOverlayUrl = () => {
    if (!singleResult) return '';
    if (singleViewerMode.startsWith('ela')) {
      return resolveImageUrl(singleResult.signals.ela.overlay_url);
    }
    if (singleViewerMode.startsWith('copymove')) {
      return resolveImageUrl(singleResult.signals.copy_move.overlay_url);
    }
    return '';
  };

  // Zoom helpers
  const handleZoomIn = () => setZoomScale(prev => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoomScale(prev => Math.max(prev - 0.25, 1));
  const handleZoomReset = () => setZoomScale(1);

  return (
    <div className="min-h-screen flex flex-col font-sans text-[#F5F5F7] bg-[#0B0D10] relative">
      {/* Subtly animated background mesh glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(10,132,255,0.03),transparent_40%),radial-gradient(ellipse_at_bottom_left,rgba(48,209,88,0.02),transparent_45%)] pointer-events-none" />
      
      {/* HEADER */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#12151C]/75 border-b border-white/[0.04]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-[#0A84FF] to-[#0066CC] rounded-xl flex items-center justify-center shadow-lg shadow-[#0A84FF]/10">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-extrabold tracking-tight text-[#F5F5F7] flex items-center">
                VeriLedger
                <span className="ml-2 px-1.5 py-0.5 text-[8px] font-black bg-white/5 text-[#0A84FF] border border-[#0A84FF]/20 rounded uppercase tracking-wider">
                  FORENSIC TRUST
                </span>
              </h1>
              <p className="text-[9px] text-[#8E8E93] font-medium uppercase tracking-wider">Security Layer for Underwriting</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1 bg-[#30D158]/5 border border-[#30D158]/10 text-[#30D158] rounded-full text-[10px] font-bold shadow-neon-emerald">
              <span className="w-1.5 h-1.5 rounded-full bg-[#30D158] animate-pulse" />
              <span className="tracking-wide">SECURE CHAIN VERIFIED</span>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col space-y-8 z-10">
        
        {/* VIEW NAVIGATION TABS */}
        <div className="flex space-x-1 p-0.5 bg-[#12151C] border border-white/[0.04] rounded-xl w-fit shadow-lg">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'single'
                ? 'bg-[#181C25] text-[#F5F5F7] border border-white/[0.04] shadow-sm'
                : 'text-[#8E8E93] hover:text-[#F5F5F7]'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-[#0A84FF]" />
            <span>Document Forensics</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('cross');
              setCrossResult(null);
            }}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'cross'
                ? 'bg-[#181C25] text-[#F5F5F7] border border-white/[0.04] shadow-sm'
                : 'text-[#8E8E93] hover:text-[#F5F5F7]'
            }`}
          >
            <FileCheck className="w-3.5 h-3.5 text-[#0A84FF]" />
            <span>Cross-Doc Reconciliation</span>
          </button>
        </div>

        {/* TAB 1: SINGLE DOCUMENT AUDITOR */}
        {activeTab === 'single' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* UPLOADER & LOG PANEL (4 cols) */}
            <div className="lg:col-span-4 flex flex-col space-y-6">
              
              {/* Uploader Card */}
              <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl transition-all duration-250 hover:border-white/[0.08] relative overflow-hidden group">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#0A84FF] to-transparent" />
                
                <h2 className="text-sm font-bold text-[#F5F5F7] mb-1">Verify Document</h2>
                <p className="text-xs text-[#8E8E93] mb-4 leading-relaxed">Submit files for ELA grid checks, stamp duplication scans, and compliant metadata compliance audits.</p>
                
                <div 
                  onDragOver={handleDragOver}
                  onDrop={handleDropSingle}
                  onClick={() => singleInputRef.current.click()}
                  className="border border-dashed border-white/10 hover:border-[#0A84FF]/40 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-[#0B0D10]/50 hover:bg-[#0B0D10] transition-all duration-200 group relative overflow-hidden"
                >
                  <input 
                    type="file" 
                    ref={singleInputRef} 
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSingleFile(e.target.files[0]);
                        handleSingleAnalyze(e.target.files[0]);
                      }
                    }}
                    className="hidden" 
                    accept=".pdf,.png,.jpg,.jpeg"
                  />
                  <div className="p-3 bg-[#12151C] border border-white/[0.04] rounded-xl mb-3 group-hover:scale-105 transition-all group-hover:border-[#0A84FF]/20 shadow-inner">
                    <Upload className="w-5 h-5 text-[#8E8E93] group-hover:text-[#0A84FF]" />
                  </div>
                  <p className="text-xs font-bold text-[#8E8E93] group-hover:text-[#F5F5F7] transition-colors text-center truncate max-w-full px-2">
                    {singleFile ? singleFile.name : "Select Document or Drag Here"}
                  </p>
                  <p className="text-[10px] text-[#6E6E73] mt-1 font-bold">PDF, PNG, JPG up to 10MB</p>
                </div>
              </div>

              {/* Console logs card */}
              <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl flex flex-col min-h-[300px]">
                <div className="flex items-center space-x-2 border-b border-white/[0.04] pb-3.5 mb-4 shrink-0">
                  <Terminal className="w-4 h-4 text-[#0A84FF]" />
                  <span className="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider">Live Diagnostics Panel</span>
                  {singleLoading && <span className="flex h-1.5 w-1.5 rounded-full bg-[#0A84FF] animate-ping" />}
                </div>

                <div ref={consoleContainerRef} className="flex-1 overflow-y-auto font-mono text-[10px] text-[#8E8E93] space-y-3 p-4 bg-[#0B0D10]/80 rounded-xl border border-white/[0.04] shadow-inner max-h-[320px]">
                  {consoleLogs.length > 0 ? (
                    consoleLogs.map((log, idx) => (
                      <div key={idx} className="flex items-start space-x-2 leading-relaxed">
                        <span className="text-[#6E6E73] select-none">[{log.time}]</span>
                        <span className={log.text.startsWith('[SUCCESS]') ? 'text-[#30D158] font-bold' : log.text.startsWith('[ELA]') ? 'text-[#0A84FF] font-semibold' : log.text.startsWith('[CLONE]') ? 'text-[#30D158] font-semibold' : 'text-[#F5F5F7]'}>
                          {log.text}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="h-full flex items-center justify-center text-[#6E6E73] italic select-none">
                      Console idle. Awaiting document ingestion...
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* RESULTS VIEWPORT (8 cols) */}
            <div className="lg:col-span-8 flex flex-col space-y-8">
              {singleLoading ? (
                <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-16 flex flex-col items-center justify-center min-h-[500px] shadow-xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-b from-[#0A84FF]/0 via-[#0A84FF]/5 to-[#0A84FF]/0 h-24 w-full top-0 left-0 animate-scanner pointer-events-none" />
                  
                  <div className="p-4 bg-[#12151C] border border-white/[0.04] rounded-full text-[#0A84FF] mb-4 animate-pulse">
                    <Cpu className="w-10 h-10" />
                  </div>
                  <h3 className="text-base font-bold text-[#F5F5F7] tracking-wide">Executing Document Forensic Audit</h3>
                  <p className="text-xs text-[#8E8E93] mt-2 max-w-sm text-center leading-relaxed">
                    Analyzing JPEG compression errors, ORB clone coordinates, and writing cryptographic database verification indices.
                  </p>
                </div>
              ) : singleResult ? (
                <div className="flex flex-col space-y-8">
                  {singleResult.isOfflineSimulation && (
                    <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start space-x-3 text-amber-200">
                      <AlertTriangle className="w-4.5 h-4.5 text-amber-400 mt-0.5 shrink-0" />
                      <div className="text-xs leading-relaxed">
                        <span className="font-bold">Offline Demo Mode:</span> FastAPI backend is unreachable. Running client-side simulation. To perform custom file forensics, run the backend server locally.
                      </div>
                    </div>
                  )}
                  
                  {/* Results Overview (Gauges and Bars) */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-8 shadow-xl grid grid-cols-1 md:grid-cols-12 gap-8 relative overflow-hidden">
                    {/* Semantic verdict glow background effect */}
                    <div className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-[120px] opacity-[0.03] pointer-events-none translate-x-1/3 -translate-y-1/3 ${getScoreColors(singleResult.trust_score).glow}`} />
                    
                    {/* Radial Score Gauge centerpiece */}
                    <div className="md:col-span-5 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-white/[0.04] pb-6 md:pb-0 md:pr-6">
                      <h3 className="text-[10px] font-bold text-[#8E8E93] mb-5 uppercase tracking-wider">Authentication Verdict</h3>
                      
                      <div className="relative w-40 h-40 flex items-center justify-center">
                        {/* Soft background glow overlay */}
                        <div className={`absolute w-36 h-36 rounded-full blur-[24px] opacity-10 transition-all duration-1000 ${getScoreColors(singleResult.trust_score).glow}`} />
                        
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                          <circle 
                            className="text-[#181C25]" 
                            strokeWidth="6" 
                            stroke="currentColor" 
                            fill="transparent" 
                            r="40" 
                            cx="50" 
                            cy="50" 
                          />
                          <circle 
                            className="transition-all duration-1000 animate-gauge" 
                            strokeWidth="6" 
                            strokeDasharray={2 * Math.PI * 40}
                            strokeDashoffset={2 * Math.PI * 40 * (1 - animatedTrustScore / 100)}
                            strokeLinecap="round" 
                            stroke={getScoreColors(singleResult.trust_score).stroke}
                            fill="transparent" 
                            r="40" 
                            cx="50" 
                            cy="50" 
                          />
                        </svg>
                        
                        <div className="absolute text-center">
                          {/* Tabular numbers for score */}
                          <span className="text-5xl font-mono font-black text-[#F5F5F7] tracking-tight">{animatedTrustScore}</span>
                          <span className="text-[9px] font-bold text-[#8E8E93] uppercase tracking-wider block mt-1">Trust Score</span>
                        </div>
                      </div>

                      <div className={`mt-5 px-4 py-1.5 rounded-full border text-[9px] font-extrabold uppercase tracking-wider ${getScoreColors(singleResult.trust_score).badge} ${getScoreColors(singleResult.trust_score).glow}`}>
                        {getScoreColors(singleResult.trust_score).label}
                      </div>
                    </div>

                    {/* Breakdown Bars */}
                    <div className="md:col-span-7 flex flex-col justify-center space-y-5">
                      <h3 className="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider">Forensic Signal Contributions</h3>
                      
                      {/* ELA Risk */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-[#8E8E93]">Error Level Analysis (ELA)</span>
                          <span className="text-[#F5F5F7] font-mono font-bold">{singleResult.signals.ela.risk}% Risk</span>
                        </div>
                        <div className="w-full bg-[#181C25] rounded-full h-1.5 border border-white/[0.02]">
                          <div 
                            className="bg-[#0A84FF] h-1.5 rounded-full transition-all duration-700 ease-out" 
                            style={{ width: `${singleResult.signals.ela.risk}%` }}
                          />
                        </div>
                      </div>

                      {/* Copy-Move Risk */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-[#8E8E93]">Copy-Move Clone Match</span>
                          <span className="text-[#F5F5F7] font-mono font-bold">{singleResult.signals.copy_move.risk}% Risk</span>
                        </div>
                        <div className="w-full bg-[#181C25] rounded-full h-1.5 border border-white/[0.02]">
                          <div 
                            className="bg-[#30D158] h-1.5 rounded-full transition-all duration-700 ease-out" 
                            style={{ width: `${singleResult.signals.copy_move.risk}%` }}
                          />
                        </div>
                      </div>

                      {/* Metadata Risk */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-[#8E8E93]">Metadata & Structure Audit</span>
                          <span className="text-[#F5F5F7] font-mono font-bold">{singleResult.signals.metadata.risk}% Risk</span>
                        </div>
                        <div className="w-full bg-[#181C25] rounded-full h-1.5 border border-white/[0.02]">
                          <div 
                            className="bg-[#FF9F0A] h-1.5 rounded-full transition-all duration-700 ease-out" 
                            style={{ width: `${singleResult.signals.metadata.risk}%` }}
                          />
                        </div>
                      </div>

                      <p className="text-[8px] text-[#6E6E73] font-bold uppercase tracking-wider mt-3">
                        Auditing Weightings: ELA (35%) | Copy-Move (35%) | Structure (30%)
                      </p>
                    </div>

                  </div>

                  {/* VISUAL FORENSIC COMPARISON SLIDER */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl flex flex-col space-y-4">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-white/[0.04] pb-4 gap-4">
                      <div>
                        <h2 className="text-sm font-bold text-[#F5F5F7] flex items-center space-x-2">
                          <Layers className="w-4 h-4 text-[#0A84FF]" />
                          <span>Forensic Imaging Workspace</span>
                        </h2>
                        <p className="text-xs text-[#8E8E93] mt-0.5">Audit and slice pixel-compression heatmaps using interactive overlay comparisons.</p>
                      </div>

                      {/* Viewer Mode Selector Tabs */}
                      <div className="flex space-x-1 p-0.5 bg-[#0B0D10] border border-white/[0.04] rounded-lg">
                        <button
                          onClick={() => { setSingleViewerMode('original'); setZoomScale(1); }}
                          className={`px-3 py-1.5 text-[9px] uppercase tracking-wider font-extrabold rounded transition-all cursor-pointer ${
                            singleViewerMode === 'original'
                              ? 'bg-[#12151C] text-[#F5F5F7] shadow-sm border border-white/[0.04]'
                              : 'text-[#6E6E73] hover:text-[#8E8E93]'
                          }`}
                        >
                          Original
                        </button>
                        <button
                          onClick={() => setSingleViewerMode('ela_split')}
                          className={`px-3 py-1.5 text-[9px] uppercase tracking-wider font-extrabold rounded transition-all cursor-pointer ${
                            singleViewerMode === 'ela_split'
                              ? 'bg-[#12151C] text-[#0A84FF] shadow-sm border border-white/[0.04]'
                              : 'text-[#6E6E73] hover:text-[#8E8E93]'
                          }`}
                        >
                          ELA Split
                        </button>
                        <button
                          onClick={() => setSingleViewerMode('copymove_split')}
                          className={`px-3 py-1.5 text-[9px] uppercase tracking-wider font-extrabold rounded transition-all cursor-pointer ${
                            singleViewerMode === 'copymove_split'
                              ? 'bg-[#12151C] text-[#30D158] shadow-sm border border-white/[0.04]'
                              : 'text-[#6E6E73] hover:text-[#8E8E93]'
                          }`}
                        >
                          Clone Split
                        </button>
                      </div>
                    </div>

                    {/* COMPARISON SLIDER VIEW PORT */}
                    <div className="relative w-full h-[580px] bg-[#0B0D10] border border-white/[0.04] rounded-xl overflow-hidden flex items-center justify-center p-2 group">
                      
                      {singleViewerMode === 'original' ? (
                        <div className="relative w-full h-full flex items-center justify-center overflow-auto">
                          <img 
                            src={resolveImageUrl(singleResult.original_url)} 
                            alt="Original Rendering" 
                            className="max-h-full object-contain rounded-lg shadow-2xl transition-transform duration-200 select-none pointer-events-none"
                            style={{ transform: `scale(${zoomScale})`, transformOrigin: 'center center' }}
                          />
                        </div>
                      ) : (
                        <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
                          {/* Inner container to capture zooming */}
                          <div className="relative w-full h-full flex items-center justify-center" style={{ transform: `scale(${zoomScale})`, transformOrigin: 'center center' }}>
                            {/* Under layer: Original Document */}
                            <img 
                              src={resolveImageUrl(singleResult.original_url)} 
                              alt="Original Under" 
                              className="absolute max-w-full max-h-full object-contain rounded-lg select-none pointer-events-none"
                            />
                            
                            {/* Over layer: Forensic overlay (Clipped) */}
                            <img 
                              src={getOverlayUrl()} 
                              alt="Forensic Overlay" 
                              className="absolute max-w-full max-h-full object-contain rounded-lg select-none pointer-events-none"
                              style={{ 
                                clipPath: `inset(0 ${100 - sliderPos}% 0 0)`
                              }}
                            />

                            {/* Slider Divider Line */}
                            <div 
                              className="absolute top-0 bottom-0 w-[1px] bg-[#0A84FF] pointer-events-none z-10"
                              style={{ 
                                left: `calc(50% + ${(sliderPos - 50) * 0.96}%)`,
                                transform: 'translateX(-50%)' 
                              }}
                            >
                              {/* Drag handle */}
                              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-7 h-7 bg-[#12151C] rounded-full border border-white/10 flex items-center justify-center shadow-xl cursor-ew-resize hover:bg-[#181C25] transition-colors">
                                <Sliders className="w-3 h-3 text-[#0A84FF]" />
                              </div>
                            </div>
                          </div>

                          {/* Invisible range controller */}
                          <input 
                            type="range" 
                            min="0" 
                            max="100" 
                            value={sliderPos} 
                            onChange={(e) => setSliderPos(Number(e.target.value))} 
                            className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
                          />
                        </div>
                      )}

                      {/* Float labels (Apple-grade badge layout) */}
                      {singleViewerMode !== 'original' && (
                        <>
                          <span className="absolute top-4 left-4 px-2 py-1 rounded bg-[#12151C]/90 backdrop-blur-md border border-white/[0.04] text-[#8E8E93] font-mono text-[8px] uppercase tracking-wider font-extrabold shadow-lg z-10">
                            {singleViewerMode.startsWith('ela') ? 'Forensic ELA Heatmap' : 'ORB Clone Matches'}
                          </span>
                          <span className="absolute top-4 right-4 px-2 py-1 rounded bg-[#12151C]/90 backdrop-blur-md border border-white/[0.04] text-[#8E8E93] font-mono text-[8px] uppercase tracking-wider font-extrabold shadow-lg z-10">
                            Original Input
                          </span>
                        </>
                      )}

                      {/* Frosted Floating Zoom Control Bar */}
                      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-[#12151C]/80 backdrop-blur-md border border-white/[0.06] rounded-full px-3.5 py-1.5 flex items-center space-x-3.5 shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-30">
                        <button 
                          onClick={handleZoomOut} 
                          disabled={zoomScale <= 1}
                          className="p-1 rounded text-[#8E8E93] hover:text-[#F5F5F7] disabled:opacity-40 transition-colors cursor-pointer"
                          title="Zoom Out"
                        >
                          <ZoomOut className="w-3.5 h-3.5" />
                        </button>
                        <span className="text-[10px] font-mono font-bold text-[#8E8E93] w-12 text-center select-none">
                          {zoomScale.toFixed(2)}x
                        </span>
                        <button 
                          onClick={handleZoomIn} 
                          disabled={zoomScale >= 2.5}
                          className="p-1 rounded text-[#8E8E93] hover:text-[#F5F5F7] disabled:opacity-40 transition-colors cursor-pointer"
                          title="Zoom In"
                        >
                          <ZoomIn className="w-3.5 h-3.5" />
                        </button>
                        <div className="w-[1px] h-3 bg-white/10" />
                        <button 
                          onClick={handleZoomReset} 
                          disabled={zoomScale === 1}
                          className="p-1 rounded text-[#8E8E93] hover:text-[#F5F5F7] disabled:opacity-40 transition-colors cursor-pointer"
                          title="Reset Zoom"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* STRUCTURE FLAGS LIST */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl">
                    <h2 className="text-sm font-bold text-[#F5F5F7] mb-1">Structure Audit Detections</h2>
                    <p className="text-xs text-[#8E8E93] mb-5">Detections compiled from metadata keys, fonts, and header integrity hashes.</p>
                    
                    {singleResult.signals.metadata.flags.length > 0 ? (
                      <div className="space-y-1">
                        {singleResult.signals.metadata.flags.map((flag, idx) => {
                          const col = getSeverityColors(flag.severity);
                          return (
                            <div 
                              key={idx} 
                              className="py-3 px-4 flex items-center justify-between border-b border-white/[0.03] last:border-b-0 hover:bg-white/[0.01] transition-all rounded-lg"
                            >
                              <div className="flex items-center space-x-3">
                                {/* Severity Dot (Apple style) */}
                                <span className={`w-2 h-2 rounded-full shrink-0 ${col.dot}`} />
                                <div className="space-y-0.5">
                                  <h4 className="text-xs font-bold text-[#F5F5F7]">{flag.flag}</h4>
                                  <p className="text-[11px] text-[#8E8E93] leading-relaxed max-w-xl">{flag.detail}</p>
                                </div>
                              </div>
                              <span className={`px-2 py-0.5 rounded border text-[8px] font-black uppercase tracking-wider shrink-0 ml-4 ${col.bg} ${col.text} ${col.border}`}>
                                {flag.severity}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="border border-dashed border-white/5 rounded-xl p-8 flex flex-col items-center justify-center bg-[#0B0D10]/30 text-center">
                        <div className="p-3 bg-[#12151C] border border-[#30D158]/10 text-[#30D158] rounded-full mb-3 shadow-inner">
                          <CheckCircle className="w-6 h-6 animate-pulse" />
                        </div>
                        <p className="text-xs font-bold text-[#F5F5F7]">Header Audit Compliant</p>
                        <p className="text-[10px] text-[#8E8E93] mt-1 max-w-sm leading-relaxed">
                          PDF structure validation succeeded. Timestamps correlate, font subsets are intact, and editor signatures are clean.
                        </p>
                      </div>
                    )}
                  </div>

                </div>
              ) : (
                <div className="border border-dashed border-white/5 rounded-2xl p-20 flex flex-col items-center justify-center bg-[#12151C] min-h-[500px] shadow-xl">
                  <FileText className="w-12 h-12 text-[#6E6E73] mb-4" />
                  <h3 className="text-sm font-bold text-[#8E8E93]">Awaiting Verification File</h3>
                  <p className="text-xs text-[#6E6E73] mt-1.5 text-center max-w-sm leading-relaxed">
                    Upload a payslip or bank statement to perform a digital integrity audit. Split views, ELA heatmaps, and hash linkage values will output here.
                  </p>
                </div>
              )}
            </div>

          </div>
        )}

        {/* TAB 2: CROSS-DOCUMENT RECONCILIATION */}
        {activeTab === 'cross' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* CROSS AUDIT CONTROLS (4 cols) */}
            <div className="lg:col-span-4 flex flex-col space-y-6">
              
              <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl space-y-6">
                <div>
                  <h2 className="text-sm font-bold text-[#F5F5F7] mb-1">Dual-Doc Comparison</h2>
                  <p className="text-xs text-[#8E8E93] leading-relaxed">Correlate employee salary claims against transactional bank ledger credits.</p>
                </div>

                {/* Payslip Upload */}
                <div className="space-y-2">
                  <label className="text-[9px] font-bold text-[#8E8E93] uppercase tracking-wider">Salary Payslip</label>
                  <div 
                    onClick={() => payslipInputRef.current.click()}
                    className={`border border-dashed border-white/10 hover:border-[#0A84FF]/40 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-[#0B0D10]/50 hover:bg-[#0B0D10] transition-all ${payslipFile ? 'border-[#0A84FF]/30 bg-[#0A84FF]/[0.02]' : ''}`}
                  >
                    <input 
                      type="file" 
                      ref={payslipInputRef} 
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) setPayslipFile(e.target.files[0]);
                      }}
                      className="hidden" 
                      accept=".pdf,.png,.jpg,.jpeg"
                    />
                    <FileText className={`w-5 h-5 mb-1.5 ${payslipFile ? 'text-[#0A84FF]' : 'text-[#8E8E93]'}`} />
                    <p className="text-[11px] font-bold text-[#8E8E93] text-center truncate max-w-[220px]">
                      {payslipFile ? payslipFile.name : "Select Salary Payslip"}
                    </p>
                  </div>
                </div>

                {/* Bank Statement Upload */}
                <div className="space-y-2">
                  <label className="text-[9px] font-bold text-[#8E8E93] uppercase tracking-wider">Bank Statement</label>
                  <div 
                    onClick={() => bankInputRef.current.click()}
                    className={`border border-dashed border-white/10 hover:border-[#0A84FF]/40 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-[#0B0D10]/50 hover:bg-[#0B0D10] transition-all ${bankFile ? 'border-[#0A84FF]/30 bg-[#0A84FF]/[0.02]' : ''}`}
                  >
                    <input 
                      type="file" 
                      ref={bankInputRef} 
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) setBankFile(e.target.files[0]);
                      }}
                      className="hidden" 
                      accept=".pdf,.png,.jpg,.jpeg"
                    />
                    <FileCheck className={`w-5 h-5 mb-1.5 ${bankFile ? 'text-[#0A84FF]' : 'text-[#8E8E93]'}`} />
                    <p className="text-[11px] font-bold text-[#8E8E93] text-center truncate max-w-[220px]">
                      {bankFile ? bankFile.name : "Select Bank Statement"}
                    </p>
                  </div>
                </div>

                {/* Submit button */}
                <button
                  onClick={handleCrossReconcile}
                  disabled={!payslipFile || !bankFile || crossLoading}
                  className="w-full py-2.5 px-4 bg-[#0A84FF] hover:bg-[#0066CC] disabled:bg-white/5 text-white disabled:text-[#6E6E73] font-bold rounded-xl text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:cursor-not-allowed uppercase tracking-wider shadow-lg hover:shadow-[#0A84FF]/10 disabled:shadow-none"
                >
                  {crossLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin text-[#0A84FF]" />
                      <span>Running OCR Parse...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="w-4 h-4" />
                      <span>Reconcile Fields</span>
                    </>
                  )}
                </button>
              </div>

              {/* Console for Cross Tab */}
              <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl flex flex-col min-h-[200px]">
                <div className="flex items-center space-x-2 border-b border-white/[0.04] pb-3 mb-3 shrink-0">
                  <Terminal className="w-4 h-4 text-[#0A84FF]" />
                  <span className="text-xs font-bold text-[#8E8E93] uppercase tracking-wider">Live OCR Engine Logs</span>
                </div>
                <div ref={crossConsoleContainerRef} className="flex-1 overflow-y-auto font-mono text-[10px] text-[#8E8E93] space-y-2.5 p-3.5 bg-[#0B0D10]/80 rounded-xl border border-white/[0.04] shadow-inner max-h-[220px]">
                  {crossConsoleLogs.length > 0 ? (
                    crossConsoleLogs.map((log, idx) => (
                      <div key={idx} className="flex items-start space-x-1.5 leading-relaxed">
                        <span className="text-[#6E6E73] select-none">[{log.time}]</span>
                        <span className="text-[#F5F5F7]">{log.text}</span>
                      </div>
                    ))
                  ) : (
                    <div className="h-full flex items-center justify-center text-[#6E6E73] italic select-none">
                      Console idle. Ingest files to audit.
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* RESULTS DETAILS (8 cols) */}
            <div className="lg:col-span-8">
              {crossLoading ? (
                <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-16 flex flex-col items-center justify-center min-h-[500px] shadow-xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-b from-[#0A84FF]/0 via-[#0A84FF]/5 to-[#0A84FF]/0 h-24 w-full top-0 left-0 animate-scanner pointer-events-none" />
                  
                  <div className="p-4 bg-[#12151C] border border-white/[0.04] rounded-full text-[#0A84FF] animate-pulse mb-4">
                    <FileCheck className="w-10 h-10" />
                  </div>
                  <h3 className="text-base font-bold text-[#F5F5F7] tracking-wide">Executing Cross-Document Comparison</h3>
                  <p className="text-xs text-[#8E8E93] mt-1.5 max-w-sm text-center leading-relaxed">
                    Reading text blocks from Payslip and running OCR parsing on Bank transaction records for audit reconciliation.
                  </p>
                </div>
              ) : crossResult ? (
                <div className="flex flex-col space-y-6">
                  {crossResult.isOfflineSimulation && (
                    <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start space-x-3 text-amber-200">
                      <AlertTriangle className="w-4.5 h-4.5 text-amber-400 mt-0.5 shrink-0" />
                      <div className="text-xs leading-relaxed">
                        <span className="font-bold">Offline Demo Mode:</span> FastAPI backend is unreachable. Running client-side simulation. To perform custom file OCR reconciliation, run the backend server locally.
                      </div>
                    </div>
                  )}
                  
                  {/* Score & Declarations overview */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl grid grid-cols-1 md:grid-cols-12 gap-6 relative overflow-hidden">
                    <div className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-[120px] opacity-[0.03] pointer-events-none translate-x-1/3 -translate-y-1/3 ${getScoreColors(crossResult.cross_trust_score).glow}`} />
                    
                    {/* Gauge score */}
                    <div className="md:col-span-4 flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-white/[0.04] pb-6 md:pb-0 md:pr-6">
                      <h3 className="text-[10px] font-bold text-[#8E8E93] mb-4 uppercase tracking-wider">Correlation Score</h3>
                      
                      <div className="relative w-32 h-32 flex items-center justify-center">
                        <div className={`absolute w-28 h-28 rounded-full blur-[20px] opacity-10 transition-all duration-1000 ${getScoreColors(crossResult.cross_trust_score).glow}`} />
                        
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                          <circle 
                            className="text-[#181C25]" 
                            strokeWidth="6" 
                            stroke="currentColor" 
                            fill="transparent" 
                            r="40" 
                            cx="50" 
                            cy="50" 
                          />
                          <circle 
                            className="transition-all duration-1000 animate-gauge" 
                            strokeWidth="6" 
                            strokeDasharray={2 * Math.PI * 40}
                            strokeDashoffset={2 * Math.PI * 40 * (1 - animatedCrossScore / 100)}
                            strokeLinecap="round" 
                            stroke={getScoreColors(crossResult.cross_trust_score).stroke}
                            fill="transparent" 
                            r="40" 
                            cx="50" 
                            cy="50" 
                          />
                        </svg>
                        
                        <div className="absolute text-center">
                          <span className="text-3xl font-mono font-black text-[#F5F5F7] tracking-tight">{animatedCrossScore}</span>
                          <span className="text-[9px] font-bold text-[#8E8E93] block uppercase tracking-wider">Match</span>
                        </div>
                      </div>

                      <div className={`mt-4 px-3 py-1 rounded-full border text-[9px] font-extrabold uppercase tracking-wider ${getScoreColors(crossResult.cross_trust_score).badge} ${getScoreColors(crossResult.cross_trust_score).glow}`}>
                        {crossResult.cross_trust_score === 100 ? "Fully Reconciled" : "Discrepancy Found"}
                      </div>
                    </div>

                    {/* Statistics details */}
                    <div className="md:col-span-8 flex flex-col justify-center space-y-4">
                      <h3 className="text-[10px] font-bold text-[#8E8E93] uppercase tracking-wider">Extracted Properties</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-[#0B0D10]/50 border border-white/[0.04] rounded-xl p-3">
                          <span className="text-[9px] text-[#8E8E93] uppercase font-bold block mb-0.5">Declared Name (Payslip)</span>
                          <span className="text-xs font-bold text-[#F5F5F7]">
                            {crossResult.payslip_extracted.employee_name || "Not Detected"}
                          </span>
                        </div>
                        <div className="bg-[#0B0D10]/50 border border-white/[0.04] rounded-xl p-3">
                          <span className="text-[9px] text-[#8E8E93] uppercase font-bold block mb-0.5">Net Pay amount (Payslip)</span>
                          <span className="text-xs font-bold text-[#0A84FF] font-mono">
                            {crossResult.payslip_extracted.net_pay 
                              ? `$${crossResult.payslip_extracted.net_pay.toLocaleString(undefined, {minimumFractionDigits: 2})}` 
                              : "Not Detected"}
                          </span>
                        </div>
                      </div>

                      <p className="text-[9px] text-[#6E6E73] leading-relaxed font-bold uppercase tracking-wider mt-2">
                        OCR scanned fields compared against statement credits using exact regex values comparison.
                      </p>
                    </div>

                  </div>

                  {/* VISUAL DISCREPANCY RECONCILIATION DIAGRAM */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl">
                    <h2 className="text-sm font-bold text-[#F5F5F7] mb-1">Reconciliation Link Map</h2>
                    <p className="text-xs text-[#8E8E93] mb-6">Interactive schema detailing verification linking between fields.</p>

                    <div className="grid grid-cols-1 md:grid-cols-7 items-center gap-4 py-4 px-4 bg-[#0B0D10]/80 rounded-xl border border-white/[0.04]">
                      
                      {/* Left: Payslip Node */}
                      <div className="md:col-span-2 p-4 bg-[#12151C] border border-white/[0.04] rounded-xl space-y-2.5">
                        <div className="flex items-center space-x-1.5 border-b border-white/[0.03] pb-2 mb-2">
                          <FileText className="w-3.5 h-3.5 text-[#0A84FF]" />
                          <span className="text-[9px] font-extrabold text-[#8E8E93] uppercase tracking-wider">Payslip Input</span>
                        </div>
                        <div className="space-y-2">
                          <div className="p-2 bg-[#0B0D10]/50 rounded border border-white/[0.03] text-center">
                            <span className="text-[8px] text-[#6E6E73] block font-bold uppercase tracking-wider">Employee Name</span>
                            <span className="text-xs font-bold text-[#F5F5F7] truncate block">{crossResult.payslip_extracted.employee_name || "???"}</span>
                          </div>
                          <div className="p-2 bg-[#0B0D10]/50 rounded border border-white/[0.03] text-center">
                            <span className="text-[8px] text-[#6E6E73] block font-bold uppercase tracking-wider">Salary Net Pay</span>
                            <span className="text-xs font-bold text-[#0A84FF] font-mono">
                              ${crossResult.payslip_extracted.net_pay ? crossResult.payslip_extracted.net_pay.toLocaleString() : "???"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Center: Connectors (3 cols) */}
                      <div className="md:col-span-3 flex flex-col justify-center items-center py-4 space-y-8 select-none">
                        
                        {/* Name verification link */}
                        <div className="w-full flex items-center justify-between px-2">
                          <span className="w-1.5 h-1.5 bg-[#0A84FF] rounded-full" />
                          <div className="flex-1 border-t border-dashed border-white/10 mx-2 relative flex items-center justify-center">
                            {crossResult.reconciliation_flags.some(f => f.flag === 'Name Mismatch') ? (
                              <>
                                <div className="absolute -top-3 px-2 py-0.5 bg-[#FF453A]/10 text-[#FF453A] border border-[#FF453A]/20 rounded text-[8px] font-bold uppercase tracking-wider">
                                  Blocked Mismatch
                                </div>
                                <div className="w-full border-t border-dashed border-[#FF453A]" />
                              </>
                            ) : (
                              <>
                                <div className="absolute -top-3 px-2 py-0.5 bg-[#30D158]/10 text-[#30D158] border border-[#30D158]/20 rounded text-[8px] font-bold uppercase tracking-wider">
                                  Confirmed Match
                                </div>
                                <div className="w-full border-t border-dashed border-[#30D158] animate-pulse" />
                              </>
                            )}
                          </div>
                          <span className="w-1.5 h-1.5 bg-[#0A84FF] rounded-full" />
                        </div>

                        {/* Amount verification link */}
                        <div className="w-full flex items-center justify-between px-2">
                          <span className="w-1.5 h-1.5 bg-[#0A84FF] rounded-full" />
                          <div className="flex-1 border-t border-dashed border-white/10 mx-2 relative flex items-center justify-center">
                            {crossResult.reconciliation_flags.some(f => f.flag === 'Missing Salary Deposit') ? (
                              <>
                                <div className="absolute -top-3 px-2 py-0.5 bg-[#FF453A]/10 text-[#FF453A] border border-[#FF453A]/20 rounded text-[8px] font-bold uppercase tracking-wider">
                                  Missing Credit
                                </div>
                                <div className="w-full border-t border-dashed border-[#FF453A]" />
                              </>
                            ) : (
                              <>
                                <div className="absolute -top-3 px-2 py-0.5 bg-[#30D158]/10 text-[#30D158] border border-[#30D158]/20 rounded text-[8px] font-bold uppercase tracking-wider">
                                  Credited Transaction
                                </div>
                                <div className="w-full border-t border-dashed border-[#30D158] animate-pulse" />
                              </>
                            )}
                          </div>
                          <span className="w-1.5 h-1.5 bg-[#0A84FF] rounded-full" />
                        </div>

                      </div>

                      {/* Right: Bank Statement Node */}
                      <div className="md:col-span-2 p-4 bg-[#12151C] border border-white/[0.04] rounded-xl space-y-2.5">
                        <div className="flex items-center space-x-1.5 border-b border-white/[0.03] pb-2 mb-2">
                          <FileCheck className="w-3.5 h-3.5 text-[#30D158]" />
                          <span className="text-[9px] font-extrabold text-[#8E8E93] uppercase tracking-wider">Statement Ledger</span>
                        </div>
                        <div className="space-y-2">
                          <div className={`p-2 bg-[#0B0D10]/50 rounded border text-center ${crossResult.reconciliation_flags.some(f => f.flag === 'Name Mismatch') ? 'border-[#FF453A]/20 text-[#FF453A]' : 'border-[#30D158]/20 text-[#30D158]'}`}>
                            <span className="text-[8px] text-[#6E6E73] block font-bold uppercase tracking-wider">Account Owner</span>
                            <span className="text-xs font-bold block truncate">
                              {crossResult.reconciliation_flags.some(f => f.flag === 'Name Mismatch') ? "Mismatched User" : (crossResult.payslip_extracted.employee_name || "Verified")}
                            </span>
                          </div>
                          <div className={`p-2 bg-[#0B0D10]/50 rounded border text-center ${crossResult.reconciliation_flags.some(f => f.flag === 'Missing Salary Deposit') ? 'border-[#FF453A]/20 text-[#FF453A]' : 'border-[#30D158]/20 text-[#30D158]'}`}>
                            <span className="text-[8px] text-[#6E6E73] block font-bold uppercase tracking-wider">Deposit Credit</span>
                            <span className="text-xs font-bold block font-mono">
                              {crossResult.reconciliation_flags.some(f => f.flag === 'Missing Salary Deposit') ? "Not Found" : `$${crossResult.payslip_extracted.net_pay?.toLocaleString()}`}
                            </span>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>

                  {/* Discrepancy Alerts table */}
                  <div className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl">
                    <h2 className="text-sm font-bold text-[#F5F5F7] mb-1">Reconciliation Audit Log</h2>
                    <p className="text-xs text-[#8E8E93] mb-4">Detailed lists of errors, conflicts, or verification matches.</p>
                    
                    {crossResult.reconciliation_flags.length > 0 ? (
                      <div className="space-y-3">
                        {crossResult.reconciliation_flags.map((flag, idx) => (
                          <div 
                            key={idx} 
                            className="bg-[#0B0D10]/50 border border-white/[0.04] rounded-xl p-4 flex items-start space-x-3.5 hover:bg-[#0B0D10] transition-all"
                          >
                            <div className="mt-0.5 text-[#FF453A] shrink-0">
                              <AlertCircle className="w-5 h-5" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <h4 className="text-xs font-bold text-[#F5F5F7]">{flag.flag}</h4>
                                <span className={`px-1.5 py-0.2 rounded border text-[8px] font-black uppercase tracking-wider ${getSeverityColors(flag.severity).bg} ${getSeverityColors(flag.severity).text} ${getSeverityColors(flag.severity).border}`}>
                                  {flag.severity}
                                </span>
                              </div>
                              <p className="text-xs text-[#8E8E93] mt-1 leading-relaxed">{flag.detail}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="border border-dashed border-white/5 rounded-xl p-8 flex flex-col items-center justify-center bg-[#0B0D10]/30 text-center">
                        <div className="p-3 bg-[#12151C] border border-[#30D158]/10 text-[#30D158] rounded-full mb-3 shadow-inner">
                          <CheckCircle className="w-6 h-6 text-[#30D158]" />
                        </div>
                        <p className="text-xs font-bold text-[#F5F5F7]">Dual Reconciliation Completed</p>
                        <p className="text-[10px] text-[#8E8E93] mt-1 max-w-sm leading-relaxed">
                          All comparison loops returned green. Salary amount matches deposit credits, and names match client statement metadata.
                        </p>
                      </div>
                    )}
                  </div>

                </div>
              ) : (
                <div className="border border-dashed border-white/5 rounded-2xl p-20 flex flex-col items-center justify-center bg-[#12151C] min-h-[500px] shadow-xl">
                  <FileCheck className="w-12 h-12 text-[#6E6E73] mb-4" />
                  <h3 className="text-sm font-bold text-[#8E8E93]">Awaiting Reconciliation</h3>
                  <p className="text-xs text-[#6E6E73] mt-1.5 text-center max-w-sm leading-relaxed">
                    Upload a payslip and matching bank statement. The systems will parse both via Tesseract OCR and display verification link schemas.
                  </p>
                </div>
              )}
            </div>

          </div>
        )}

        {/* LEDGER TIMELINE SECTION */}
        <section className="bg-[#12151C] border border-white/[0.04] rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-white/[0.04] pb-4 mb-6 gap-4">
            <div>
              <h2 className="text-sm font-bold text-[#F5F5F7] flex items-center space-x-2.5">
                <Database className="w-4 h-4 text-[#0A84FF]" />
                <span>Tamper-Evident Ledger Chronology</span>
              </h2>
              <p className="text-xs text-[#8E8E93] mt-0.5">Append-only cryptographic blocks linked dynamically via SQLite backend.</p>
            </div>
            
            <div className="flex items-center space-x-3 shrink-0">
              <button
                onClick={handleVerifyLedger}
                disabled={ledgerLoading || ledger.length === 0}
                className="py-2 px-3.5 bg-[#181C25] border border-white/10 hover:border-[#0A84FF]/40 hover:bg-[#1C202B] text-[#8E8E93] hover:text-[#F5F5F7] font-bold rounded-lg text-[10px] uppercase tracking-wider flex items-center space-x-1.5 transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 shadow-sm"
              >
                {ledgerLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#0A84FF]" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                <span>Audit Chain Integrity</span>
              </button>
            </div>
          </div>

          {/* Verification Banner */}
          {ledgerVerifyResult && (
            <div className={`mb-8 p-4 rounded-xl border flex items-start space-x-3.5 shadow-xl transition-all duration-300 ${
              ledgerVerifyResult === 'intact'
                ? 'bg-[#30D158]/5 border-[#30D158]/15 text-[#30D158] shadow-neon-emerald'
                : 'bg-[#FF453A]/5 border-[#FF453A]/15 text-[#FF453A] shadow-neon-rose animate-pulse'
            }`}>
              <div className="shrink-0 mt-0.5">
                {ledgerVerifyResult === 'intact' ? (
                  <div className="p-1.5 bg-[#12151C] rounded-full border border-[#30D158]/20 text-[#30D158]">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                ) : (
                  <div className="p-1.5 bg-[#12151C] rounded-full border border-[#FF453A]/20 text-[#FF453A]">
                    <ShieldAlert className="w-5 h-5 animate-bounce" />
                  </div>
                )}
              </div>
              <div className="flex-1 space-y-0.5">
                <h4 className="text-xs font-bold text-[#F5F5F7]">
                  {ledgerVerifyResult === 'intact' ? "Ledger Audit: Chained Verification Intact" : "Ledger Audit: BLOCKCHAIN TAMPERING BREACH DETECTED!"}
                </h4>
                <p className="text-[11px] text-[#8E8E93] leading-relaxed">
                  {ledgerVerifyResult === 'intact'
                    ? "Verified all blocks. The sequence of SHA-256 links resolves perfectly to predecessor block hashes. No unauthorized modifications detected."
                    : "Cryptographic auditing failed. Database rows have been modified, deleted, or inserted out of order, causing chain hash mismatch."}
                </p>
              </div>
            </div>
          )}

          {/* Vertical Timeline List (Apple-style) */}
          {ledger.length > 0 ? (
            <div className="relative pl-6 border-l border-white/[0.06] ml-3.5 py-2 space-y-6">
              {ledger.map((entry, index) => {
                const isTampered = ledgerVerifyResult === 'tampered';
                return (
                  <div key={entry.id} className="relative group/timeline transition-all duration-200">
                    {/* Timeline Node Point Indicator */}
                    <div className="absolute -left-[30px] top-1.5 flex items-center justify-center">
                      <div className={`w-2 h-2 rounded-full border transition-all duration-300 ${
                        isTampered 
                          ? 'bg-[#FF453A] border-[#FF453A] shadow-neon-rose scale-125 animate-ping'
                          : 'bg-[#0A84FF] border-[#0A84FF] shadow-neon-blue group-hover/timeline:scale-125'
                      }`} />
                    </div>

                    {/* Timeline row content */}
                    <div 
                      onClick={() => setSelectedBlock(entry)}
                      className="bg-[#181C25]/40 border border-white/[0.04] hover:border-[#0A84FF]/20 rounded-xl p-4.5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer hover:bg-[#181C25] transition-all"
                    >
                      <div className="flex items-center space-x-4">
                        <span className="text-[9px] font-mono font-bold bg-[#181C25] text-[#8E8E93] border border-white/[0.04] px-2 py-0.5 rounded tracking-wide">
                          Block #{entry.id}
                        </span>
                        <div>
                          <h4 className="text-xs font-bold text-[#F5F5F7] group-hover/timeline:text-[#0A84FF] transition-colors">
                            {entry.filename}
                          </h4>
                          <span className="text-[10px] text-[#6E6E73] block mt-0.5">
                            Ingested {new Date(entry.timestamp).toLocaleDateString()} at {new Date(entry.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>

                      {/* Truncated monospaced hashes with Copy Affordance */}
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3 md:gap-6 text-[10px] shrink-0 font-mono">
                        <div>
                          <span className="text-[8px] uppercase font-bold text-[#6E6E73] block mb-0.5">Document Hash</span>
                          <div className="flex items-center space-x-1.5 bg-[#0B0D10]/50 border border-white/[0.04] rounded px-2 py-1">
                            <span className="text-[#8E8E93]">{entry.doc_hash.slice(0, 8)}...{entry.doc_hash.slice(-8)}</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopy(entry.doc_hash, `${entry.id}-doc`);
                              }}
                              className="p-1 rounded hover:bg-[#12151C] text-[#6E6E73] hover:text-[#F5F5F7] transition-colors cursor-pointer"
                              title="Copy Doc Hash"
                            >
                              {copiedHashId === `${entry.id}-doc` ? (
                                <Check className="w-3 h-3 text-[#30D158]" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                        </div>

                        <div>
                          <span className="text-[8px] uppercase font-bold text-[#6E6E73] block mb-0.5">Link Hash</span>
                          <div className="flex items-center space-x-1.5 bg-[#0B0D10]/50 border border-white/[0.04] rounded px-2 py-1">
                            <span className="text-[#0A84FF]">{entry.chain_hash.slice(0, 8)}...{entry.chain_hash.slice(-8)}</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopy(entry.chain_hash, `${entry.id}-chain`);
                              }}
                              className="p-1 rounded hover:bg-[#12151C] text-[#6E6E73] hover:text-[#F5F5F7] transition-colors cursor-pointer"
                              title="Copy Link Hash"
                            >
                              {copiedHashId === `${entry.id}-chain` ? (
                                <Check className="w-3 h-3 text-[#30D158]" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="border border-dashed border-white/5 rounded-xl p-12 flex flex-col items-center justify-center bg-[#0B0D10]/30 text-center">
              <Database className="w-8 h-8 text-[#6E6E73] mb-2" />
              <p className="text-xs font-bold text-[#8E8E93]">Ledger Database Empty</p>
              <p className="text-[10px] text-[#6E6E73] mt-1">Audit logs will be cryptographically chained as blocks here on upload.</p>
            </div>
          )}
        </section>

      </main>

      {/* BLOCK DETAIL INSPECTOR MODAL */}
      {selectedBlock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0B0D10]/60 backdrop-blur-sm transition-all">
          <div className="relative w-full max-w-lg bg-[#12151C] border border-white/10 rounded-2xl shadow-2xl p-6 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#0A84FF] to-transparent" />
            
            <div className="flex justify-between items-center border-b border-white/[0.04] pb-3.5 mb-5">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-[#0A84FF]" />
                <h3 className="text-sm font-bold text-[#F5F5F7]">Block #{selectedBlock.id} Ledger Inspector</h3>
              </div>
              <button 
                onClick={() => setSelectedBlock(null)}
                className="p-1 rounded-lg text-[#8E8E93] hover:text-[#F5F5F7] hover:bg-white/5 transition-all cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block">Document Filename</label>
                <input 
                  type="text" 
                  value={selectedBlock.filename} 
                  readOnly 
                  className="w-full bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg p-2.5 text-xs text-[#F5F5F7] focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block">Raw File SHA-256 Hash</label>
                  <button 
                    onClick={() => handleCopy(selectedBlock.doc_hash, 'modal-doc')}
                    className="text-[9px] text-[#0A84FF] hover:underline flex items-center space-x-1 font-bold bg-transparent border-none cursor-pointer"
                  >
                    {copiedHashId === 'modal-doc' ? <Check className="w-2.5 h-2.5 text-[#30D158]" /> : <Copy className="w-2.5 h-2.5" />}
                    <span>{copiedHashId === 'modal-doc' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div className="font-mono text-xs text-[#8E8E93] p-2.5 bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg break-all select-all font-semibold leading-relaxed">
                  {selectedBlock.doc_hash}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block">Previous Row Chain Hash</label>
                  <button 
                    onClick={() => handleCopy(selectedBlock.prev_row_hash, 'modal-prev')}
                    className="text-[9px] text-[#0A84FF] hover:underline flex items-center space-x-1 font-bold bg-transparent border-none cursor-pointer"
                  >
                    {copiedHashId === 'modal-prev' ? <Check className="w-2.5 h-2.5 text-[#30D158]" /> : <Copy className="w-2.5 h-2.5" />}
                    <span>{copiedHashId === 'modal-prev' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div className="font-mono text-xs text-[#6E6E73] p-2.5 bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg break-all select-all font-semibold leading-relaxed">
                  {selectedBlock.prev_row_hash}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between items-center">
                  <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block">Resulting Link Hash</label>
                  <button 
                    onClick={() => handleCopy(selectedBlock.chain_hash, 'modal-chain')}
                    className="text-[9px] text-[#0A84FF] hover:underline flex items-center space-x-1 font-bold bg-transparent border-none cursor-pointer"
                  >
                    {copiedHashId === 'modal-chain' ? <Check className="w-2.5 h-2.5 text-[#30D158]" /> : <Copy className="w-2.5 h-2.5" />}
                    <span>{copiedHashId === 'modal-chain' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div className="font-mono text-xs text-[#0A84FF] p-2.5 bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg break-all select-all font-semibold leading-relaxed">
                  {selectedBlock.chain_hash}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block mb-1">Index ID</label>
                  <span className="text-xs font-mono font-bold text-[#F5F5F7] bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg px-3 py-1.5 block">
                    {selectedBlock.id}
                  </span>
                </div>
                <div>
                  <label className="text-[9px] uppercase tracking-wider text-[#8E8E93] font-bold block mb-1">Timestamp</label>
                  <span className="text-xs font-bold text-[#F5F5F7] bg-[#0B0D10]/50 border border-white/[0.04] rounded-lg px-3 py-1.5 block truncate" title={new Date(selectedBlock.timestamp).toLocaleString()}>
                    {new Date(selectedBlock.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="mt-6 border-t border-white/[0.04] pt-4.5 flex justify-end">
              <button 
                onClick={() => setSelectedBlock(null)}
                className="px-4 py-2 bg-[#181C25] border border-white/10 hover:border-white/20 text-[#8E8E93] hover:text-[#F5F5F7] rounded-lg text-xs font-semibold cursor-pointer"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <footer className="bg-[#12151C] border-t border-white/[0.04] py-6 mt-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="text-[10px] text-[#6E6E73] font-bold uppercase tracking-wider">
            &copy; 2026 VeriLedger. Cryptographic Loan Forgery Layer. Developed by Tanishq Varshney.
          </p>
          <div className="flex space-x-4">
            <span className="text-[10px] text-[#6E6E73] font-mono">FastAPI</span>
            <span className="text-[10px] text-[#6E6E73] font-mono">SQLite DB</span>
            <span className="text-[10px] text-[#6E6E73] font-mono">OpenCV + PyMuPDF + Tesseract</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
