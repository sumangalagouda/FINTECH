import { useState, useEffect } from 'react';
import { FileText, Download, Briefcase, FileCheck } from 'lucide-react';

export default function Reports({ api, cases, selectedCaseId, selectedCase }) {
  const [busy, setBusy] = useState(false);
  const [sioDecision, setSioDecision] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  
  const fetchEvidence = async () => {
    if (!selectedCaseId) return;
    try {
      const data = await api(`/evidence/${selectedCaseId}`);
      // Filter for items that are documents/reports generated
      const docs = data.filter(item => 
        ['report', 'fir', 'closing_document'].includes(item.item_type)
      );
      setEvidenceList(docs);
    } catch (err) {
      console.error('Failed to fetch evidence', err);
    }
  };

  useEffect(() => {
    const fetchDecision = async () => {
      if (!selectedCaseId) return;
      try {
        const res = await api(`/cases/${selectedCaseId}/sio-decision`);
        setSioDecision(res);
      } catch (err) {
        console.error('Failed to fetch SIO decision', err);
      }
    };
    fetchDecision();
    fetchEvidence();
  }, [selectedCaseId]);

  const downloadFile = async (url, filename) => {
    setBusy(true);
    try {
      const response = await fetch('/api' + url, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('fintelligence_token')}` }
      });
      if (!response.ok) throw new Error('Failed to download report');
      
      const contentType = response.headers.get('content-type') || '';
      let finalFilename = filename;
      
      // If we are getting the html fallback instead of PDF, fix extension
      if (contentType.includes('text/html') && finalFilename.endsWith('.pdf')) {
          finalFilename = finalFilename.replace('.pdf', '.html');
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = finalFilename;
      link.click();
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      alert('Error downloading file: ' + e.message);
    } finally {
      setBusy(false);
    }
  };

  const generateFir = async () => {
    setBusy(true);
    try {
      const response = await fetch(`/api/reports/fir-draft/${selectedCaseId}`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('fintelligence_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({}) // password is no longer required here if SIO Action exists
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to generate FIR');
      }
      // Trigger download immediately
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `FIR_Draft_${selectedCaseId.slice(0, 8)}.pdf`;
      link.click();
      URL.revokeObjectURL(objectUrl);
      
      // Refresh list to show it in the table
      await fetchEvidence();
    } catch (e) {
      alert('Error generating FIR: ' + e.message);
    } finally {
      setBusy(false);
    }
  };

  const getIcon = (type) => {
    if (type === 'fir') return <Briefcase size={15} />;
    if (type === 'closing_document') return <FileCheck size={15} />;
    return <FileText size={15} />;
  };
  
  const getLabel = (type) => {
    if (type === 'fir') return "FIR Draft";
    if (type === 'closing_document') return "Case Closure Report";
    return "Investigation Report";
  };

  return (
    <section className="panel stack">

      {sioDecision && sioDecision.has_action && (
        <div style={{ marginBottom: '16px', padding: '16px', background: '#f8fafc', borderRadius: 8 }}>
          <h3 style={{ marginTop: 0 }}>SR. IO DECISION RECORD</h3>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div><strong>Decision:</strong> {sioDecision.decision}</div>
            <div><strong>Authority:</strong> {sioDecision.authority || '-'}</div>
            <div><strong>IPC Sections:</strong> {(sioDecision.ipc_sections || []).join(', ') || '-'}</div>
            <div style={{ flexBasis: '100%' }}><strong>Remarks:</strong> {sioDecision.remarks || '-'}</div>
            <div><strong>Signed by:</strong> {sioDecision.signed_by_name}</div>
            <div><strong>Signed at:</strong> {sioDecision.signed_at ? new Date(sioDecision.signed_at).toLocaleString() : '-'}</div>
            <div><strong>Signature:</strong> {sioDecision.signature_hash?.substring(0, 20)}...</div>
            <div><strong>Override:</strong> {sioDecision.is_override ? 'Yes' : 'No'}</div>
          </div>
          
          {sioDecision.decision === 'recommend_fir' && !evidenceList.find(e => e.item_type === 'fir') && (
            <div style={{ marginTop: 12 }}>
              <button className="dark-button" onClick={generateFir} disabled={busy}>
                <Download size={14} /> GENERATE & DOWNLOAD FIR DRAFT
              </button>
            </div>
          )}
        </div>
      )}

      <div>
        <p className="subcopy">Generated PDF investigation packets: case summary, detector results, money trail, and final closure docs.</p>
      </div>
      <div className="table-frame">
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Date Generated</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {evidenceList.map(item => {
              const filename = item.file_path.split(/[\/\\]/).pop();
              return (
                <tr key={item.id}>
                  <td>{getIcon(item.item_type)} <span style={{marginLeft: '6px'}}>{getLabel(item.item_type)}</span></td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td>Available</td>
                  <td>
                    <button className="link-button" onClick={() => downloadFile(`/evidence/${item.id}/download`, filename)} disabled={busy} type="button">
                      <Download size={14} /> {busy ? 'Downloading' : 'Download'}
                    </button>
                  </td>
                </tr>
              )
            })}
            {evidenceList.length === 0 && (
               <tr>
                 <td colSpan="4" style={{textAlign: 'center', color: '#64748b'}}>No documents have been generated for this case yet.</td>
               </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
