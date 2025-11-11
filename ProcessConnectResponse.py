import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
connect = boto3.client('connect')

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', '')
NOTIFY_EMAIL = os.environ.get('NOTIFY_EMAIL', '')
CONNECT_INSTANCE_ID = os.environ.get('CONNECT_INSTANCE_ID', '')
TASK_FLOW_ID = os.environ.get('TASK_FLOW_ID', '')
TASK_TEMPLATE_ID = os.environ.get('TASK_TEMPLATE_ID', '')  # optional

def lambda_handler(event, context):
    logger.info("Lambda triggered by Amazon Connect.")
    logger.info(f"Raw event received: {event}")

    try:
        attrs = event['Details']['ContactData']['Attributes']
        patient_id = attrs['patient_id']
        date = attrs['appointment_date']
        response = attrs.get('userResponse', '')
        phone_number = attrs.get('phone_number', '')

        new_status = "Confirmed" if response == "1" else "Reschedule" if response == "2" else "Pending"
        logger.info(f"Parsed patient_id: {patient_id}, appointment_date: {date}, response: {response}, new_status: {new_status}")

        # Update DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'patient_id': patient_id, 'appointment_date': date},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": new_status}
        )
        logger.info(f"Updated DynamoDB status for {patient_id} to {new_status}")

        # Compose email content
        plain_text = f"Patient {patient_id} responded: {new_status} for {date}."

        html_body = f"""
        <html>
        <head>
          <style>
            body {{
              font-family: Arial, sans-serif;
              background-color: #f9f9f9;
              padding: 20px;
            }}
            .container {{
              background-color: #ffffff;
              padding: 20px;
              border-radius: 8px;
              max-width: 600px;
              margin: auto;
              border: 1px solid #dddddd;
            }}
            h2 {{
              color: #4CAF50;
              text-align: center;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
              margin-top: 20px;
            }}
            th, td {{
              padding: 10px;
              text-align: left;
              border-bottom: 1px solid #dddddd;
            }}
            th {{
              background-color: #f2f2f2;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>📞 Patient Response Notification</h2>
            <table>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
              <tr>
                <td>Patient ID</td>
                <td>{patient_id}</td>
              </tr>
              <tr>
                <td>Appointment Date</td>
                <td>{date}</td>
              </tr>
              <tr>
                <td>Response</td>
                <td>{new_status}</td>
              </tr>
              <tr>
                <td>Phone Number</td>
                <td>{phone_number}</td>
              </tr>
            </table>
          </div>
        </body>
        </html>
        """

        # Send email
        response_email = ses.send_email(
            Source=NOTIFY_EMAIL,
            Destination={'ToAddresses': [NOTIFY_EMAIL]},
            Message={
                'Subject': {'Data': f"Patient {patient_id} Response"},
                'Body': {
                    'Text': {'Data': plain_text},
                    'Html': {'Data': html_body}
                }
            }
        )
        logger.info(f"Email sent to {NOTIFY_EMAIL}: {response_email['MessageId']}")

        # Create Task if rescheduling
        if new_status == "Reschedule":
            logger.info(f"Creating Connect Task for reschedule...")

            task_params = {
                "InstanceId": CONNECT_INSTANCE_ID,
                "Name": "Reschedule Appointment",
                "Description": f"Patient {patient_id} requested to reschedule appointment on {date}.",
                "ContactFlowId": TASK_FLOW_ID,
                "Attributes": {
                    "patient_id": patient_id,
                    "appointment_date": date,
                    "reason": "reschedule_request",
                    "patient_phone": phone_number
                }
            }

            if TASK_TEMPLATE_ID:
                task_params["TaskTemplateId"] = TASK_TEMPLATE_ID

            response_task = connect.start_task_contact(**task_params)
            logger.info(f"Connect Task created: {response_task['ContactId']}")

    except Exception as e:
        logger.error(f"Error processing response: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

    return {
        "status": "Logged",
        "responseStatus": new_status
    }


