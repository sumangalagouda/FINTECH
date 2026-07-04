import { useRef, useState } from 'react';
import { UploadCloud, FileText, FolderPlus, FolderOpen } from 'lucide-react';

export default function Upload({ api, cases, refreshCases, selectedCaseId, setSelectedCaseId, setNotice, setActiveView, setCaseViewMode }) {
  const inputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [popupMsg, setPopupMsg] = useState('');
  const [uploadedCaseId, setUploadedCaseId] = useState(null);
  
  // Two strict modes: 'new' or 'existing'
  const [mode, setMode] = useState('new');
  const [targetCaseId, setTargetCaseId] = useState(selectedCaseId || '');

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  };

  const upload = async () => {
    if (!files.length) {
      setNotice('Choose at least one PDF, CSV, spreadsheet, or image before analyzing.');
      return;
    }
    
    if (mode === 'existing' && !targetCaseId) {
      setNotice('Please select an existing case to append to.');
      return;
    }

    setBusy(true);
    setNotice('');
    try {
      const form = new FormData();
      files.forEach(file => {
        form.append('files', file);
      });
      
      if (mode === 'existing') {
        form.append('case_id', targetCaseId);
      }
      
      const result = await api('/upload/', { method: 'POST', body: form });
      
      await refreshCases(result.case_id);
      setUploadedCaseId(result.case_id);
      
      setActiveView('cases');
      setCaseViewMode('detail');
      setPopupMsg(`Analyzed statements successfully. Case ${result.case_id.slice(0, 8)} updated.`);
      setTimeout(() => setPopupMsg(''), 5000);
      setNotice('');
      
      // Reset after upload
      setFiles([]);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="upload-view" style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '40px' }}>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '32px' }}>
        <button 
          onClick={() => setMode('new')}
          style={{
            flex: 1, padding: '24px', borderRadius: '12px', border: mode === 'new' ? '2px solid #3b82f6' : '1px solid #e2e8f0',
            background: mode === 'new' ? '#eff6ff' : 'white', cursor: 'pointer', display: 'flex', flexDirection: 'column',
            alignItems: 'center', gap: '12px'
          }}
        >
          <FolderPlus size={32} color={mode === 'new' ? '#3b82f6' : '#64748b'} />
          <strong style={{ color: mode === 'new' ? '#1e3a8a' : '#334155', fontSize: '16px' }}>Create New Case</strong>
          <span style={{ color: '#64748b', fontSize: '13px' }}>Upload statements to start a new investigation</span>
        </button>
        
        <button 
          onClick={() => setMode('existing')}
          style={{
            flex: 1, padding: '24px', borderRadius: '12px', border: mode === 'existing' ? '2px solid #3b82f6' : '1px solid #e2e8f0',
            background: mode === 'existing' ? '#eff6ff' : 'white', cursor: 'pointer', display: 'flex', flexDirection: 'column',
            alignItems: 'center', gap: '12px'
          }}
        >
          <FolderOpen size={32} color={mode === 'existing' ? '#3b82f6' : '#64748b'} />
          <strong style={{ color: mode === 'existing' ? '#1e3a8a' : '#334155', fontSize: '16px' }}>Add to Existing Case</strong>
          <span style={{ color: '#64748b', fontSize: '13px' }}>Append statements to an ongoing investigation</span>
        </button>
      </div>

      {mode === 'existing' && (
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#334155' }}>
            Select Target Case
          </label>
          <select 
            value={targetCaseId}
            onChange={(e) => setTargetCaseId(e.target.value)}
            style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '15px' }}
          >
            <option value="">-- Choose a case --</option>
            {cases.map(c => (
              <option key={c.id} value={c.id}>
                {c.title} ({c.id.slice(0, 8)})
              </option>
            ))}
          </select>
        </div>
      )}

      <button className="dropzone" type="button" onClick={() => inputRef.current?.click()} style={{ minHeight: '200px' }}>
        <UploadCloud size={48} style={{ marginBottom: '16px' }} />
        <strong>
          {files.length > 0 
            ? `${files.length} file(s) selected` 
            : 'Drop statements here, or click to browse'}
        </strong>
        {files.length > 0 && (
          <div style={{ marginTop: '12px', fontSize: '13px', color: '#64748b' }}>
            {files.map(f => f.name).join(', ')}
          </div>
        )}
        <span style={{ marginTop: '16px' }}>PDF / CSV / XLSX / JPG / PNG</span>
      </button>
      
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.csv,.xls,.xlsx,.png,.jpg,.jpeg"
        hidden
        onChange={handleFileSelect}
      />
      
      <div className="upload-actions" style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', marginTop: '32px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <button 
            className="primary-button" 
            onClick={upload} 
            disabled={busy || files.length === 0 || (mode === 'existing' && !targetCaseId)} 
            type="button"
            style={{ padding: '12px 32px', fontSize: '16px' }}
          >
            {busy ? 'Analyzing statements...' : 'Analyze statements'}
          </button>
        </div>
      </div>
      
      {popupMsg && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(255, 255, 255, 0.4)', backdropFilter: 'blur(8px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', border: '1px solid var(--success)', color: 'var(--success)', padding: '32px 48px', borderRadius: '12px', boxShadow: '0 24px 48px rgba(0,0,0,0.1)', fontWeight: '600', fontSize: '18px', textAlign: 'center', maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '24px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            {popupMsg}
          </div>
        </div>
      )}
    </section>
  );
}
