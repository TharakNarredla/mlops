variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "data_bucket_name" {
  description = "S3 bucket name for training data"
  type        = string
}

variable "artifacts_bucket_name" {
  description = "S3 bucket name for model artifacts"
  type        = string
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default     = {}
}
