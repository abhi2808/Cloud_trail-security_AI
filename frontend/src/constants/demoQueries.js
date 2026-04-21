const demoQueries = [
  {
    label: '🖥️ EC2 Terminations',
    query: 'Who terminated EC2 instances in the last 24 hours?',
  },
  {
    label: '👤 IAM User Creation',
    query: 'Show all IAM user creation events this week',
  },
  {
    label: '🔒 Security Group Changes',
    query: 'Who modified security groups today?',
  },
  {
    label: '⚠️ Root Account Activity',
    query: 'Show all root user activity in the last 7 days',
  },
  {
    label: '🔑 Access Key Creation',
    query: 'Who created new AWS access keys this month?',
  },
];

export default demoQueries;
