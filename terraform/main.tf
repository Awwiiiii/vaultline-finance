terraform {
  backend "s3" {
    bucket         = "vaultline-tf-state-avi"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "vaultline-lock"
  }

  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = "us-east-1" }

# The Network (VPC)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "vaultline-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  map_public_ip_on_launch = true
  enable_dns_hostnames = true  # Nodes need this to resolve the EKS API
  enable_dns_support   = true  # Nodes need this to reach AWS services

  enable_nat_gateway = true
  single_nat_gateway = true

  # Essential tags for EKS to discover subnets for Load Balancers
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# The Kubernetes Cluster (EKS)
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "vaultline-cluster"
  cluster_version = "1.30" # Upgraded to a highly supported stable version

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.public_subnets
  cluster_endpoint_public_access = true

  # Self-managed node groups often need this for administrative access
  enable_irsa = true 

  eks_managed_node_groups = {
    initial = {
      capacity_type  = "SPOT"
      instance_types = ["t3.small" , "t3.medium" ] # Cost-effective instance types
      ami_type       = "AL2_x86_64" # Explicitly use Amazon Linux 2
      
      min_size     = 1
      max_size     = 3
      desired_size = 2

      # Tagging for FinOps Tracking
      tags = {
        Project     = "VaultLine-Finance"
        Environment = "Staging"
      }
    }
  }
}