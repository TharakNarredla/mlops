output "execution_role_arn" {
  description = "SageMaker execution role ARN for training jobs"
  value       = aws_iam_role.sagemaker.arn
}

output "execution_role_name" {
  description = "SageMaker execution role name"
  value       = aws_iam_role.sagemaker.name
}
