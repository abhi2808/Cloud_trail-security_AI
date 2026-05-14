import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Search, Key, Users, Shield, Activity, Database, Eye, Server, Bell, HardDrive, DollarSign, Cloud } from 'lucide-react';

const TOOL_LABELS = {
  search_cloudtrail:        'CloudTrail Search',
  get_iam_user_permissions: 'IAM Permissions',
  get_iam_role_permissions: 'IAM Role',
  list_iam_users:           'IAM Users',
  simulate_iam_permissions: 'Permission Sim',
  check_access_keys:        'Access Keys',
  describe_ec2_instance:    'EC2 Instance',
  describe_security_group:  'Security Group',
  list_ec2_instances:       'EC2 Scan',
  get_cloudwatch_alarms:    'CloudWatch Alarms',
  get_metric_anomalies:     'Metric Anomalies',
  list_s3_buckets:          'S3 Buckets',
  get_s3_bucket_policy:     'S3 Policy',
  get_caller_identity:      'Identity Check',
  list_kms_keys:            'KMS Keys',
  get_kms_key_details:      'KMS Details',
  list_secrets:             'Secrets Scan',
  get_secret_details:       'Secret Details',
  list_rds_databases:       'RDS Databases',
  get_rds_database_details: 'RDS Details',
  list_rds_snapshots:       'RDS Snapshots',
  get_cost_anomalies:       'Cost Anomalies',
  get_cost_spike:           'Cost Spike',
  get_cost_summary:         'Cost Summary',
  list_eks_clusters:        'EKS Clusters',
  describe_eks_cluster:     'EKS Cluster',
};

const TOOL_ICON_MAP = {
  search_cloudtrail:        Search,
  get_iam_user_permissions: Key,
  get_iam_role_permissions: Shield,
  list_iam_users:           Users,
  simulate_iam_permissions: Activity,
  check_access_keys:        Key,
  describe_ec2_instance:    Server,
  describe_security_group:  Shield,
  list_ec2_instances:       Server,
  get_cloudwatch_alarms:    Bell,
  get_metric_anomalies:     Activity,
  list_s3_buckets:          HardDrive,
  get_s3_bucket_policy:     Eye,
  get_caller_identity:      Search,
  list_kms_keys:            Database,
  get_kms_key_details:      Database,
  list_secrets:             Eye,
  get_secret_details:       Eye,
  list_rds_databases:       Database,
  get_rds_database_details: Database,
  get_cost_anomalies:       DollarSign,
  get_cost_spike:           DollarSign,
  list_eks_clusters:        Cloud,
  describe_eks_cluster:     Cloud,
};

const ease = [0.16, 1, 0.3, 1];

export default function InvestigationTimeline({ steps = [], severity }) {
  const [expanded, setExpanded] = useState(false);

  if (steps.length === 0) return null;

  return (
    <div className="timeline-wrap">
      <button className="timeline-toggle" onClick={() => setExpanded(v => !v)}>
        <div className="timeline-toggle-left">
          <ChevronDown
            size={14}
            strokeWidth={1.5}
            style={{ transition: 'transform 0.25s', transform: expanded ? 'rotate(180deg)' : 'none' }}
          />
          <span>Investigation trace</span>
          <span className="timeline-count">{steps.length} step{steps.length !== 1 ? 's' : ''}</span>
        </div>
        {severity && severity !== 'NONE' && (
          <span style={{
            fontSize: '0.62rem', fontWeight: 600, padding: '2px 8px', borderRadius: '100px',
            border: '1px solid', textTransform: 'uppercase', letterSpacing: '0.06em',
            color: `var(--sev-${severity.toLowerCase()})`,
            borderColor: `var(--sev-${severity.toLowerCase()})`,
            background: `rgba(${severity === 'CRITICAL' ? '248,113,113' : severity === 'HIGH' ? '251,146,60' : severity === 'MEDIUM' ? '252,211,77' : '96,165,250'},0.08)`,
          }}>
            {severity}
          </span>
        )}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            className="timeline-steps"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease }}
          >
            {steps.map((step, i) => {
              const isLast = i === steps.length - 1;
              const label = TOOL_LABELS[step.tool] || step.tool;
              const Icon = TOOL_ICON_MAP[step.tool] || Search;

              return (
                <motion.div
                  key={i}
                  className="timeline-step"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.35, ease, delay: i * 0.06 }}
                >
                  <div className="step-node">
                    <div className="step-dot">
                      <Icon size={11} strokeWidth={1.5} />
                    </div>
                    {!isLast && <div className="step-line" />}
                  </div>

                  <div className="step-content">
                    <div className="step-meta">
                      <span className="step-num">#{step.step}</span>
                      <span className="step-label">{label}</span>
                    </div>
                    {step.reasoning && (
                      <div className="step-reasoning">"{step.reasoning}"</div>
                    )}
                    <div className="step-result">
                      {step.tool.startsWith('parallel_batch') && step.parallel_results?.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {step.parallel_results.map((pr, idx) => (
                            <div key={idx} className="parallel-row">
                              <span className="parallel-arrow">↳</span>
                              <span className="parallel-tool">{TOOL_LABELS[pr.tool] || pr.tool}</span>
                              <span className="parallel-arrow">→</span>
                              <span className="parallel-summary">{pr.summary}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        step.summary
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
