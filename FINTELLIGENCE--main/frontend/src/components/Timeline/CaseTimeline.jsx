import React from 'react';
import { motion } from 'framer-motion';
import { Timeline } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const CaseTimeline = ({ transactions }) => {
  // Group by date in real logic
  const mockTransactions = [
    { id: 1, date: '2024-01-13', amount: 500000, type: 'credit', risk_level: 'critical', desc: 'Transfer from ACC001' },
    { id: 2, date: '2024-01-13', amount: 498000, type: 'debit', risk_level: 'high', desc: 'Transfer to ACC002' },
    { id: 3, date: '2024-01-14', amount: 1500, type: 'debit', risk_level: 'low', desc: 'Amazon Purchase' },
  ];

  const items = mockTransactions.map((t, index) => ({
    color: t.risk_level === 'critical' ? 'red' : t.risk_level === 'high' ? 'orange' : 'green',
    dot: t.type === 'credit' ? <ArrowUpOutlined style={{ fontSize: '16px', color: '#22C55E' }} /> : <ArrowDownOutlined style={{ fontSize: '16px', color: '#EF4444' }} />,
    children: (
      <motion.div
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.2 }}
        style={{ padding: '10px', background: t.risk_level === 'critical' ? '#FEF2F2' : '#F9FAFB', borderRadius: '8px', cursor: 'pointer' }}
      >
        <div style={{ fontWeight: 'bold' }}>{t.date}</div>
        <div style={{ fontSize: '16px', color: t.type === 'credit' ? '#22C55E' : '#EF4444' }}>
          {t.type === 'credit' ? '+' : '-'}₹{t.amount.toLocaleString()}
        </div>
        <div style={{ color: '#6B7280' }}>{t.desc}</div>
      </motion.div>
    ),
  }));

  return (
    <div style={{ padding: '20px', background: 'white', borderRadius: '8px' }}>
      <h3>Case Timeline</h3>
      <Timeline items={items} />
    </div>
  );
};

export default CaseTimeline;
