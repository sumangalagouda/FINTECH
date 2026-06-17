import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#22C55E', '#F97316', '#EF4444']; // Green, Orange, Red

const data = [
  { name: 'Accounts', children: [
    { name: 'ACC001', size: 500000, risk_score: 95 },
    { name: 'ACC002', size: 300000, risk_score: 80 },
    { name: 'ACC003', size: 150000, risk_score: 50 },
    { name: 'ACC004', size: 50000, risk_score: 20 },
  ]}
];

const CustomizedContent = (props) => {
  const { root, depth, x, y, width, height, index, payload, colors, rank, name, risk_score } = props;

  let bgColor = COLORS[0];
  if (risk_score > 75) bgColor = COLORS[2];
  else if (risk_score >= 40) bgColor = COLORS[1];

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: bgColor,
          stroke: '#fff',
          strokeWidth: 2 / (depth + 1e-10),
          strokeOpacity: 1 / (depth + 1e-10),
        }}
      />
      {width > 50 && height > 30 ? (
        <text x={x + 4} y={y + 18} fill="#fff" fontSize={14}>
          {name}
        </text>
      ) : null}
    </g>
  );
};

const RiskHeatMap = () => {
  return (
    <div style={{ width: '100%', height: '400px', background: 'white', padding: '20px', borderRadius: '8px' }}>
      <h3>Risk Heat Map</h3>
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          fill="#8884d8"
          content={<CustomizedContent />}
        >
          <Tooltip />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export default RiskHeatMap;
