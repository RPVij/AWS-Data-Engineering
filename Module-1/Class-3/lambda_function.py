import json
import boto3
import pandas as pd

def lambda_handler(event, context):
    # Initialize Boto3 clients
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')

    try:
        # Extract bucket name and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # Retrieve the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        json_content = json.loads(content)

        # Convert JSON content to a Pandas DataFrame
        df = pd.DataFrame(json_content)
        # Filter DataFrame for delivered orders
        delivered_orders_df = df[df['status'] == 'delivered']

        # If you need to do something with delivered_orders_df, like storing it, do so here
        filtered_json = delivered_orders_df.to_json(orient='records')
        original_filename = key.split('/')[-1]  # Extract the original filename
        base_filename, file_extension = original_filename.rsplit('.', 1)
        modified_filename = f"{base_filename}_delivered.{file_extension}"
        target_key = f'doordash-target-zn/{modified_filename}'
        s3_client.put_object(Body=filtered_json, Bucket=bucket, Key=target_key)
        
        # Publish a success notification to SNS
        sns_response = sns_client.publish(
            TopicArn='arn:aws:sns:ap-south-1:891377038355:aws-de-m1-c3-a1-sns',
            Message='Data successfully processed and loaded from: ' + key,
            Subject='Lambda S3 Processing Notification',
        )

        print(delivered_orders_df)

        return {
            'statusCode': 200,
            'body': json.dumps('Process completed successfully!')
        }

    except Exception as e:
        # Log the error
        print(f"Error processing S3 object {key} from bucket {bucket}. Error: {str(e)}")

        # Optionally, publish an error notification to SNS
        sns_response = sns_client.publish(
            TopicArn='arn:aws:sns:ap-south-1:891377038355:aws-de-m1-c3-a1-sns',
            Message=f"Error processing S3 object {key} from bucket {bucket}. Error: {str(e)}",
            Subject='Lambda S3 Processing Error Notification',
        )

        # Return an error response
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing the S3 object.')
        }

    finally:
        print("----- EXECUTION COMPLETE -----")
