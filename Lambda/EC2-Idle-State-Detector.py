import boto3
import json
import os
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Initialize AWS clients
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    # Get environment variables
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    if not sns_topic_arn:
        return {
            'statusCode': 400,
            'body': json.dumps('SNS_TOPIC_ARN environment variable must be set')
        }
    
    try:
        print("Starting idle instance detection...")
        
        # Get all running instances
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        idle_instances = []
        total_instances = 0
        
        # Check each instance
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                total_instances += 1
                instance_id = instance['InstanceId']
                instance_type = instance.get('InstanceType', 'Unknown')
                
                # Get instance name from tags
                instance_name = 'Unnamed'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break
                
                print(f"Checking instance: {instance_id} ({instance_name})")
                
                # Get CPU utilization for last 24 hours
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
                
                try:
                    metrics = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1 hour periods
                        Statistics=['Average']
                    )
                    
                    if metrics['Datapoints']:
                        # Calculate average CPU over 24 hours
                        avg_cpu = sum(point['Average'] for point in metrics['Datapoints']) / len(metrics['Datapoints'])
                        print(f"Instance {instance_id} average CPU: {avg_cpu:.2f}%")
                        
                        # Check if instance is idle (less than 5% CPU for 24 hours)
                        if avg_cpu < 5.0:
                            idle_instances.append({
                                'InstanceId': instance_id,
                                'InstanceName': instance_name,
                                'InstanceType': instance_type,
                                'AvgCPU': avg_cpu,
                                'LaunchTime': instance.get('LaunchTime', 'Unknown')
                            })
                            print(f"Instance {instance_id} marked as idle")
                    else:
                        print(f"No CPU metrics found for instance {instance_id}")
                        
                except Exception as e:
                    print(f"Error getting metrics for {instance_id}: {str(e)}")
        
        # Stop idle instances if any found
        stopped_instances = []
        if idle_instances:
            print(f"Found {len(idle_instances)} idle instances")
            
            # Stop the instances
            instance_ids_to_stop = [inst['InstanceId'] for inst in idle_instances]
            
            try:
                ec2.stop_instances(InstanceIds=instance_ids_to_stop)
                stopped_instances = idle_instances
                print(f"Successfully stopped {len(stopped_instances)} instances")
            except Exception as e:
                print(f"Error stopping instances: {str(e)}")
                # Send error notification
                send_error_notification(sns, sns_topic_arn, str(e))
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error stopping instances: {str(e)}')
                }
        
        # Send notification
        send_notification(sns, sns_topic_arn, stopped_instances, total_instances)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {total_instances} instances, stopped {len(stopped_instances)} idle instances',
                'stopped_instances': len(stopped_instances)
            })
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        send_error_notification(sns, sns_topic_arn, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(f'Unexpected error: {str(e)}')
        }

def send_notification(sns, topic_arn, stopped_instances, total_instances):
    """Send SNS notification about stopped instances"""
    try:
        if stopped_instances:
            subject = f'🚨 EC2 Cost Alert: {len(stopped_instances)} Idle Instances Stopped'
            message = f"""EC2 Cost Optimization Report

Summary:
- Total running instances checked: {total_instances}
- Idle instances found and stopped: {len(stopped_instances)}

Stopped Instances Details:
"""
            
            for inst in stopped_instances:
                message += f"""
Instance: {inst['InstanceName']} ({inst['InstanceId']})
Type: {inst['InstanceType']}
Average CPU (24h): {inst['AvgCPU']:.2f}%
Launch Time: {inst['LaunchTime']}
---"""
            
            message += f"""

These instances had less than 5% CPU utilization over the past 24 hours and have been automatically stopped to save costs.

You can restart them anytime from the EC2 Console.

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        else:
            subject = '✅ EC2 Cost Report: No Idle Instances Found'
            message = f"""EC2 Cost Optimization Report

Good news! No idle instances were found.

Summary:
- Total running instances checked: {total_instances}
- Idle instances found: 0

All your running instances appear to be actively used (>5% CPU utilization over 24 hours).

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print("SNS notification sent successfully")
        
    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")

def send_error_notification(sns, topic_arn, error_message):
    """Send error notification via SNS"""
    try:
        subject = '❌ EC2 Cost Optimization Error'
        message = f"""An error occurred in the EC2 Cost Optimization system:

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
