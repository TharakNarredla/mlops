variable "environment" {
  description = "Environment name (e.g. test, prod)"
  type        = string

  validation {
    condition     = contains(["test", "staging", "prod"], var.environment)
    error_message = "Environment must be test, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric and hyphens only."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "Region must be valid AWS region format (e.g. eu-central-1)."
  }
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
