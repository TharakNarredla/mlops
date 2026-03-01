output "data_bucket_name" {
  description = "Name of the data S3 bucket"
  value       = aws_s3_bucket.data.id
}

output "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.id
}
