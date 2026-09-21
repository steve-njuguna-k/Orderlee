output "alb_dns_name" {
  description = "Public DNS name of the load balancer - point your domain's CNAME/ALIAS here"
  value       = aws_lb.app.dns_name
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  value = aws_subnet.private_app[*].id
}

output "private_db_subnet_ids" {
  value = aws_subnet.private_db[*].id
}

output "rds_endpoint" {
  description = "RDS Postgres endpoint - private, reachable only from the app tier security group"
  value       = aws_db_instance.postgres.address
}

output "db_credentials_secret_arn" {
  description = "Secrets Manager ARN holding DB host/port/name/username/password"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "django_secret_key_secret_arn" {
  value = aws_secretsmanager_secret.django_secret_key.arn
}

output "ec2_iam_role_arn" {
  value = aws_iam_role.ec2_app_role.arn
}

output "africastalking_secret_arn" {
  description = "Secrets Manager ARN holding Africa's Talking API credentials"
  value       = aws_secretsmanager_secret.africastalking_credentials.arn
}

output "django_admin_secret_arn" {
  description = "Secrets Manager ARN holding Django initial superadmin credentials"
  value       = aws_secretsmanager_secret.django_admin_credentials.arn
}

output "django_debug_parameter_arn" {
  description = "SSM Parameter ARN for Django DEBUG mode setting"
  value       = aws_ssm_parameter.django_debug.arn
}

output "django_allowed_hosts_parameter_arn" {
  description = "SSM Parameter ARN for Django ALLOWED_HOSTS setting"
  value       = aws_ssm_parameter.django_allowed_hosts.arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name where application logs are sent"
  value       = aws_cloudwatch_log_group.app.name
}

output "launch_template_id" {
  description = "ID of the launch template used by the Auto Scaling Group"
  value       = aws_launch_template.app.id
}