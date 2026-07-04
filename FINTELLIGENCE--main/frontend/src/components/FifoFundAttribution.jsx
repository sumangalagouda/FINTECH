import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Layers, ArrowRight, Waypoints } from 'lucide-react';

const formatMoney = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0));
const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value).slice(0, 10) : date.toISOString().slice(0, 10);
};

// Recursive component to render the trail branches
function BranchNode({ node }) {
  const [expanded, setExpanded] = useState(true);
  
  if (!node) return null;
  
  return (
    <div style={{ marginLeft: node.hop === 1 ? '0px' : '24px', position: 'relative', marginTop: '12px' }}>
      {/* Branch line for indentation */}
      {node.hop > 1 && (
        <div style={{ position: 'absolute', left: '-12px', top: '16px', bottom: '0', width: '2px', background: '#e2e8f0' }} />
      )}
      
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', cursor: node.branches?.length ? 'pointer' : 'default', transition: 'background 0.2s', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: '#f8fafc', padding: '6px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <ArrowRight size={16} color="#64748b" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 'bold', color: '#0f172a', fontSize: '15px' }}>{formatMoney(node.attributed_amount)}</span>
              <span style={{ color: '#94a3b8' }}>→</span>
              <span style={{ fontWeight: '600', color: '#334155', fontSize: '14px', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px' }}>{node.account}</span>
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', display: 'flex', gap: '12px' }}>
              <span>{formatDate(node.date)}</span>
              <span>• held {node.time_held_human}</span>
            </div>
          </div>
        </div>
        {node.branches?.length > 0 && (
          <div style={{ color: '#94a3b8' }}>
            {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        )}
      </div>

      {expanded && node.branches && node.branches.length > 0 && (
        <div style={{ marginTop: '8px' }}>
          {node.branches.map((branch, idx) => (
            <BranchNode key={idx} node={branch} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FifoFundAttribution({ api, caseId, selectedAccountId, uniqueAccounts, onAccountSelect }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!api || !caseId || !selectedAccountId) return;
    
    let alive = true;
    setIsLoading(true);
    
    // Call our new trail reconstruction endpoint
    api('/graph/reconstruct-trail', {
      method: 'POST',
      body: JSON.stringify({ account_id: selectedAccountId, case_id: caseId })
    }).then(res => {
      if (alive) {
        setData(res || null);
      }
    }).catch(err => {
      console.error(err);
      if (alive) setData(null);
    }).finally(() => {
      if (alive) setIsLoading(false);
    });

    return () => { alive = false; };
  }, [api, caseId, selectedAccountId]);

  return (
    <div className="panel" style={{ padding: '24px', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <span className="eyebrow" style={{ color: '#64748b', fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.05em' }}>FORENSIC ACCOUNTING</span>
          <h3 style={{ margin: '4px 0 0 0', fontSize: '20px', color: '#0f172a' }}>Money Trail Analysis</h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#64748b' }}>
            Trace suspicious inflows down the branching dispersal chain.
          </p>
        </div>
        
        {/* Account Selector */}
        <select 
          value={selectedAccountId || ''}
          onChange={(e) => onAccountSelect(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none', background: '#f8fafc', color: '#0f172a', fontWeight: '500', minWidth: '200px' }}
        >
          {uniqueAccounts.map(acc => (
            <option key={acc} value={acc}>{acc}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>Reconstructing branched money trail...</div>
      ) : !data || !data.destinations || data.destinations.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px', border: '1px dashed #e2e8f0' }}>
          No branched suspicious money trail available for the selected account.
        </div>
      ) : (
        <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '24px', border: '1px solid #e2e8f0' }}>
          {/* Seed Summary */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '24px', paddingBottom: '24px', borderBottom: '1px dashed #cbd5e1' }}>
            <div style={{ background: '#fee2e2', color: '#ef4444', padding: '12px', borderRadius: '12px' }}>
              <Waypoints size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '14px', color: '#64748b', fontWeight: '500' }}>
                  Suspicious Inflow Seed ({data.seed_detector})
                </div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#ef4444' }}>
                  {data.outflow_ratio}% Depleted
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginTop: '4px' }}>
                <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#0f172a' }}>{formatMoney(data.suspicious_inflow_amount)}</span>
                <span style={{ fontSize: '15px', color: '#64748b', fontWeight: '500' }}>into {data.seed_account}</span>
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '8px', display: 'flex', gap: '16px' }}>
                <span>{formatMoney(data.attributed_outflow_amount)} traced downstream</span>
                <span>• dispersed over {data.depletion_duration}</span>
              </div>
            </div>
          </div>
          
          {/* Branching Tree */}
          <div style={{ paddingLeft: '8px' }}>
             {data.destinations.map((dest, idx) => (
               <BranchNode key={idx} node={dest} />
             ))}
          </div>
        </div>
      )}
    </div>
  );
}
