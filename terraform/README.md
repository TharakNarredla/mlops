# Terraform — MLOps Infrastructure

Provisions AWS resources for the MLOps pipeline: S3 (data + artifacts), ECR, and EKS.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured (or `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

## Structure

```
terraform/
├── main.tf           # Root module, calls submodules
├── variables.tf       # Input variables
├── outputs.tf        # Outputs
├── terraform.tfvars.example  # Sample values (copy to terraform.tfvars)
├── environments/
│   └── test/         # Test environment
└── modules/
    ├── s3/           # Data + artifacts buckets (encrypted, versioned)
    ├── ecr/          # Container registry (encrypted, lifecycle policy)
    └── eks/          # Kubernetes cluster + node group
```

## Security

- S3: Block public access, AES256 encryption, versioning
- ECR: AES256 encryption, scan on push, lifecycle policy (keep last 10)
- EKS: Dedicated IAM roles, cluster logging enabled

## Usage

```bash
cd terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars

# Or use environment-specific vars (copy .example to .tfvars first)
terraform plan -var-file=environments/test/terraform.tfvars
terraform apply -var-file=environments/test/terraform.tfvars
```

## Outputs

- `s3_data_bucket` — Bucket for training data
- `s3_artifacts_bucket` — Bucket for model artifacts
- `ecr_repository_url` — ECR URL for inference images
- `eks_cluster_name` — EKS cluster name
- `eks_cluster_endpoint` — EKS API endpoint
