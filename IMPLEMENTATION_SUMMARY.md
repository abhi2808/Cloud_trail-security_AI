# CloudComply AI — Implementation Summary

## What The Application Is
A natural language AWS security and compliance investigation platform. Security analysts type plain English questions and an AI agent autonomously investigates across multiple AWS services, returning a structured verdict with severity, evidence, an investigation timeline, and recommended actions.

## Authentication & User Management
JWT-based multi-user authentication. Users register and login with email and bcrypt-hashed passwords. Tokens expire in 24 hours. All protected routes validate Bearer tokens via FastAPI middleware. Generic 401 responses on failure — never reveals whether email exists or password is wrong.

## AWS Account Management
Each user manages multiple AWS accounts within the platform. When adding an account, the user provides a nickname, region, access key ID, and secret access key. The backend validates key format, calls CloudTrail live to test the connection, and only saves after verification. Both credentials are encrypted with Fernet AES-256 before MongoDB storage. The encryption key lives only in the backend `.env` — never in the database. Decrypted keys exist only in memory during boto3 calls and are never logged, never returned to the frontend, and never surface in error messages. All account DB queries verify the account belongs to the requesting user.

## The Agentic ReAct Loop
The core of the application. When a user submits a query, the backend runs an autonomous investigation loop:
The agent receives the question plus all available tool definitions and reasons about what to investigate first. It calls a tool, sees the result, reasons about what to do next, calls another tool, and continues until it has enough evidence to form a verdict or hits the iteration limit. Each reasoning step is logged to an investigation memory which is passed back to the AI in each subsequent step so it remembers what it has already discovered.

The loop supports two execution modes:
1. **Single tool call**: The AI calls one tool and waits for the result before reasoning about the next step.
2. **Parallel batch**: The AI identifies multiple independent tool calls and returns them in a single `tool_calls` array. The runner executes all of them simultaneously using `asyncio.gather()` and returns all results as one memory entry. This counts as one iteration regardless of how many tools ran. 

*Safety Constraint*: The backend enforces a strict max batch limit (10 tool calls per iteration) to prevent AWS API rate limiting and context-window bloat.

## Parallel Execution Logic
The AI uses parallel batching in two scenarios. 
1. **Same-service fan-out**: After listing EC2 instances, it describes all running instances simultaneously, then checks all their security groups and IAM roles simultaneously in the same batch.
2. **Cross-service fan-out**: For broad sweep queries, it lists EC2, S3, RDS, KMS, secrets, and checks CloudWatch alarms all in a single parallel batch, then runs all detail lookups in a second parallel batch. A full account security audit that previously took 12+ sequential steps now completes in 3-4 steps.

## Region Routing Architecture
The platform handles region routing intelligently based on service capability:
- **Global Services**: IAM, S3, and Cost Explorer natively operate across the entire AWS account.
- **Parallel Multi-Region Sweeps**: CloudTrail handles "All Regions" queries by dynamically spawning 17 parallel background threads to sweep every AWS region simultaneously.
- **Regional Services**: EC2, EKS, KMS, RDS, and CloudWatch strictly target the user-selected region from the UI. If "All Regions" is selected, the platform defaults to the account's baseline region (e.g., `ap-south-1`) to avoid massive latency from cross-region metadata polling.

## AWS Services The Agent Can Investigate
- **CloudTrail**: `LookupEvents` queries. Finds who did what, when, and from which IP. The backend uses a smart query optimizer that prioritizes specific constraints (`ResourceName` over `EventName`) to drastically reduce AWS API calls, returning exactly what the AI needs without polluting context. It also features a date-math interceptor that corrects AI-generated date boundaries (automatically bumping exact midnight values to `23:59:59` to prevent missing same-day events). Features pagination up to 200 events and exponential backoff retry.
- **IAM**: Lists users and roles, reads all attached managed policies, inline policies, and group memberships. Derives effective services from policy documents. Checks access key age and flags keys older than 90 days. Simulates permissions and assesses the blast radius of compromised identities.
- **EC2**: Lists instances with state and tags. Describes individual instances including security groups, IAM profile, public IP, and IMDSv1 status. Analyzes security group rules and flags any rule open to `0.0.0.0/0` as public exposure.
- **CloudWatch**: Fetches metric data for EC2 and Lambda with anomaly detection (flags values >2x average). Lists all alarms currently in `ALARM` state.
- **S3**: Lists all buckets with public access block status. Checks policies for Principal wildcard. Never reads object contents. Explicit deny on `GetObject` in the IAM policy.
- **KMS**: Lists customer-managed keys with rotation status. Gets key policies and flags external account grants or keys with disabled rotation.
- **Secrets Manager**: Lists secrets with rotation status and last accessed date. Flags secrets not rotated in 90+ days. Gets resource policies and flags external access. Never calls `GetSecretValue`.
- **RDS**: Lists database instances with public accessibility, encryption status, and deletion protection. Flags publicly shared snapshots.
- **EKS (Kubernetes)**: Lists clusters, node groups, Fargate profiles, and add-ons. Flags clusters with public `0.0.0.0/0` API endpoints, missing KMS secrets encryption, or disabled control-plane audit logging.
- **AWS Cost Explorer**: Detects cost spikes by comparing recent spend to baseline. Gets AWS-detected ML cost anomalies. Gets daily cost breakdown for specific services.
- **AI/ML Metadata**: Scans Bedrock foundation models and invocation logging. Scans SageMaker endpoints, training jobs, and notebook instances.
- **Lambda**: Lists functions with runtime, role, environment variables. Flags suspicious env var names containing secret or password patterns.
- **AWS Config**: Gets historical configuration snapshots and resources currently failing compliance rules (when Config is enabled).

## AI Layer
Uses AWS Bedrock via `boto3` Converse API. 
Model: **Claude 3.5 Sonnet v2** (`apac.anthropic.claude-3-5-sonnet-20241022-v2:0`) via an APAC cross-region inference profile. The backend uses dedicated IAM credentials for Bedrock access, completely separate from the customer AWS credentials being audited.

The system prompt defines the ReAct JSON format for tool calls, maps human language to specific AWS EventNames, defines severity levels, IST timestamp conversion, sweep vs. targeted query behavior, parallel execution rules, and specialized investigation logic for cost spikes, identity blast radius, and missing audit data.

## IAM Policy Design
Split into three managed policies due to AWS 6144 character limit: `cloudcomply-ai-core`, `cloudcomply-ai-monitoring`, `cloudcomply-ai-datasecurity`. Philosophy: reads metadata, never reads data. Explicit Deny statements on the most sensitive actions: `s3:GetObject`, `kms:Decrypt`, `secretsmanager:GetSecretValue`, `ssm:GetParameter`, `lambda:InvokeFunction`, `bedrock:InvokeModel`, `sagemaker:InvokeEndpoint`.

## Frontend
React 18 with Vite, Zustand for state, TailwindCSS dark terminal theme. Three pages: Login/Register, Dashboard for account management, Chat for investigation. Chat renders each step in a collapsible timeline showing tool name, reasoning, and result summary. Parallel batch steps show each sub-tool result as an indented row. Severity badges and Recommended Actions render dynamically. Account and Region selector dropdowns at the top. JWT persisted in `localStorage`.

## Database
MongoDB Atlas with Motor async driver. Two collections: `users` (email, hashed password) and `accounts` (user_id, nickname, region, encrypted credentials, last verified timestamp). Indexes on email (unique) and user_id + nickname compound key.

## What Is Not Yet Implemented
- **Phase 2 Pipeline Features**: GuardDuty integration, VPC Flow Logs analysis.
- **Data Persistence**: Chat history persistence to MongoDB (currently lost on refresh). S3 investigation log archival for ML training.
- **Cross-Account Trust**: Cross-account investigation via STS AssumeRole.
