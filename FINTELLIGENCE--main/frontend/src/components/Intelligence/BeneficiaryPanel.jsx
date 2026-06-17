import React from 'react';
import { Drawer, Progress, Table, Tag } from 'antd';

const BeneficiaryPanel = ({ visible, onClose, nodeData }) => {
  if (!nodeData) return null;

  const mockTransactions = [
    { key: '1', date: '2024-01-13', amount: 500000, type: 'credit' },
    { key: '2', date: '2024-01-14', amount: 498000, type: 'debit' },
  ];

  const columns = [
    { title: 'Date', dataIndex: 'date', key: 'date' },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', render: (val) => `₹${val.toLocaleString()}` },
    { title: 'Type', dataIndex: 'type', key: 'type', render: (val) => <Tag color={val === 'credit' ? 'green' : 'red'}>{val.toUpperCase()}</Tag> },
  ];

  return (
    <Drawer
      title="Beneficiary Intelligence"
      placement="right"
      onClose={onClose}
      open={visible}
      width={400}
    >
      <h3>{nodeData.label}</h3>
      <div style={{ marginBottom: '20px' }}>
        <strong>Risk Score:</strong>
        <Progress percent={nodeData.risk_score} status={nodeData.risk_score > 75 ? 'exception' : 'active'} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div>
          <div style={{ fontSize: '12px', color: '#6B7280' }}>Total Received</div>
          <div style={{ fontWeight: 'bold', color: '#22C55E' }}>₹{nodeData.total_received}</div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#6B7280' }}>Total Sent</div>
          <div style={{ fontWeight: 'bold', color: '#EF4444' }}>₹{nodeData.total_received * 0.9}</div>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <div><strong>Transaction Count:</strong> {nodeData.transaction_count}</div>
      </div>

      <h4>Transactions</h4>
      <Table dataSource={mockTransactions} columns={columns} pagination={false} size="small" />
    </Drawer>
  );
};

export default BeneficiaryPanel;
