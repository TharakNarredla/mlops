# Terraform — MLOps Infrastructure

Provisions AWS resources for the MLOps pipeline: S3 (data + artifacts), ECR, and EKS.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured (or `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

## Structure

```
terraform/
├── main.tf           # Root module, calls submodules
├── variables.tf     # Input variables
├── outputs.tf       # Outputs
├── terraform.tfvars.example
├── environments/
│   └── test/
└── modules/
    ├── s3/           # Data + artifacts buckets (encrypted, versioned)
    ├── sagemaker/    # SageMaker execution role for training jobs
    ├── ec2_mlflow/   # EC2 instance for MLflow server
    ├── ecr/          # Container registry (encrypted, lifecycle policy)
    └── eks/          # Kubernetes cluster + node group (shared VPC)
```

## Diagram Alignment

Matches the architecture diagram:
- **S3** → data + artifacts
- **SageMaker** → execution role for training (train.py uses this role)
- **EC2** → MLflow server (artifacts in S3)
- **ECR** → Docker images
- **EKS** → inference API pods

## Security

- S3: Block public access, AES256 encryption, versioning
- SageMaker: IAM role with S3 access only
- EC2: IAM role with S3 artifacts access, security group (5001, 22)
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
- `sagemaker_execution_role_arn` — Role for SageMaker training jobs
- `mlflow_url` — MLflow UI (EC2)
- `ecr_repository_url` — ECR URL for inference images
- `eks_cluster_name` — EKS cluster name
- `eks_cluster_endpoint` — EKS API endpoint
