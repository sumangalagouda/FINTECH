import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Spin } from 'antd';
import dagre from 'dagre';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 100, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 50,
        y: nodeWithPosition.y - 50,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

const CustomNode = ({ data }) => {
  const size = Math.max(60, Math.min(120, (data.transaction_count || 1) * 15));
  let color = '#22C55E'; // Green
  if (data.risk_score > 75) color = '#EF4444'; // Red
  else if (data.risk_score >= 40) color = '#F97316'; // Orange
  if (data.is_hub) color = '#8B5CF6'; // Purple

  return (
    <div style={{
      width: size, height: size, borderRadius: '50%', backgroundColor: color,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      color: 'white', fontSize: '10px', border: '2px solid white', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      cursor: 'pointer', padding: '5px', textAlign: 'center'
    }}>
      <div style={{ fontWeight: 'bold', wordBreak: 'break-all' }}>{data.label}</div>
      <div>₹{data.total_received}</div>
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

const FundFlowGraph = ({ caseId, onNodeClick }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!caseId) return;

    const fetchGraph = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token') || '';
        // If caseId is "mock-case-id" don't hit the API to prevent 500 error if not needed
        let endpoint = `http://localhost:5000/api/graph/${caseId}`;

        const res = await fetch(endpoint, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
          throw new Error('Failed to fetch graph data');
        }

        const data = await res.json();

        let fetchedNodes = [];
        let fetchedEdges = [];

        if (data.nodes) {
          fetchedNodes = data.nodes.map(n => ({
            id: n.id,
            type: 'custom',
            data: { label: n.id, ...n },
            position: { x: 0, y: 0 }
          }));
        }

        if (data.links) {
          fetchedEdges = data.links.map(l => ({
            id: `e-${l.source}-${l.target}`,
            source: l.source,
            target: l.target,
            animated: true,
            style: { stroke: '#9CA3AF', strokeWidth: 1 }
          }));
        }

        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(fetchedNodes, fetchedEdges, 'LR');

        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      } catch (error) {
        console.error("Error fetching graph:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [caseId, setNodes, setEdges]);

  return (
    <div style={{ width: '100%', height: '600px', border: '1px solid #eee', borderRadius: '8px' }}>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Spin size="large" />
        </div>
      ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(e, node) => onNodeClick && onNodeClick(node)}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      )}
    </div>
  );
};

export default FundFlowGraph;

