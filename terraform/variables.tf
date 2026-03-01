variable "environment" {
  description = "Environment name (e.g. test, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

variable "ec2_key_name" {
  description = "SSH key pair for EC2 (MLflow). Create in EC2 console if needed."
  type        = string
  default     = ""
}
