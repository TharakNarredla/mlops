variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for EC2 instance"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instance"
  type        = string
}

variable "artifacts_bucket_name" {
  description = "S3 bucket for MLflow artifacts"
  type        = string
}

variable "key_name" {
  description = "SSH key pair name for EC2 access (create in EC2 console if needed)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default     = {}
}
