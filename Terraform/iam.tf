data "aws_caller_identity" "current" {}

resource "aws_iam_role" "ec2_app_role" {
  name = "${var.project_name}-${var.environment}-ec2-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-app-role"
  }
}

# Read-only access to exactly the two secrets this app needs - nothing else.
resource "aws_iam_policy" "secrets_read" {
  name        = "${var.project_name}-${var.environment}-secrets-read"
  description = "Allow reading only this app's own DB credentials and Django secret key"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "ReadAppSecretsOnly"
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.db_credentials.arn,
        aws_secretsmanager_secret.django_secret_key.arn
      ]
    }]
  })
}

# Write access scoped to this app's own CloudWatch log group only.
resource "aws_iam_policy" "app_logs" {
  name        = "${var.project_name}-${var.environment}-app-logs"
  description = "Allow writing application logs to this app's CloudWatch log group only"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "WriteAppLogsOnly"
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ]
      Resource = [
        "${aws_cloudwatch_log_group.app.arn}:*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_read" {
  role       = aws_iam_role.ec2_app_role.name
  policy_arn = aws_iam_policy.secrets_read.arn
}

resource "aws_iam_role_policy_attachment" "app_logs" {
  role       = aws_iam_role.ec2_app_role.name
  policy_arn = aws_iam_policy.app_logs.arn
}

# AWS-managed policy used ONLY to enable Session Manager (SSM) as a
# replacement for SSH - it is itself scoped to SSM's own control-plane
# actions, not a blanket wildcard over unrelated services. This lets you
# manage the instance with zero open inbound SSH ports.
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_app_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_app_profile" {
  name = "${var.project_name}-${var.environment}-ec2-app-profile"
  role = aws_iam_role.ec2_app_role.name
}
