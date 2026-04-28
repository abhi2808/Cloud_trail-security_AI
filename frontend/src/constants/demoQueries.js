const demoQueries = [
  {
    label: '🕵️ Full Identity Investigation',
    query: 'Investigate any IAM user who logged in last night — show their permissions and what they did.',
  },
  {
    label: '🛡️ Internet Exposure Audit',
    query: 'Do any EC2 instances have security groups open to 0.0.0.0/0? What IAM roles do they carry?',
  },
  {
    label: '🪣 Data Exposure Risk',
    query: 'Which S3 buckets are publicly accessible and do they have permissive bucket policies?',
  },
  {
    label: '🚨 Threat Triage',
    query: 'Are there any active CloudWatch alarms or unusual API spikes right now? What is the blast radius?',
  },
];

export default demoQueries;
