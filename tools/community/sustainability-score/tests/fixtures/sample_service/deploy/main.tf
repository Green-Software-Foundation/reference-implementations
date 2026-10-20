provider "aws" {
  region = "us-east-1"
}

resource "aws_autoscaling_group" "web" {
  desired_capacity = 12
  max_size         = 12
  min_size         = 12
}

resource "aws_instance" "worker" {
  instance_type = "m5.12xlarge"
  ami           = "ami-123456"
}
