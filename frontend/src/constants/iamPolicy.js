export const IAM_POLICY_JSON = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrail",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:ListTrails"
      ],
      "Resource": "*"
    }
  ]
};

export const IAM_SETUP_STEPS = [
  { step: 1, title: "Open IAM Console", description: "Go to AWS Console → IAM → Users → Create User" },
  { step: 2, title: "Set Username", description: "Name it: cloudtrail-ai-readonly. Disable console access." },
  { step: 3, title: "Attach Policy", description: "Choose 'Attach policies directly' → Create inline policy → paste the JSON below" },
  { step: 4, title: "Create Access Key", description: "Go to the user → Security Credentials → Create Access Key → Choose 'Application running outside AWS'" },
  { step: 5, title: "Copy Credentials", description: "Copy the Access Key ID and Secret Access Key. Secret is shown only once." }
];
