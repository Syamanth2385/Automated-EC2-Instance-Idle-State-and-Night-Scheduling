import boto3
import json
import os
from datetime import datetime

def lambda_handler(event, context):
    # Initialize AWS clients
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')
    
    # Get environment variables
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    if not sns_topic_arn:
        return {
            'statusCode': 400,
            'body': json.dumps('SNS_TOPIC_ARN environment variable must be set')
        }
    
    try:
        print("Starting scheduled night shutdown...")
        
        # Get all running instances with AutoShutdown tag
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'tag:AutoShutdown', 'Values': ['true', 'True', 'TRUE', 'yes', 'Yes', 'YES']}
            ]
        )
        
        shutdown_instances = []
        total_running = 0
        
        # Process each instance
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                total_running += 1
                instance_id = instance['InstanceId']
                instance_type = instance.get('InstanceType', 'Unknown')
                launch_time = instance.get('LaunchTime', 'Unknown')
                
                # Get instance details from tags
                instance_name = 'Unnamed'
                environment = 'Unknown'
                owner = 'Unknown'
                auto_shutdown_value = 'true'
                
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                    elif tag['Key'] == 'Environment':
                        environment = tag['Value']
                    elif tag['Key'] == 'Owner':
                        owner = tag['Value']
                    elif tag['Key'] == 'AutoShutdown':
                        auto_shutdown_value = tag['Value']
                
                shutdown_instances.append({
                    'InstanceId': instance_id,
                    'InstanceName': instance_name,
                    'InstanceType': instance_type,
                    'Environment': environment,
                    'Owner': owner,
                    'LaunchTime': launch_time,
                    'AutoShutdownValue': auto_shutdown_value
                })
                
                print(f"Found instance for shutdown: {instance_id} ({instance_name}) - {environment}")
        
        # Stop the instances
        stopped_instances = []
        if shutdown_instances:
            print(f"Attempting to stop {len(shutdown_instances)} instances...")
            
            instance_ids_to_stop = [inst['InstanceId'] for inst in shutdown_instances]
            
            try:
                stop_response = ec2.stop_instances(InstanceIds=instance_ids_to_stop)
                stopped_instances = shutdown_instances
                print(f"Successfully initiated shutdown for {len(stopped_instances)} instances")
                
                # Log the stopping instances details
                for instance in stop_response['StoppingInstances']:
                    print(f"Instance {instance['InstanceId']}: {instance['PreviousState']['Name']} → {instance['CurrentState']['Name']}")
                    
            except Exception as e:
                print(f"Error stopping instances: {str(e)}")
                send_error_notification(sns, sns_topic_arn, f"Failed to stop instances: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error stopping instances: {str(e)}')
                }
        
        # Send notification
        send_notification(sns, sns_topic_arn, stopped_instances, total_running)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Scheduled shutdown complete: {len(stopped_instances)} instances stopped',
                'stopped_instances': len(stopped_instances),
                'total_tagged_instances': total_running
            })
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        send_error_notification(sns, sns_topic_arn, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(f'Unexpected error: {str(e)}')
        }

def send_notification(sns, topic_arn, stopped_instances, total_tagged):
    """Send SNS notification about scheduled shutdown"""
    try:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        if stopped_instances:
            subject = f'🌙 Scheduled Night Shutdown: {len(stopped_instances)} Instances Stopped'
            message = f"""Scheduled Night Shutdown Report

🌙 AUTOMATIC SHUTDOWN COMPLETED 🌙

Summary:
- Instances with AutoShutdown tag: {total_tagged}
- Instances successfully stopped: {len(stopped_instances)}
- Shutdown time: {current_time} UTC

Stopped Instances Details:
"""
            
            # Group by environment for better organization
            environments = {}
            for inst in stopped_instances:
                env = inst['Environment']
                if env not in environments:
                    environments[env] = []
                environments[env].append(inst)
            
            for env, instances in environments.items():
                message += f"\n📁 Environment: {env}\n"
                for inst in instances:
                    message += f"""
  🖥️  {inst['InstanceName']} ({inst['InstanceId']})
      Type: {inst['InstanceType']}
      Owner: {inst['Owner']}
      Launch Time: {inst['LaunchTime']}
      AutoShutdown: {inst['AutoShutdownValue']}
"""
            
            message += f"""
---

💰 COST SAVINGS:
These instances will not incur compute charges while stopped.
Storage (EBS) charges continue, but compute costs are eliminated.

🔄 TO RESTART INSTANCES:
1. Go to EC2 Console: https://console.aws.amazon.com/ec2/#Instances:
2. Select stopped instances
3. Actions → Instance State → Start

⏰ SCHEDULE INFO:
This is an automated shutdown based on the 'AutoShutdown' tag.
To exclude an instance from future shutdowns, remove or change the AutoShutdown tag.

📋 TAG MANAGEMENT:
- Current trigger: AutoShutdown = true/True/TRUE/yes/Yes/YES
- To disable: Set AutoShutdown = false or remove the tag
- Tag instances: https://console.aws.amazon.com/ec2/#Instances:

Time: {current_time} UTC
"""
        else:
            subject = '🌙 Scheduled Night Shutdown: No Instances to Stop'
            message = f"""Scheduled Night Shutdown Report

🌙 SCHEDULED SHUTDOWN CHECK COMPLETED 🌙

Summary:
- Instances checked: {total_tagged}
- Instances stopped: 0

No running instances were found with the AutoShutdown tag set to 'true'.

This could mean:
✅ No instances are tagged for automatic shutdown
✅ All tagged instances are already stopped
✅ AutoShutdown tags are set to 'false'

💡 TO ENABLE AUTOMATIC SHUTDOWN:
1. Go to EC2 Console: https://console.aws.amazon.com/ec2/#Instances:
2. Select instances you want to auto-shutdown
3. Add tag: Key='AutoShutdown', Value='true'

⏰ SCHEDULE:
This function runs automatically based on your EventBridge schedule.
Current check time: {current_time} UTC

Time: {current_time} UTC
"""
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print("Scheduled shutdown notification sent successfully")
        
    except Exception as e:
        print(f"Error sending shutdown notification: {str(e)}")

def send_error_notification(sns, topic_arn, error_message):
    """Send error notification via SNS"""
    try:
        subject = '❌ Scheduled Shutdown Error'
        message = f"""An error occurred in the Scheduled Night Shutdown system:

Error: {error_message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Please check the CloudWatch Logs for more details.
"""
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        
    except Exception as e:
        print(f"Error sending error notification: {str(e)}")
