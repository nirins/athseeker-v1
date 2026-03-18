import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client("sns")


def lambda_handler(event, context):
    """
    Cognito PostConfirmation trigger — publishes an SNS notification
    when a new user confirms their account.
    """
    try:
        trigger_source = event.get("triggerSource", "")
        user_attributes = event.get("request", {}).get("userAttributes", {})
        username = event.get("userName", "unknown")
        email = user_attributes.get("email", "unknown")
        user_pool_id = event.get("userPoolId", "unknown")

        # Only notify on actual sign-up confirmation, not admin-created users
        if trigger_source not in ("PostConfirmation_ConfirmSignUp",):
            logger.info(f"Skipping notification for trigger source: {trigger_source}")
            return event

        topic_arn = os.environ["SNS_TOPIC_ARN"]

        message = (
            f"New user signed up to ATHSeeker\n\n"
            f"Username: {username}\n"
            f"Email: {email}\n"
            f"User Pool: {user_pool_id}\n"
            f"Trigger: {trigger_source}"
        )

        sns_client.publish(
            TopicArn=topic_arn,
            Subject="New ATHSeeker Sign Up",
            Message=message,
        )

        logger.info(f"SNS notification sent for new user: {username}")

    except Exception as e:
        # Log but don't raise — we must return event to not block sign-up
        logger.error(f"Failed to send SNS notification: {e}")

    return event
