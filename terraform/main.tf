locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  })
}

module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

module "ecr" {
  source = "./modules/ecr"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

module "eks" {
  source = "./modules/eks"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

module "sagemaker" {
  source = "./modules/sagemaker"

  name_prefix          = local.name_prefix
  data_bucket_name     = module.s3.data_bucket_name
  artifacts_bucket_name = module.s3.artifacts_bucket_name
  tags                 = local.common_tags
}

module "ec2_mlflow" {
  source = "./modules/ec2_mlflow"

  name_prefix           = local.name_prefix
  vpc_id                = module.eks.vpc_id
  subnet_id             = module.eks.public_subnet_ids[0]
  artifacts_bucket_name = module.s3.artifacts_bucket_name
  key_name              = var.ec2_key_name
  tags                  = local.common_tags
}
