
---

## Setup Guide

### 1. Create EC2 Instances

Create EC2 instances that you want the scheduler to manage.

Add the tag:
AutoShutdown = True


---

### 2. Deploy Lambda Functions
Two Lambda functions are used:
1. Idle Instance Detector
2. Night Shutdown Scheduler
Upload the Python scripts from the `lambda/` directory.
---

### 3. Configure EventBridge Rules

Create scheduled triggers:
**Idle Detection**
Runs once daily.
**Night Shutdown**
cron(0 22 * * ? *)
Runs at **10 PM daily**.
---
### 4. Create CloudWatch Dashboard
Add widgets for:
- Lambda Invocations
- Lambda Errors
- Lambda Duration
- EC2 Status Checks
- SNS Messages
---
## Example Use Case
This project is useful for:
- Development environments
- Test infrastructure
- Cloud cost optimization
- FinOps automation
---
## Skills Demonstrated
- Cloud Cost Optimization (FinOps)
- AWS Serverless Automation
- Infrastructure Monitoring
- Event-driven architecture
- Cloud resource scheduling
---
## Future Improvements
- Automatic EC2 startup scheduler
- Cost savings analytics
- Multi-account resource scanning
- Tag-based automation policies

---
## Author
Syamanth  
Computer Science Student | Cloud Engineering Enthusiast
