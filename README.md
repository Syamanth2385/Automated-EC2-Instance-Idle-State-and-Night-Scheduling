# Automated-EC2-Instance-Idle-State-and-Night-Scheduling
# AWS EC2 Cost Optimization Automation

## Overview

This project implements a FinOps automation system for optimizing AWS EC2 infrastructure costs.  
The system detects idle EC2 instances based on CPU utilization and automatically stops them to prevent unnecessary cloud spending.  

Additionally, it includes a scheduled shutdown mechanism that stops development instances every night based on predefined tags.

A CloudWatch dashboard is also implemented to monitor automation performance and system activity.

---

## Features

### 1. Idle EC2 Instance Detector
- Automatically detects EC2 instances with **CPU utilization below 5%**.
- Runs daily to identify underutilized resources.
- Stops idle instances automatically to reduce infrastructure costs.

### 2. Night Shutdown Scheduler
- Automatically shuts down EC2 instances at **10 PM every day**.
- Uses **tag-based filtering** to avoid affecting production instances.

Supported Tag Format:
AutoShutdown = True
AutoShutdown = true
AutoShutdown = TRUE

Only instances with this tag will be automatically stopped.

### 3. Cloud Monitoring Dashboard

A monitoring dashboard was created using **Amazon CloudWatch** to visualize system activity and automation performance.

Dashboard Metrics Include:

- Lambda function invocations
- Lambda execution duration
- Lambda error rate
- Instance status check metrics
- SNS message notifications
- System activity monitoring

---

## Architecture

This system uses a serverless automation architecture.

Main AWS Services Used:

- AWS Lambda
- Amazon EventBridge
- Amazon EC2
- Amazon CloudWatch
- Amazon SNS

Workflow:
      EventBridge (Scheduled Trigger)
                ↓
              Lambda
                ↓
 Idle Instance Detection / Night Shutdown
                ↓
       EC2 Instance Stop Action
                ↓
      CloudWatch Monitoring + SNS Alerts

---

## CloudWatch Dashboard

The project includes a monitoring dashboard to track automation behavior.

Example metrics visualized:

- Lambda Invocation Count
- Lambda Duration
- Error Monitoring
- EC2 Instance Status
- SNS Notifications Sent

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
