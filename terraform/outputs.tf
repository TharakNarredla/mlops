output "s3_data_bucket" {
  description = "S3 bucket for training data"
  value       = module.s3.data_bucket_name
}

output "s3_artifacts_bucket" {
  description = "S3 bucket for model artifacts"
  value       = module.s3.artifacts_bucket_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for inference images"
  value       = module.ecr.repository_url
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "sagemaker_execution_role_arn" {
  description = "SageMaker execution role ARN for training jobs"
  value       = module.sagemaker.execution_role_arn
}

output "mlflow_url" {
  description = "MLflow UI URL (EC2)"
  value       = module.ec2_mlflow.mlflow_url
}

output "mlflow_ec2_public_ip" {
  description = "MLflow EC2 instance public IP"
  value       = module.ec2_mlflow.public_ip
}
