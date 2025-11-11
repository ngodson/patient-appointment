🩺 Patient Appointment Reminder System

An automated patient appointment reminder system built with AWS Lambda, Amazon DynamoDB, and Amazon Connect.
This project automatically scans scheduled patient appointments and triggers outbound voice calls to remind patients of their upcoming visits.

Healthcare facilities often need to remind patients of upcoming appointments.
This project provides a serverless, scalable, and cost-effective solution using AWS services.

Each day, an AWS Lambda function scans a DynamoDB table for appointments scheduled for the current day with a Pending status, then initiates outbound voice calls using Amazon Connect.

   +-------------------+
   |  DynamoDB Table   |
   |-------------------|
   | patient_id        |
   | phone_number      |
   | appointment_date  |
   | status (Pending)  |
   +---------+---------+
             |
             v
   +-------------------+
   | AWS Lambda        |
   |-------------------|
   | Scans today's     |
   | appointments, and |
   | calls patients    |
   +---------+---------+
             |
             v
   +-------------------+
   | Amazon Connect    |
   |-------------------|
   | Contact Flow      |
   | Places outbound   |
   | call using TTS    |
   +-------------------+

Tech Stack

AWS Lambda – Core compute logic

Amazon DynamoDB – Appointment data storage

Amazon Connect – Outbound call automation

AWS CloudWatch – Logging and monitoring

Python (boto3) – AWS SDK for Lambda integration

⚙️ How It Works

The Lambda function runs (manually or scheduled via CloudWatch Event).

It scans the DynamoDB table for appointments scheduled for today.

For each record with status = Pending:

It calls Amazon Connect via the start_outbound_voice_contact() API.

The Contact Flow plays a reminder message.

Call details and errors are logged to CloudWatch

Error Handling

Common errors and fixes:

Error	Cause	Solution
DestinationNotAllowedException	Phone number not allowed or country disabled	Enable country in Amazon Connect → Telephony → Outbound calling
InvalidParameterException	Invalid phone number format	Ensure E.164 format (+1XXXXXXXXXX)
AccessDeniedException	Lambda missing permissions	Add AmazonConnect_FullAccess policy


<img width="1612" height="846" alt="Screenshot 2025-11-11 at 21 49 00" src="https://github.com/user-attachments/assets/9d2f954b-5196-48d3-b4a0-17181445bd52" />
<img width="1612" height="817" alt="Screenshot 2025-11-11 at 21 50 14" src="https://github.com/user-attachments/assets/877d9e78-e926-4711-b2a0-bb7598b50b41" />
<img width="1612" height="846" alt="Screenshot 2025-11-11 at 21 49 00" src="https://github.com/user-attachments/assets/c29e95e2-09b6-4d14-9d9b-b2e791b8487d" />
