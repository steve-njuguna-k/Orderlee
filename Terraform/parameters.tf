resource "aws_ssm_parameter" "django_debug" {
  name        = "/${var.project_name}/${var.environment}/django/DEBUG"
  description = "Django DEBUG mode setting"
  type        = "String"
  value       = tostring(var.debug)

  tags = {
    Name = "${var.project_name}-${var.environment}-django-debug"
  }
}

resource "aws_ssm_parameter" "django_allowed_hosts" {
  name        = "/${var.project_name}/${var.environment}/django/ALLOWED_HOSTS"
  description = "Comma-separated list of allowed hostnames"
  type        = "String"
  value       = join(",", var.allowed_hosts)

  tags = {
    Name = "${var.project_name}-${var.environment}-django-allowed-hosts"
  }
}