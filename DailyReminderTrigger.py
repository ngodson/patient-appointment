import boto3
import os
import logging
from datetime import datetime
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients and resources
connect = boto3.client('connect')
dynamodb = boto3.resource('dynamodb')

# Environment variables with defaults
TABLE_NAME = os.environ.get('TABLE_NAME', '')
CONNECT_INSTANCE_ID = os.environ.get('CONNECT_INSTANCE_ID', '')
CONTACT_FLOW_ID = os.environ.get('CONTACT_FLOW_ID', '')
SOURCE_PHONE_NUMBER = os.environ.get('SOURCE_PHONE_NUMBER', '')

def lambda_handler(event, context):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logger.info(f"Starting outbound call process for date: {today}")
    logger.info(f"Using table: {TABLE_NAME}, instance ID: {CONNECT_INSTANCE_ID}")

    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan(
            FilterExpression="appointment_date = :d AND #s = :p",
            ExpressionAttributeValues={":d": today, ":p": "Pending"},
            ExpressionAttributeNames={"#s": "status"}
        )

        items = response.get('Items', [])
        logger.info(f"Found {len(items)} appointments to call.")

        for item in items:
            phone = item['phone_number']
            logger.info(f"Raw phone number from DB for patient {item['patient_id']}: {repr(phone)}")

            try:
                connect.start_outbound_voice_contact(
                    DestinationPhoneNumber=phone,
                    ContactFlowId=CONTACT_FLOW_ID,
                    InstanceId=CONNECT_INSTANCE_ID,
                    SourcePhoneNumber=SOURCE_PHONE_NUMBER,
                    Attributes={
                        "patient_id": item['patient_id'],
                        "appointment_date": item['appointment_date'],
                        "phone_number": item['phone_number']
                    }
                )
                logger.info(f"Call initiated successfully for {item['patient_id']}")
            except ClientError as e:
                logger.error(f"Failed to start call for {item['patient_id']}: {e}")

    except Exception as e:
        logger.error(f"Error scanning DynamoDB or initiating calls: {str(e)}")

    return {
        "status": "completed",
        "appointments_found": len(items)
    }
