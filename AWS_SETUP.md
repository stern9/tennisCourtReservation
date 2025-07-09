# AWS Setup Guide for DynamoDB Local Testing

## Prerequisites

This project uses DynamoDB Local for development, which requires AWS CLI configuration (even with fake credentials).

## Setup Steps

### 1. Install AWS CLI

```bash
# macOS with Homebrew
brew install awscli

# Or download from AWS
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### 2. Configure AWS CLI (for local development)

```bash
aws configure
```

When prompted, enter:
- AWS Access Key ID: `fake`
- AWS Secret Access Key: `fake`
- Default region name: `us-east-1`
- Default output format: `json`

### 3. Test Configuration

```bash
# Test DynamoDB Local connection
AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake aws dynamodb list-tables --endpoint-url http://localhost:8000 --region us-east-1
```

## Running the Project

### 1. Start DynamoDB Local

```bash
# Start container
docker run -d --name tennis-dynamodb-local -p 8000:8000 amazon/dynamodb-local:latest -jar DynamoDBLocal.jar -sharedDb -inMemory

# Verify it's running
curl http://localhost:8000
```

### 2. Set Up Database

```bash
cd src
python setup_database.py
```

### 3. Run Tests

```bash
python run_tests.py
```

## Alternative: Use Environment Variables

If you prefer not to configure AWS CLI globally:

```bash
export AWS_ACCESS_KEY_ID=fake
export AWS_SECRET_ACCESS_KEY=fake
export AWS_DEFAULT_REGION=us-east-1
export DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
```

## Next Steps

Once AWS CLI is configured:
1. Run `python run_tests.py` to verify Step 1.1 implementation
2. Proceed to Step 1.2: Data Models & Validation Layer