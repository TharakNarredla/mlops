#!/bin/bash
set -e
yum update -y
yum install -y python3 pip3

pip3 install mlflow boto3

# MLflow with S3 artifact store
mkdir -p /opt/mlflow
cat > /opt/mlflow/run.sh << 'SCRIPT'
#!/bin/bash
export MLFLOW_BACKEND_STORE_URI=sqlite:///opt/mlflow/mlflow.db
export MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://${artifacts_bucket}/mlruns
mlflow server --host 0.0.0.0 --port 5001
SCRIPT
chmod +x /opt/mlflow/run.sh

# Run as simple service (restarts on reboot)
(crontab -l 2>/dev/null; echo "@reboot /opt/mlflow/run.sh >> /var/log/mlflow.log 2>&1") | crontab -
/opt/mlflow/run.sh >> /var/log/mlflow.log 2>&1 &
