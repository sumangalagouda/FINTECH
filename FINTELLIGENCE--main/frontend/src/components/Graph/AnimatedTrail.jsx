import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button, Slider, Tooltip } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StepBackwardOutlined, StepForwardOutlined, ReloadOutlined } from '@ant-design/icons';

const AnimatedTrail = ({ caseId }) => {
  const [trail, setTrail] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!caseId || caseId === 'mock-case-id') return;

    const fetchTrail = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token') || '';
        const res = await fetch('http://localhost:5000/api/graph/reconstruct-trail', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ case_id: caseId })
        });
        const data = await res.json();
        if (data && data.trail) {
          setTrail(data.trail);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrail();
  }, [caseId]);

  useEffect(() => {
    let interval;
    if (isPlaying && currentStep < trail.length) {
      interval = setInterval(() => {
        setCurrentStep((prev) => prev + 1);
      }, 2000 / speed);
    } else if (currentStep >= trail.length) {
      setIsPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, speed, trail.length]);

  return (
    <div style={{ padding: '20px', background: '#1e1e1e', color: 'white', borderRadius: '8px', overflowX: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', minWidth: '600px' }}>
        <h3>Animated Money Trail</h3>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Button icon={<StepBackwardOutlined />} onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} />
          <Button type="primary" icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />} onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? 'Pause' : 'Play'}
          </Button>
          <Button icon={<StepForwardOutlined />} onClick={() => setCurrentStep(Math.min(trail.length, currentStep + 1))} />
          <Button icon={<ReloadOutlined />} onClick={() => { setCurrentStep(0); setIsPlaying(false); }} />
          <div style={{ width: '100px', marginLeft: '20px' }}>
            <Slider min={0.5} max={3} step={0.5} value={speed} onChange={setSpeed} />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', position: 'relative', height: '250px', alignItems: 'center', minWidth: '800px' }}>
        <AnimatePresence>
          {trail.slice(0, currentStep).map((node, index) => (
            <React.Fragment key={`${node.account}-${index}`}>
              {index > 0 && (
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: 100 }}
                  style={{ height: '2px', background: '#EF4444', margin: '0 10px' }}
                  transition={{ duration: 0.5 }}
                />
              )}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
                <motion.div
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{
                    width: '80px', height: '80px', borderRadius: '50%',
                    background: node.risk_flag === 'destination' ? '#EF4444' : (node.risk_flag === 'origin' ? '#22C55E' : '#3B82F6'),
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold',
                    fontSize: '10px', textAlign: 'center', wordBreak: 'break-all', padding: '5px'
                  }}
                >
                  {node.account}
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  style={{
                    position: 'absolute', top: '90px', background: 'rgba(0,0,0,0.7)',
                    padding: '8px', borderRadius: '4px', fontSize: '11px', whiteSpace: 'nowrap',
                    border: '1px solid #444', zIndex: 10
                  }}
                >
                  <div style={{ color: '#9CA3AF', marginBottom: '2px' }}>{node.label}</div>
                  <div><span style={{ color: '#22C55E' }}>Rcvd:</span> ₹{node.amount_received}</div>
                  <div><span style={{ color: '#EF4444' }}>Sent:</span> ₹{node.amount_sent}</div>
                  <div><span style={{ color: '#FBBF24' }}>Time Held:</span> {node.time_held_minutes} mins</div>
                  <div style={{ marginTop: '2px' }}><span style={{ color: '#A78BFA' }}>Flag:</span> {node.risk_flag}</div>
                </motion.div>
              </div>
            </React.Fragment>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AnimatedTrail;
