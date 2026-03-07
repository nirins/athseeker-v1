#!/bin/bash

# Script to set a permanent password for a Cognito user

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <username> <password>"
    echo "Example: $0 Nirin 'MyPassword123!'"
    exit 1
fi

USERNAME=$1
PASSWORD=$2
USER_POOL_ID="ap-southeast-1_ZB2oGErmf"
REGION="ap-southeast-1"

echo "Setting permanent password for user: $USERNAME"

aws cognito-idp admin-set-user-password \
  --user-pool-id "$USER_POOL_ID" \
  --username "$USERNAME" \
  --password "$PASSWORD" \
  --permanent \
  --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Password set successfully!"
    echo "You can now login with:"
    echo "  Username: $USERNAME"
    echo "  Password: $PASSWORD"
else
    echo "❌ Failed to set password"
    exit 1
fi
