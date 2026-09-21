resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%^&*()-_=+"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}/${var.environment}/db-credentials"
  description = "Master credentials and connection info for the ${var.project_name} RDS Postgres instance"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    dbname   = var.db_name
  })
}

# Django's SECRET_KEY - generated once, stored only in Secrets Manager,
# fetched by the app at container start. Never baked into the AMI or image.
resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

resource "aws_secretsmanager_secret" "django_secret_key" {
  name        = "${var.project_name}/${var.environment}/django-secret-key"
  description = "Django SECRET_KEY for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-${var.environment}-django-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "django_secret_key" {
  secret_id     = aws_secretsmanager_secret.django_secret_key.id
  secret_string = random_password.django_secret_key.result
}

resource "aws_secretsmanager_secret" "africastalking_credentials" {
  name        = "${var.project_name}/${var.environment}/africastalking"
  description = "Africa's Talking API credentials for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-${var.environment}-africastalking"
  }
}

resource "aws_secretsmanager_secret_version" "africastalking_credentials" {
  secret_id = aws_secretsmanager_secret.africastalking_credentials.id

  secret_string = jsonencode({
    AT_USERNAME      = var.at_username
    AT_API_KEY       = var.at_api_key
    AT_SMS_SHORTCODE = var.at_sms_shortcode
  })
}

# Generate a secure password automatically rather than using weak plain text
resource "random_password" "django_admin_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+"
}

resource "aws_secretsmanager_secret" "django_admin_credentials" {
  name        = "${var.project_name}/${var.environment}/django-admin-credentials"
  description = "Django initial superadmin account credentials for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-${var.environment}-django-admin-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "django_admin_credentials" {
  secret_id = aws_secretsmanager_secret.django_admin_credentials.id

  secret_string = jsonencode({
    DJANGO_ADMIN_USERNAME = var.django_admin_username
    DJANGO_ADMIN_EMAIL    = var.django_admin_email
    DJANGO_ADMIN_PASSWORD = random_password.django_admin_password.result
  })
}