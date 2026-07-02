import React, { useState, useEffect } from 'react';
import {
  Modal,
  Steps,
  Form,
  Input,
  Select,
  Checkbox,
  Button,
  Spin,
  message,
  Divider,
  Alert,
  Row,
  Col,
  Card,
  Statistic
} from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const TakeActionModal = ({ caseId, open, onClose, onActionComplete }) => {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [gateData, setGateData] = useState(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const [formData, setFormData] = useState({
    decision: null,
    authority: '',
    ipc_sections: [],
    remarks: ''
  });

  const [password, setPassword] = useState('');
  const [outcome, setOutcome] = useState(null);

  // Fetch gate check data on modal open
  useEffect(() => {
    if (open && caseId) {
      fetchGateCheckData();
    }
  }, [open, caseId]);

  const fetchGateCheckData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('fintelligence_token');
      const response = await axios.get(
        `/api/cases/${caseId}/action-gate-check`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGateData(response.data);

      // Pre-fill Step 2 form with suggestions
      setFormData(prev => ({
        ...prev,
        authority: response.data.auto_suggested_authority,
        ipc_sections: response.data.auto_suggested_ipc_sections
      }));
    } catch (error) {
      message.error('Failed to load readiness check. ' + (error.response?.data?.error || error.message));
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleProceedStep1 = () => {
    setStep(1);
  };

  const handleBackStep2 = () => {
    setStep(0);
  };

  const handleNextStep2 = () => {
    // Validate Step 2
    if (!formData.decision) {
      message.error('Please select a decision');
      return;
    }
    if (formData.remarks.length < 10) {
      message.error('Remarks must be at least 10 characters');
      return;
    }
    if ((formData.decision === 'recommend_fir' || formData.decision === 'escalate_external') && !formData.authority) {
      message.error('Authority must be selected for this decision');
      return;
    }

    setStep(2);
  };

  const handleBackStep3 = () => {
    setStep(1);
  };

  const handleSignAndConfirm = async () => {
    if (!password) {
      message.error('Password is required');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('fintelligence_token');

      const response = await axios.post(
        `/api/cases/${caseId}/sio-action`,
        {
          decision: formData.decision,
          authority: formData.authority,
          ipc_sections: formData.ipc_sections,
          remarks: formData.remarks,
          password: password
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Success - show outcome
      setOutcome(response.data);
      setStep(3);
      message.success(response.data.message);

      // Do not auto-close so the user can download documents.
      if (onActionComplete) {
        onActionComplete(response.data);
      }
    } catch (error) {
      if (error.response?.status === 401) {
        message.error('Incorrect password. Signature not applied.');
      } else {
        message.error('Failed to submit action. ' + (error.response?.data?.error || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setStep(0);
    setFormData({
      decision: null,
      authority: '',
      ipc_sections: [],
      remarks: ''
    });
    setPassword('');
    setOutcome(null);
    setGateData(null);
    onClose();
  };

  const handleDownload = async (type) => {
    try {
      let endpoint = '';
      let method = 'GET';
      let body = null;
      let filename = '';

      if (type === 'FIR') {
        endpoint = `/api/reports/fir-draft/${caseId}`;
        method = 'POST';
        body = JSON.stringify({
          signature_password: password,
          mock_details: formData.remarks
        });
        filename = `FIR_Draft_${caseId.slice(0, 8)}.pdf`;
      } else if (type === 'DOSSIER') {
        endpoint = `/api/reports/dossier/${caseId}?authority=${encodeURIComponent(formData.authority)}`;
        filename = `Case_Dossier_${caseId.slice(0, 8)}.pdf`;
      } else if (type === 'CLOSURE' || type === 'REFERRAL') {
        endpoint = `/api/reports/closure/${caseId}`;
        method = 'POST';
        body = JSON.stringify({
          signature_password: password,
          closure_reason: formData.remarks
        });
        filename = type === 'CLOSURE' ? `Closure_Report_${caseId.slice(0, 8)}.pdf` : `Referral_Letter_${caseId.slice(0, 8)}.pdf`;
      }

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('fintelligence_token')}`,
          'Content-Type': 'application/json'
        },
        body
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to download');
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(objectUrl);
      message.success(`Downloaded ${filename}`);
    } catch (err) {
      console.error(err);
      message.error(`Download failed: ${err.message}`);
    }
  };

  const renderGateCheckStep = () => {
    if (!gateData) {
      return <Spin />;
    }

    const { gate_conditions, suspicion_score, threshold, below_threshold, warning } = gateData;

    return (
      <div>
        <h3 style={{ marginBottom: '20px' }}>CASE READINESS CHECK</h3>

        {warning && (
          <Alert
            message="⚠️ OVERRIDE NOTICE"
            description={warning}
            type="warning"
            showIcon
            style={{ marginBottom: '20px' }}
          />
        )}

        <Card style={{ marginBottom: '20px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="Suspicion Score"
                value={suspicion_score}
                suffix={`/ ${threshold}`}
                valueStyle={{ color: suspicion_score >= threshold ? '#52c41a' : '#ff4d4f' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Status"
                value={suspicion_score >= threshold ? 'Above Threshold' : 'Below Threshold'}
                valueStyle={{ color: suspicion_score >= threshold ? '#52c41a' : '#faad14' }}
              />
            </Col>
          </Row>
        </Card>

        <div style={{ marginBottom: '20px' }}>
          <h4>READINESS CONDITIONS</h4>
          {Object.entries(gate_conditions).map(([key, condition]) => (
            <div
              key={key}
              style={{
                padding: '12px',
                marginBottom: '8px',
                borderLeft: `4px solid ${condition.status ? '#52c41a' : '#faad14'}`,
                backgroundColor: condition.status ? '#f6ffed' : '#fffbe6'
              }}
            >
              <div style={{ fontWeight: 'bold', color: '#333' }}>
                {condition.status ? '✅' : '🟠'} {condition.label}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {condition.value}
              </div>
            </div>
          ))}
        </div>

        <Alert
          message="Note: All conditions are informational only. You can proceed regardless of status."
          type="info"
          style={{ marginBottom: '20px' }}
        />

        <div style={{ textAlign: 'right' }}>
          <Button onClick={handleCancel} style={{ marginRight: '8px' }}>
            CANCEL
          </Button>
          <Button type="primary" onClick={handleProceedStep1}>
            PROCEED
          </Button>
        </div>
      </div>
    );
  };

  const renderDecisionFormStep = () => {
    const showAuthorityField =
      formData.decision === 'recommend_fir' || formData.decision === 'escalate_external';
    const showIpcField =
      formData.decision === 'recommend_fir' || formData.decision === 'escalate_external';

    const allIpcOptions = [
      'PMLA Section 3 — Money Laundering',
      'IPC 420 — Cheating',
      'IPC 467 — Forgery of Valuable Security',
      'IPC 471 — Using Forged Documents',
      'IPC 201 — Causing Disappearance',
      'IPC 201-A — Causing Disappearance of Evidence'
    ];

    const authorityOptions = [
      'Economic Offences Wing',
      'Enforcement Directorate (ED)',
      'Financial Intelligence Unit (FIU)',
      'Cyber Crime Cell',
      'Central Bureau of Investigation',
      'Bank Fraud Investigation Unit'
    ];

    return (
      <div>
        <h3 style={{ marginBottom: '20px' }}>SR. IO DECISION</h3>

        <Form layout="vertical">
          <Form.Item label="DECISION (Required)" required>
            <Select
              placeholder="Select your decision"
              value={formData.decision}
              onChange={(value) => setFormData({ ...formData, decision: value })}
              options={[
                { label: 'Recommend FIR Filing', value: 'recommend_fir' },
                { label: 'Close — Insufficient Evidence', value: 'close_insufficient_evidence' },
                {
                  label: 'Return to IO for Further Investigation',
                  value: 'return_to_io'
                },
                { label: 'Escalate to Higher Authority', value: 'escalate_external' }
              ]}
            />
          </Form.Item>

          {showAuthorityField && (
            <Form.Item label="SUBMISSION AUTHORITY (Required)">
              <Select
                placeholder="Select submission authority"
                value={formData.authority}
                onChange={(value) => setFormData({ ...formData, authority: value })}
                options={authorityOptions.map(auth => ({ label: auth, value: auth }))}
              />
            </Form.Item>
          )}

          {showIpcField && (
            <Form.Item label="IPC SECTIONS APPLICABLE">
              <Checkbox.Group
                value={formData.ipc_sections}
                onChange={(values) => setFormData({ ...formData, ipc_sections: values })}
                options={allIpcOptions.map(ipc => ({ label: ipc, value: ipc }))}
                style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
              />
            </Form.Item>
          )}

          <Form.Item label="REMARKS (Required, min 10 characters)">
            <Input.TextArea
              placeholder="State your reasoning for this decision..."
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              rows={5}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              Characters: {formData.remarks.length} / 10 (minimum)
            </div>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'right', marginTop: '20px' }}>
          <Button onClick={handleBackStep2} style={{ marginRight: '8px' }}>
            BACK
          </Button>
          <Button type="primary" onClick={handleNextStep2}>
            NEXT: SIGN & CONFIRM
          </Button>
        </div>
      </div>
    );
  };

  const renderSignatureConfirmStep = () => {
    const decisionLabel = {
      recommend_fir: 'Recommend FIR Filing',
      close_insufficient_evidence: 'Close — Insufficient Evidence',
      return_to_io: 'Return to IO for Further Investigation',
      escalate_external: 'Escalate to Higher Authority'
    }[formData.decision];

    return (
      <div>
        <h3 style={{ marginBottom: '20px' }}>CONFIRM WITH DIGITAL SIGNATURE</h3>

        <Card style={{ marginBottom: '20px', backgroundColor: '#fafafa' }}>
          <h4>SUMMARY (Read-Only)</h4>
          <div style={{ marginBottom: '8px' }}>
            <strong>Decision:</strong> {decisionLabel}
          </div>
          {formData.authority && (
            <div style={{ marginBottom: '8px' }}>
              <strong>Authority:</strong> {formData.authority}
            </div>
          )}
          {formData.ipc_sections.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <strong>IPC Sections:</strong> {formData.ipc_sections.join(', ')}
            </div>
          )}
          <div style={{ marginBottom: '8px' }}>
            <strong>Signed by:</strong> {localStorage.getItem('userName') || 'Current User'}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Timestamp:</strong> {new Date().toLocaleString('en-IN')}
          </div>
        </Card>

        {gateData?.below_threshold && (
          <Alert
            message="⚠️ OVERRIDE NOTICE"
            description={`Suspicion score (${gateData.suspicion_score.toFixed(1)}) is below threshold (${gateData.threshold}). This decision will be permanently flagged as a Sr. IO override in the audit trail.`}
            type="warning"
            showIcon
            style={{ marginBottom: '20px' }}
          />
        )}

        <Form layout="vertical">
          <Form.Item label="Enter your password to sign:" required>
            <Input.Password
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onPressEnter={handleSignAndConfirm}
            />
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'right', marginTop: '20px' }}>
          <Button onClick={handleBackStep3} disabled={loading} style={{ marginRight: '8px' }}>
            BACK
          </Button>
          <Button
            type="primary"
            onClick={handleSignAndConfirm}
            loading={loading}
            danger
          >
            CONFIRM & SIGN
          </Button>
        </div>
      </div>
    );
  };

  const renderOutcomeStep = () => {
    if (!outcome) return null;

    const { decision } = outcome;

    const outcomeConfigs = {
      recommend_fir: {
        icon: <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a' }} />,
        title: '✅ FIR FILING RECOMMENDED',
        actions: [
          { label: 'DOWNLOAD FIR DRAFT', type: 'FIR' },
          { label: 'DOWNLOAD CASE DOSSIER', type: 'DOSSIER' }
        ]
      },
      close_insufficient_evidence: {
        icon: <CloseCircleOutlined style={{ fontSize: '48px', color: '#1890ff' }} />,
        title: '✅ CASE CLOSED',
        description: 'Closed with Sr. IO digital signature.',
        actions: [{ label: 'DOWNLOAD CLOSURE REPORT', type: 'CLOSURE' }]
      },
      return_to_io: {
        icon: <ClockCircleOutlined style={{ fontSize: '48px', color: '#faad14' }} />,
        title: '✅ RETURNED TO INVESTIGATION OFFICER',
        description: 'IO has been notified with your notes.'
      },
      escalate_external: {
        icon: <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a' }} />,
        title: `✅ ESCALATED TO ${formData.authority?.toUpperCase()}`,
        actions: [
          { label: 'DOWNLOAD REFERRAL LETTER', type: 'REFERRAL' },
          { label: 'DOWNLOAD CASE DOSSIER', type: 'DOSSIER' }
        ]
      }
    };

    const config = outcomeConfigs[decision] || outcomeConfigs.recommend_fir;

    return (
      <div style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: '20px' }}>{config.icon}</div>
        <h2 style={{ marginBottom: '10px' }}>{config.title}</h2>
        {config.description && (
          <p style={{ fontSize: '14px', color: '#666', marginBottom: '20px' }}>
            {config.description}
          </p>
        )}

        <Card style={{ marginBottom: '20px', backgroundColor: '#fafafa' }}>
          <div style={{ marginBottom: '8px' }}>
            <strong>Signature:</strong>{' '}
            {outcome.signature_hash?.substring(0, 20)}...
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Signed:</strong> {new Date(outcome.signed_at).toLocaleString('en-IN')}
          </div>
        </Card>

        {config.actions && (
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            {config.actions.map((action, idx) => (
              <Button
                key={idx}
                type="primary"
                style={{ marginRight: '8px', marginBottom: '8px' }}
                onClick={() => handleDownload(action.type)}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <Button onClick={onClose} size="large">
            CLOSE WINDOW
          </Button>
        </div>
      </div>
    );
  };

  const steps = [
    { title: 'Readiness Check', content: renderGateCheckStep() },
    { title: 'Decision Form', content: renderDecisionFormStep() },
    { title: 'Confirm Sign', content: renderSignatureConfirmStep() },
    { title: 'Outcome', content: renderOutcomeStep() }
  ];

  return (
    <Modal
      title="TAKE ACTION — SR. IO DECISION WORKFLOW"
      open={open}
      onCancel={handleCancel}
      width={700}
      footer={null}
      closable={step !== 3 && !loading}
    >
      <Spin spinning={loading && step === 0}>
        <Steps
          current={step}
          items={steps.map(s => ({ title: s.title }))}
          style={{ marginBottom: '30px' }}
        />

        <Divider />

        {steps[step]?.content}
      </Spin>
    </Modal>
  );
};

export default TakeActionModal;
