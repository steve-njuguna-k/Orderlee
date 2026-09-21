data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/${var.project_name}/${var.environment}/app"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-${var.environment}-app-logs"
  }
}

resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-${var.environment}-app-"
  image_id      = data.aws_ssm_parameter.al2023_ami.value
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_app_profile.name
  }

  vpc_security_group_ids = [aws_security_group.app.id]

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh.tpl", {
    aws_region                      = var.aws_region
    db_secret_name                  = aws_secretsmanager_secret.db_credentials.name
    django_secret_name              = aws_secretsmanager_secret.django_secret_key.name
    africastalking_secret_name      = aws_secretsmanager_secret.africastalking_credentials.name
    django_admin_secret_name        = aws_secretsmanager_secret.django_admin_credentials.name
    django_debug_param_name         = aws_ssm_parameter.django_debug.name
    django_allowed_hosts_param_name = aws_ssm_parameter.django_allowed_hosts.name
    app_container_image             = var.app_container_image
    nginx_container_image           = var.nginx_container_image
    log_group_name                  = aws_cloudwatch_log_group.app.name
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-${var.environment}-app"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  name                      = "${var.project_name}-${var.environment}-app-asg"
  vpc_zone_identifier       = aws_subnet.private_app[*].id
  min_size                  = var.asg_min_size
  max_size                  = var.asg_max_size
  desired_capacity          = var.asg_desired_capacity
  health_check_type         = "ELB"
  health_check_grace_period = 120

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app.arn]

  tag {
    key                 = "Name"
    value               = "${var.project_name}-${var.environment}-app"
    propagate_at_launch = true
  }
}

# ==========================================
# Bastion Host Security Group
# ==========================================

resource "aws_security_group" "bastion" {
  name        = "${var.project_name}-${var.environment}-bastion-sg"
  description = "Security group for the Bastion host"
  vpc_id      = aws_vpc.main.id

  # Optional SSH ingress rule restricted to your specific IP address.
  # If using SSM Session Manager exclusively, you can leave inbound empty.
  ingress {
    description = "SSH from allowed IP ranges"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.bastion_allowed_cidr_blocks
  }

  egress {
    description = "Allow all outbound traffic (needed for SSM Agent & package downloads)"
    from_port   = 0
    to_port     = 0
    protocol    ="-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-bastion-sg"
  }
}

# ==========================================
# Allow Inbound Traffic to App & DB SG from Bastion
# ==========================================

resource "aws_security_group_rule" "app_allow_bastion_ssh" {
  type                     = "ingress"
  description              = "Allow SSH access from Bastion host"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  security_group_id        = aws_security_group.app.id
  source_security_group_id = aws_security_group.bastion.id
}

resource "aws_security_group_rule" "rds_allow_bastion" {
  type                     = "ingress"
  description              = "Allow PostgreSQL access from Bastion host"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db.id
  source_security_group_id = aws_security_group.bastion.id
}

# ==========================================
# IAM Role for Bastion (SSM Access Enabled)
# ==========================================

resource "aws_iam_role" "bastion_role" {
  name = "${var.project_name}-${var.environment}-bastion-role"

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

  tags = {
    Name = "${var.project_name}-${var.environment}-bastion-role"
  }
}

# Attach AWS Managed Policy for Systems Manager Session Manager
resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  role       = aws_iam_role.bastion_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion_profile" {
  name = "${var.project_name}-${var.environment}-bastion-profile"
  role = aws_iam_role.bastion_role.name
}

# ==========================================
# Bastion EC2 Instance
# ==========================================

resource "aws_instance" "bastion" {
  ami                  = data.aws_ssm_parameter.al2023_ami.value
  instance_type        = "t3.micro"
  subnet_id            = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.bastion.id]
  iam_instance_profile = aws_iam_instance_profile.bastion_profile.name
  key_name = var.aws_ssh_admin_key_file != "" ? var.aws_ssh_admin_key_file : null

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y htop nc telnet postgresql15
              EOF

  tags = {
    Name = "${var.project_name}-${var.environment}-bastion"
  }
}