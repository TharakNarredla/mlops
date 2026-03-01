# EC2 instance for MLflow server
# Hosts experiment tracking; artifacts stored in S3

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_iam_role" "ec2" {
  name = "${var.name_prefix}-mlflow-ec2"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "ec2_s3" {
  name = "${var.name_prefix}-mlflow-s3"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.artifacts_bucket_name}",
          "arn:aws:s3:::${var.artifacts_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.name_prefix}-mlflow"
  role = aws_iam_role.ec2.name

  tags = var.tags
}

resource "aws_security_group" "mlflow" {
  name        = "${var.name_prefix}-mlflow"
  description = "MLflow server"
  vpc_id      = var.vpc_id

  ingress {
    description = "MLflow UI"
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-mlflow-sg" })
}

resource "aws_instance" "mlflow" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type           = "t3.small"
  subnet_id               = var.subnet_id
  vpc_security_group_ids  = [aws_security_group.mlflow.id]
  iam_instance_profile    = aws_iam_instance_profile.ec2.name
  key_name                = var.key_name != "" ? var.key_name : null
  user_data = templatefile("${path.module}/user_data.sh", {
    artifacts_bucket = var.artifacts_bucket_name
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-mlflow"
  })
}
