output "instance_id" {
  description = "EC2 instance ID for MLflow server"
  value       = aws_instance.mlflow.id
}

output "public_ip" {
  description = "Public IP of MLflow server (UI at http://<ip>:5001)"
  value       = aws_instance.mlflow.public_ip
}

output "mlflow_url" {
  description = "MLflow UI URL"
  value       = "http://${aws_instance.mlflow.public_ip}:5001"
}
