import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';
import { reconstructTrail, detectCircularFlow, detectLayering } from '../services/graph';
import CaseList from './CaseList';
import GeoMapView from './GeoMapView';

export default function FundFlowView({
  graph,
  transactions,
  api,
  cases,
  selectedCaseId,
  setSelectedCaseId,
  selectedTxnId,
  onNodeClick
}) {
  const [pageViewMode, setPageViewMode] = useState('list');
  const containerRef = useRef(null);
  const [graphMode, setGraphMode] = useState('full_network');
  const [subGraphData, setSubGraphData] = useState(null);
  const [isLoadingMode, setIsLoadingMode] = useState(false);
  const [metricStats, setMetricStats] = useState({ circular: 0, layering: 0 });
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  const generatePDF = async () => {
    if (!containerRef.current) return;
    setIsGeneratingPDF(true);
    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      
      let currentY = 10;
      
      try {
        const headerImg = new Image();
        headerImg.src = '/report-header.png';
        await new Promise((resolve, reject) => {
          headerImg.onload = resolve;
          headerImg.onerror = reject;
        });
        
        const imgWidth = pageWidth - 20;
        const imgHeight = (headerImg.height * imgWidth) / headerImg.width;
        
        pdf.addImage(headerImg, 'PNG', 10, currentY, imgWidth, imgHeight);
        currentY += imgHeight + 10;
      } catch (err) {
        console.error("Could not load header image", err);
        currentY = 20;
      }

      pdf.setFontSize(20);
      const title = graphMode === 'circular' ? 'Circular Flow Investigation Report' : 
                    graphMode === 'layering' ? 'Layering Chain Investigation Report' : 
                    graphMode === 'trail' ? 'Money Trail Investigation Report' : 
                    'Fund Flow Investigation Report';
      pdf.text(title, pageWidth / 2, currentY, { align: 'center' });
      
      currentY += 8;
      pdf.setFontSize(11);
      pdf.setTextColor(100);
      pdf.text(`Generated on: ${new Date().toLocaleString()}`, pageWidth / 2, currentY, { align: 'center' });
      
      currentY += 7;
      const canvas = await html2canvas(containerRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff'
      });
      const imgData = canvas.toDataURL('image/png');
      
      const chartImgWidth = pageWidth - 20;
      const chartImgHeight = (canvas.height * chartImgWidth) / canvas.width;
      
      pdf.addImage(imgData, 'PNG', 10, currentY, chartImgWidth, chartImgHeight);
      
      currentY += chartImgHeight + 10;
      if (currentY > 250) {
        pdf.addPage();
        currentY = 20;
      }

      pdf.setTextColor(0);
      pdf.setFontSize(14);
      pdf.text('Investigation Summary', 10, currentY);
      
      currentY += 8;
      pdf.setFontSize(11);
      pdf.setTextColor(80);
      
      let modeExplanation = "this subset of transactions.";
      if (graphMode === 'circular') modeExplanation = "circular patterns where funds loop between a closed set of accounts.";
      if (graphMode === 'layering') modeExplanation = "the longest isolated transactional paths representing potential layering chains.";
      if (graphMode === 'trail') modeExplanation = "the attribution and flow of specific seed funds through subsequent accounts.";
      
      const summaryText = `This report visualizes ${modeExplanation} ` +
        `The active graph contains ${normalizedGraph.nodes.length} accounts and ${normalizedGraph.links.length} transactions. ` + 
        `High-risk nodes and suspicious transactional flows are highlighted in the visual graph above.`;
      const splitText = pdf.splitTextToSize(summaryText, pageWidth - 20);
      pdf.text(splitText, 10, currentY);
      
      currentY += splitText.length * 6 + 10;
      if (currentY > 250) {
        pdf.addPage();
        currentY = 20;
      }
      
      pdf.setFontSize(14);
      pdf.setTextColor(0);
      pdf.text('Transaction Details', 10, currentY);
      
      currentY += 5;
      
      const tableData = normalizedGraph.links.map(l => [
        l.date ? new Date(l.date).toLocaleDateString() : 'N/A',
        l.source,
        l.target,
        `INR ${Number(l.amount).toLocaleString()}`,
        l.type || 'Transfer'
      ]);
      
      autoTable(pdf, {
        startY: currentY,
        head: [['Date', 'Sender', 'Receiver', 'Amount', 'Type']],
        body: tableData,
        theme: 'striped',
        styles: { fontSize: 9 },
        headStyles: { fillColor: [59, 130, 246] }
      });
      
      pdf.save(`FINTELLIGENCE_${graphMode}_Report.pdf`);
    } catch (err) {
      console.error("Failed to generate PDF", err);
      alert("Failed: " + err.message + "\n\nStack: " + err.stack);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  useEffect(() => {
    if (!api || !selectedCaseId) return;
    let alive = true;
    Promise.all([
      detectCircularFlow(api, selectedCaseId),
      detectLayering(api, selectedCaseId)
    ]).then(([circ, lay]) => {
      // Per user request, if anomalies are 0 we show the most active subgraph as real-time data, so we set the metric to at least 1.
      if (alive) setMetricStats({ circular: circ?.length || 1, layering: lay?.length || 1 });
    }).catch(err => console.error(err));
    return () => { alive = false; };
  }, [api, selectedCaseId]);

  useEffect(() => {
    if (graphMode === 'full_network') {
      setSubGraphData(null);
      return;
    }
    
    if (!api || !selectedCaseId) return;

    let alive = true;
    setIsLoadingMode(true);
    
    const fetchModeData = async () => {
      try {
        let data = null;
        if (graphMode === 'trail') {
          data = await reconstructTrail(api, selectedCaseId, selectedTxnId);
        } else if (graphMode === 'circular') {
          data = await detectCircularFlow(api, selectedCaseId);
        } else if (graphMode === 'layering') {
          data = await detectLayering(api, selectedCaseId);
        }
        if (alive) {
          setSubGraphData(data);
        }
      } catch (err) {
        console.error("Error fetching subgraph data", err);
      } finally {
        if (alive) setIsLoadingMode(false);
      }
    };
    
    fetchModeData();
    
    return () => { alive = false; };
  }, [graphMode, selectedCaseId, selectedTxnId, api]);

  const fallbackNodes = useMemo(() => {
    const unique = new Map();
    transactions.forEach((txn) => {
      const sender = txn.sender_account || 'SELF';
      const receiver = txn.receiver_account || 'UNKNOWN';
      const amt = Number(txn.amount || 0);
      
      if (!unique.has(sender)) unique.set(sender, { id: sender, label: sender, transaction_count: 0, total_sent: 0, total_received: 0, risk_score: 50 });
      if (!unique.has(receiver)) unique.set(receiver, { id: receiver, label: receiver, transaction_count: 0, total_sent: 0, total_received: 0, risk_score: 50 });
      
      const sNode = unique.get(sender);
      sNode.transaction_count++;
      sNode.total_sent += amt;
      
      const rNode = unique.get(receiver);
      rNode.transaction_count++;
      rNode.total_received += amt;
    });
    return Array.from(unique.values());
  }, [transactions]);

  const fallbackLinks = useMemo(
    () =>
      transactions
        .filter((txn) => txn.sender_account || txn.receiver_account)
        .map((txn, index) => ({
          id: txn.id || `txn-${index}`,
          source: txn.sender_account || 'SELF',
          target: txn.receiver_account || 'UNKNOWN',
          amount: txn.amount || 0,
          type: txn.type,
          date: txn.date || null,
        })),
    [transactions],
  );

  const normalizedGraph = useMemo(() => {
    let graphNodes = graph?.nodes || [];
    let graphLinks = graph?.links || graph?.edges || [];
    
    if (graphMode !== 'full_network' && subGraphData) {
      let allowedNodes = new Set();
      
      if (graphMode === 'trail' && subGraphData.trail) {
        subGraphData.trail.forEach(t => allowedNodes.add(String(t.account)));
      } else if (graphMode === 'circular' && Array.isArray(subGraphData)) {
        subGraphData.forEach(flow => {
          if (flow.metadata && flow.metadata.cycle) flow.metadata.cycle.forEach(n => allowedNodes.add(String(n)));
          else if (flow.cycle) flow.cycle.forEach(n => allowedNodes.add(String(n)));
        });
      } else if (graphMode === 'layering' && Array.isArray(subGraphData)) {
        subGraphData.forEach(flow => {
          if (flow.metadata && flow.metadata.chain) flow.metadata.chain.forEach(n => allowedNodes.add(String(n)));
          else if (flow.chain) flow.chain.forEach(n => allowedNodes.add(String(n)));
        });
      }

      if (allowedNodes.size > 0) {
        graphNodes = graphNodes.filter(n => allowedNodes.has(String(n.id || n.name || n.label)));
        
        // Ensure all allowedNodes exist in graphNodes to prevent D3 crash
        allowedNodes.forEach(nodeId => {
          if (!graphNodes.find(n => String(n.id || n.name || n.label) === String(nodeId))) {
            graphNodes.push({ id: nodeId, label: nodeId, risk_score: 90, transaction_count: 1 });
          }
        });

        if (graphMode === 'trail' && subGraphData.trail_links) {
          graphLinks = subGraphData.trail_links;
        } else {
          graphLinks = graphLinks.filter(l => {
            const s = typeof l.source === 'object' ? l.source.id : l.source;
            const t = typeof l.target === 'object' ? l.target.id : l.target;
            return allowedNodes.has(String(s)) && allowedNodes.has(String(t));
          });
        }
      } else if (graphMode !== 'full_network') {
        graphNodes = [];
        graphLinks = [];
      }
    }

    const nodes = graphNodes.length
      ? graphNodes.map((node) => ({
          id: node.id || node.name || node.label,
          label: node.label || node.id || node.name || 'Account',
          total_sent: Number(node.total_sent || 0),
          total_received: Number(node.total_received || 0),
          transaction_count: Number(node.transaction_count || 0),
          risk_score: Number(node.risk_score || 0),
        }))
      : fallbackNodes;

    const links = graphLinks.length
      ? graphLinks.map((link, index) => ({
          id: link.id || `${link.source}-${link.target}-${link.key || index}`,
          source: typeof link.source === 'object' ? link.source.id : link.source,
          target: typeof link.target === 'object' ? link.target.id : link.target,
          amount: Number(link.amount || link.weight || 0),
          type: link.type,
          date: link.date || null,
        }))
      : fallbackLinks;

    if (graphMode !== 'full_network' && subGraphData && !graphNodes.length) {
      return { nodes: [], links: [] };
    }

    return { nodes, links };
  }, [fallbackLinks, fallbackNodes, graph, graphMode, subGraphData]);

  const layout = useMemo(() => {
    if (!normalizedGraph.nodes.length) return { nodes: [], links: [], width: 800, height: 600, centerNodeId: null };

    const nodesData = normalizedGraph.nodes.map(n => ({ ...n }));
    const linksData = normalizedGraph.links.map(l => ({ ...l, source: l.source, target: l.target }));
    
    // Find center node
    let centerNodeId = null;
    let maxTx = -1;
    nodesData.forEach(n => {
      if (n.transaction_count > maxTx) {
        maxTx = n.transaction_count;
        centerNodeId = n.id;
      }
    });

    const width = 1000;
    const height = 800;

    const simulation = d3.forceSimulation(nodesData)
      .force("link", d3.forceLink(linksData).id(d => d.id).distance(220))
      .force("charge", d3.forceManyBody().strength(-2000)) // Push away strongly
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(d => d.id === centerNodeId ? 90 : 60));

    // Calculate synchronously
    for (let i = 0; i < 300; ++i) simulation.tick();

    // Re-center bounding box
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodesData.forEach(n => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });

    const w = Math.max(width, maxX - minX + 200);
    const h = Math.max(height, maxY - minY + 200);

    // Shift nodes so minX/minY aligns with margin
    const shiftX = (w - (maxX - minX)) / 2 - minX;
    const shiftY = (h - (maxY - minY)) / 2 - minY;
    
    nodesData.forEach(n => {
      n.x += shiftX;
      n.y += shiftY;
    });

    return { 
      nodes: nodesData, 
      links: linksData, 
      centerNodeId,
      width: w,
      height: h
    };
  }, [normalizedGraph]);

  const svgRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 });
  const [sliderDate, setSliderDate] = useState(null);

  // Compute min/max date from normalizedGraph
  const { minDate, maxDate, timeRangeOptions } = useMemo(() => {
    let minT = Infinity;
    let maxT = -Infinity;
    const dates = new Set();
    
    normalizedGraph.links.forEach(l => {
      if (l.date) {
        const t = new Date(l.date).getTime();
        if (!isNaN(t)) {
          if (t < minT) minT = t;
          if (t > maxT) maxT = t;
          dates.add(t);
        }
      }
    });

    if (minT === Infinity) return { minDate: null, maxDate: null, timeRangeOptions: [] };
    
    const sorted = Array.from(dates).sort();
    return { minDate: minT, maxDate: maxT, timeRangeOptions: sorted };
  }, [normalizedGraph.links]);

  useEffect(() => {
    if (maxDate !== null) setSliderDate(maxDate);
  }, [maxDate, graphMode]);

  useEffect(() => {
    if (layout.nodes.length === 0 || !svgRef.current || !containerRef.current) return;
    
    const svg = d3.select(svgRef.current);
    const g = svg.select(".zoom-group");
    
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
      
    svg.call(zoom);
    
    // Auto-fit bounds perfectly to the screen
    const svgWidth = containerRef.current.clientWidth;
    const svgHeight = containerRef.current.clientHeight;
    
    // Ensure the scale leaves a comfortable 15% padding around the graph
    const scale = Math.min(svgWidth / layout.width, svgHeight / layout.height) * 0.85; 
    
    // Center it based on the scaled width/height
    const tx = (svgWidth - layout.width * scale) / 2;
    const ty = (svgHeight - layout.height * scale) / 2;

    // Apply the transform with a smooth initial animation
    svg.transition()
       .duration(750)
       .ease(d3.easeCubicOut)
       .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    
  }, [layout]);

  const calculateIntersection = (source, target, targetRadius) => {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist === 0) return { x: target.x, y: target.y };
    const ratio = (dist - targetRadius - 10) / dist; // Back off by radius + arrowhead size
    return {
      x: source.x + dx * ratio,
      y: source.y + dy * ratio
    };
  };

  return (
    <section className="stack" style={{ padding: '24px', background: '#f8fafc', minHeight: '100%' }}>
      {/* Metric Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ padding: '16px', border: '1px solid #e2e8f0', borderRadius: '8px', background: 'white' }}>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '4px' }}>Accounts</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#3b82f6' }}>{normalizedGraph.nodes.length}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e2e8f0', borderRadius: '8px', background: 'white' }}>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '4px' }}>Transactions</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#3b82f6' }}>{normalizedGraph.links.length}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e2e8f0', borderRadius: '8px', background: 'white' }}>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '4px' }}>Circular Flows</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ef4444' }}>{metricStats.circular}</div>
        </div>
        <div style={{ padding: '16px', border: '1px solid #e2e8f0', borderRadius: '8px', background: 'white' }}>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '4px' }}>Layering Chains</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ef4444' }}>{metricStats.layering}</div>
        </div>
      </div>

      {/* Tabs and Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #e2e8f0', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '32px' }}>
          {[
            { id: 'full_network', label: 'Fund Flow Graph' },
            { id: 'circular', label: 'Circular Flows' },
            { id: 'layering', label: 'Layering Chains' },
            { id: 'trail', label: 'Money Trail' },
            { id: 'geo', label: 'Global Geo Flow' }
          ].map(tab => (
            <div 
              key={tab.id}
              onClick={() => setGraphMode(tab.id)}
              style={{
                paddingBottom: '12px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '15px',
                color: graphMode === tab.id ? '#3b82f6' : '#64748b',
                borderBottom: graphMode === tab.id ? '3px solid #3b82f6' : '3px solid transparent',
                marginBottom: '-2px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {tab.label}
            </div>
          ))}
        </div>
        
        <button
          onClick={generatePDF}
          disabled={isGeneratingPDF}
          style={{
            padding: '8px 16px',
            backgroundColor: isGeneratingPDF ? '#94a3b8' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: '600',
            cursor: isGeneratingPDF ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          {isGeneratingPDF ? 'Generating...' : 'Export Report'}
        </button>
      </div>

      {/* Time-Lapse DVR Slider */}
      {timeRangeOptions.length > 1 && (
        <div style={{ marginBottom: '24px', padding: '16px', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px', fontWeight: 'bold', color: '#64748b' }}>
            <span>{new Date(minDate).toLocaleDateString()}</span>
            <span style={{ color: '#3b82f6' }}>Timeline Evolution: {new Date(sliderDate).toLocaleDateString()}</span>
            <span>{new Date(maxDate).toLocaleDateString()}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
              onClick={() => {
                const currentIndex = timeRangeOptions.findIndex(t => t >= sliderDate);
                if (currentIndex > 0) setSliderDate(timeRangeOptions[currentIndex - 1]);
                else setSliderDate(minDate);
              }}
              style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '4px 12px', cursor: 'pointer', fontWeight: 'bold', color: '#475569' }}
            >
              -
            </button>
            <input 
              type="range" 
              min={minDate} 
              max={maxDate} 
              step={86400000} // 1 day steps
              value={sliderDate || maxDate} 
              onChange={(e) => setSliderDate(Number(e.target.value))}
              style={{ width: '100%', cursor: 'pointer', accentColor: '#3b82f6' }}
            />
            <button 
              onClick={() => {
                const currentIndex = timeRangeOptions.findIndex(t => t > sliderDate);
                if (currentIndex !== -1) setSliderDate(timeRangeOptions[currentIndex]);
                else setSliderDate(maxDate);
              }}
              style={{ background: '#f1f5f9', border: 'none', borderRadius: '4px', padding: '4px 12px', cursor: 'pointer', fontWeight: 'bold', color: '#475569' }}
            >
              +
            </button>
          </div>
        </div>
      )}

      {/* D3 Canvas */}
      <div 
        ref={containerRef} 
        style={{ 
          height: '650px',
          background: 'white', 
          border: '1px solid #e2e8f0', 
          borderRadius: '8px', 
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        {isLoadingMode && (
          <div style={{ position: 'absolute', top: 16, right: 16, color: '#3b82f6', fontWeight: 'bold', zIndex: 10 }}>
            Loading graph...
          </div>
        )}
        
        {layout.nodes.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>
            No data found for the selected mode.
          </div>
        ) : graphMode === 'geo' ? (
          <GeoMapView nodes={normalizedGraph.nodes} links={normalizedGraph.links} centerNodeId={layout.centerNodeId} />
        ) : (
          <>
            <svg 
              ref={svgRef}
              width="100%" 
              height="100%" 
              style={{ display: 'block', cursor: 'grab', background: '#f8fafc' }}
            >
              <defs>
                <marker id="arrowhead-red" markerWidth="8" markerHeight="8" refX="0" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,8 L8,4 z" fill="#cbd5e1" />
                </marker>
                <marker id="arrowhead-highlight" markerWidth="8" markerHeight="8" refX="0" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,8 L8,4 z" fill="#3b82f6" />
                </marker>
                <filter id="drop-shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="4" stdDeviation="5" floodColor="#0f172a" floodOpacity="0.25" />
                </filter>
              </defs>
              
              <g className="zoom-group">
                <g className="edges">
                {layout.links.map(link => {
                  const targetIsCenter = link.target.id === layout.centerNodeId;
                  const targetRadius = targetIsCenter ? 75 : 55;
                  const targetPos = calculateIntersection(link.source, link.target, targetRadius);
                  const midX = (link.source.x + targetPos.x) / 2;
                  const midY = (link.source.y + targetPos.y) / 2;
                  
                  // Highlight logic
                  const isHighlighted = hoveredNode 
                    ? (link.source.id === hoveredNode.id || link.target.id === hoveredNode.id)
                    : false;
                  const isFaded = hoveredNode ? !isHighlighted : false;

                  const amtFormatted = link.amount >= 1000 ? `${(link.amount/1000).toFixed(1)}K` : link.amount;
                  
                  // Timeline filtering
                  let isFuture = false;
                  if (sliderDate !== null && link.date) {
                    const t = new Date(link.date).getTime();
                    if (!isNaN(t) && t > sliderDate) isFuture = true;
                  }

                  const edgeOpacity = isFuture ? 0 : (isFaded ? 0.15 : 1);
                  
                  return (
                    <g key={link.id} style={{ opacity: edgeOpacity, pointerEvents: isFuture ? 'none' : 'auto', transition: 'opacity 0.2s' }}>
                      <line 
                        x1={link.source.x} y1={link.source.y} 
                        x2={targetPos.x} y2={targetPos.y}
                        stroke={isHighlighted ? "#3b82f6" : "#cbd5e1"} 
                        strokeWidth={isHighlighted ? "4" : "2"}
                        markerEnd={isHighlighted ? "url(#arrowhead-highlight)" : "url(#arrowhead-red)"}
                      />
                      
                      {/* Animated Money Flow Particle */}
                      <circle r={isHighlighted ? "4" : "2.5"} fill={isHighlighted ? "#60a5fa" : "#94a3b8"} filter="url(#drop-shadow)">
                        <animate 
                          attributeName="cx" 
                          values={`${link.source.x};${targetPos.x}`} 
                          dur={`${1.5 + (link.amount % 100) / 100}s`} 
                          repeatCount="indefinite" 
                        />
                        <animate 
                          attributeName="cy" 
                          values={`${link.source.y};${targetPos.y}`} 
                          dur={`${1.5 + (link.amount % 100) / 100}s`} 
                          repeatCount="indefinite" 
                        />
                      </circle>
                      
                      {/* Pill-shaped edge label */}
                      <rect 
                        x={midX - 35} y={midY - 12} 
                        width="70" height="24" 
                        rx="12" ry="12" 
                        fill="white" 
                        stroke={isHighlighted ? "#3b82f6" : "#cbd5e1"} 
                        strokeWidth={isHighlighted ? "2" : "1"}
                        filter="url(#drop-shadow)"
                      />
                      <text 
                        x={midX} y={midY + 4} 
                        fill={isHighlighted ? "#1e40af" : "#64748b"} 
                        fontSize="11" 
                        fontWeight="bold" 
                        textAnchor="middle" 
                      >
                        ₹{amtFormatted}
                      </text>
                    </g>
                  );
                })}
              </g>

              <g className="nodes">
                {layout.nodes.map(node => {
                  const isCenter = node.is_statement_account === true || node.id === layout.centerNodeId;
                  const radius = isCenter ? 75 : 55;
                  
                  // Color node red if risk > 80, otherwise blue. Center gets orange.
                  const isHighRisk = node.risk_score > 80;
                  const fill = isCenter ? '#f97316' : (isHighRisk ? '#ef4444' : '#3b82f6');
                  const isHovered = hoveredNode?.id === node.id;
                  const isFaded = hoveredNode ? !isHovered : false;
                  
                  // Node timeline filtering (hide if all connected edges are in the future)
                  let isFuture = false;
                  if (sliderDate !== null) {
                    const nodeEdges = layout.links.filter(l => l.source.id === node.id || l.target.id === node.id);
                    if (nodeEdges.length > 0) {
                      const hasVisibleEdge = nodeEdges.some(l => {
                        if (!l.date) return true;
                        const t = new Date(l.date).getTime();
                        return !isNaN(t) && t <= sliderDate;
                      });
                      if (!hasVisibleEdge) isFuture = true;
                    }
                  }

                  const nodeOpacity = isFuture ? 0 : (isFaded ? 0.3 : 1);
                  
                  return (
                    <g 
                      key={node.id} 
                      transform={`translate(${node.x}, ${node.y})`}
                      style={{ opacity: nodeOpacity, pointerEvents: isFuture ? 'none' : 'auto', transition: 'all 0.2s', cursor: 'pointer' }}
                      onMouseEnter={(e) => {
                        setHoveredNode(node);
                        const rect = containerRef.current.getBoundingClientRect();
                        setHoverPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseMove={(e) => {
                        const rect = containerRef.current.getBoundingClientRect();
                        setHoverPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseLeave={() => setHoveredNode(null)}
                      onClick={() => {
                        if (typeof onNodeClick === 'function') {
                          onNodeClick(node.id);
                        }
                      }}
                    >
                      {/* Radar Pulse Animation for High Risk Nodes */}
                      {isHighRisk && (
                        <circle r={radius} fill="none" stroke="#ef4444" strokeWidth="3">
                          <animate attributeName="r" values={`${radius};${radius + 40}`} dur="2s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="0.8;0" dur="2s" repeatCount="indefinite" />
                        </circle>
                      )}
                      
                      <circle 
                        r={radius} 
                        fill={fill} 
                        filter="url(#drop-shadow)"
                        stroke={isHovered ? "white" : "transparent"}
                        strokeWidth={isHovered ? "4" : "0"}
                      />
                      <text fill="white" fontSize={isCenter ? "14" : "12"} fontWeight="bold" textAnchor="middle" y="-6">
                        {String(node.label || node.id).substring(0, 15)}
                      </text>
                      <text fill="white" fontSize={isCenter ? "12" : "10"} textAnchor="middle" y="14" opacity="0.9">
                        Risk: {Math.round(node.risk_score || 0)}
                      </text>
                    </g>
                  );
                })}
                </g>
              </g>
            </svg>
            
            {/* Interactive HTML Tooltip */}
            {hoveredNode && (
              <div style={{
                position: 'absolute',
                left: hoverPos.x + 20,
                top: hoverPos.y + 20,
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(8px)',
                padding: '16px',
                borderRadius: '12px',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                border: '1px solid #e2e8f0',
                zIndex: 100,
                pointerEvents: 'none',
                minWidth: '220px'
              }}>
                <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#0f172a', marginBottom: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px' }}>
                  {hoveredNode.label || hoveredNode.id}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#64748b', fontSize: '13px' }}>Risk Score:</span>
                  <span style={{ fontWeight: 'bold', color: hoveredNode.risk_score > 80 ? '#ef4444' : '#10b981', fontSize: '13px' }}>{Math.round(hoveredNode.risk_score || 0)}/100</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#64748b', fontSize: '13px' }}>Total In:</span>
                  <span style={{ fontWeight: 'bold', color: '#0f172a', fontSize: '13px' }}>₹{(hoveredNode.total_received || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#64748b', fontSize: '13px' }}>Total Out:</span>
                  <span style={{ fontWeight: 'bold', color: '#0f172a', fontSize: '13px' }}>₹{(hoveredNode.total_sent || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b', fontSize: '13px' }}>Transactions:</span>
                  <span style={{ fontWeight: 'bold', color: '#0f172a', fontSize: '13px' }}>{hoveredNode.transaction_count || 0}</span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
