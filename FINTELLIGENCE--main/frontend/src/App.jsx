import React, { useState } from 'react'
import FundFlowGraph from './components/Graph/FundFlowGraph'
import AnimatedTrail from './components/Graph/AnimatedTrail'
import CaseTimeline from './components/Timeline/CaseTimeline'
import BeneficiaryPanel from './components/Intelligence/BeneficiaryPanel'
import RiskHeatMap from './components/Intelligence/RiskHeatMap'
import './App.css'

function App() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [panelVisible, setPanelVisible] = useState(false);

  const handleNodeClick = (node) => {
    setSelectedNode(node.data);
    setPanelVisible(true);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>FINTELLIGENCE - Graph Intelligence Layer</h1>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div style={{ flex: 2 }}>
          <h2 style={{ marginBottom: '10px' }}>Fund Flow Graph</h2>
          <FundFlowGraph caseId="2220d98a-ec23-409b-b2fc-4713c3c0ba8a" onNodeClick={handleNodeClick} />
        </div>
        
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <RiskHeatMap />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 2 }}>
          <AnimatedTrail caseId="2220d98a-ec23-409b-b2fc-4713c3c0ba8a" />
        </div>
        
        <div style={{ flex: 1 }}>
          <CaseTimeline transactions={[]} />
        </div>
      </div>

      <BeneficiaryPanel 
        visible={panelVisible} 
        onClose={() => setPanelVisible(false)} 
        nodeData={selectedNode} 
      />
    </div>
  )
}

export default App
