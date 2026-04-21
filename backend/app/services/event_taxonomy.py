"""
AWS CloudTrail event name taxonomy for AI system prompt injection.
Maps natural language descriptions to actual CloudTrail event names.
"""

EVENT_TAXONOMY = """
=== AWS CLOUDTRAIL EVENT NAME TAXONOMY ===

Use this taxonomy to map user natural language queries to the correct AWS CloudTrail event names.

--- EC2 (Elastic Compute Cloud) ---
- terminated / deleted / killed / removed instance → TerminateInstances
- stopped instance → StopInstances
- started / launched existing instance → StartInstances
- created / launched NEW instance → RunInstances
- modified / changed security group inbound rules → AuthorizeSecurityGroupIngress
- revoked / removed security group inbound rules → RevokeSecurityGroupIngress
- modified security group rules (general) → ModifySecurityGroupRules
- created security group → CreateSecurityGroup
- deleted security group → DeleteSecurityGroup
- modified instance attribute → ModifyInstanceAttribute
- created AMI / image → CreateImage
- deregistered AMI → DeregisterImage
- allocated elastic IP → AllocateAddress
- released elastic IP → ReleaseAddress

--- IAM (Identity and Access Management) ---
- created user → CreateUser
- deleted user → DeleteUser
- attached / assigned policy to user → AttachUserPolicy
- attached / assigned policy to role → AttachRolePolicy
- detached policy from user → DetachUserPolicy
- detached policy from role → DetachRolePolicy
- created access key / credentials → CreateAccessKey
- deleted access key → DeleteAccessKey
- changed / reset password / login profile → UpdateLoginProfile
- created login profile → CreateLoginProfile
- created role → CreateRole
- deleted role → DeleteRole
- assumed role / role switch / STS → AssumeRole
- created policy → CreatePolicy
- deleted policy → DeletePolicy
- added user to group → AddUserToGroup
- removed user from group → RemoveUserFromGroup
- enabled MFA → EnableMFADevice
- deactivated MFA → DeactivateMFADevice

--- S3 (Simple Storage Service) ---
- deleted bucket → DeleteBucket
- created bucket → CreateBucket
- changed / set bucket policy / permissions → PutBucketPolicy
- deleted bucket policy → DeleteBucketPolicy
- changed bucket ACL → PutBucketAcl
- enabled / disabled bucket versioning → PutBucketVersioning
- changed bucket encryption → PutBucketEncryption
- made bucket public → PutBucketPolicy (check for public access statements)
- uploaded object → PutObject
- deleted object → DeleteObject
- get object → GetObject

--- RDS (Relational Database Service) ---
- deleted database → DeleteDBInstance
- created database → CreateDBInstance
- modified database → ModifyDBInstance
- created DB snapshot → CreateDBSnapshot
- deleted DB snapshot → DeleteDBSnapshot
- restored DB from snapshot → RestoreDBInstanceFromDBSnapshot

--- Lambda ---
- created function → CreateFunction20150331
- deleted function → DeleteFunction20150331
- updated function code → UpdateFunctionCode20150331v2
- updated function configuration → UpdateFunctionConfiguration20150331v2
- invoked function → Invoke20150331

--- CloudFormation ---
- created stack → CreateStack
- deleted stack → DeleteStack
- updated stack → UpdateStack

--- VPC / Networking ---
- created VPC → CreateVpc
- deleted VPC → DeleteVpc
- created subnet → CreateSubnet
- deleted subnet → DeleteSubnet
- modified network ACL → CreateNetworkAclEntry, DeleteNetworkAclEntry
- created VPC peering → CreateVpcPeeringConnection
- deleted VPC peering → DeleteVpcPeeringConnection

--- General / Security Events ---
- console login / signed in → ConsoleLogin
- failed login attempt → ConsoleLogin (look for errorCode or errorMessage)
- root user activity → any event where userIdentity.type = "Root"
- suspicious activity indicators:
  * ConsoleLogin where MFA was NOT used (additionalEventData.MFAUsed = "No")
  * Root user performing any action
  * CreateAccessKey events (potential credential compromise)
  * Off-hours activity (actions outside 09:00-18:00 IST / 03:30-12:30 UTC)
  * Console logins from external / non-RFC1918 IP addresses
  * Multiple failed API calls (presence of errorCode in events)
  * AssumeRole from unexpected accounts
  * Changes to CloudTrail itself (StopLogging, DeleteTrail, UpdateTrail)

--- CloudTrail Self-Monitoring ---
- stopped logging → StopLogging
- started logging → StartLogging
- deleted trail → DeleteTrail
- created trail → CreateTrail
- updated trail → UpdateTrail

=== END TAXONOMY ===
"""
