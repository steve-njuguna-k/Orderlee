#!/bin/bash
set -euxo pipefail

# ---- Base packages ----
dnf update -y
dnf install -y docker jq awscli

systemctl enable docker
systemctl start docker

curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# ---- Pull secrets from AWS Secrets Manager at boot ----
DB_SECRET_JSON=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${db_secret_name}" \
  --query SecretString --output text)

DJANGO_SECRET_KEY=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${django_secret_name}" \
  --query SecretString --output text)

AFRICASTALKING_SECRET_JSON=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${africastalking_secret_name}" \
  --query SecretString --output text)

DJANGO_ADMIN_SECRET_JSON=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${django_admin_secret_name}" \
  --query SecretString --output text)

# ---- Fetch non-sensitive parameters from SSM Parameter Store ----
DEBUG=$(aws ssm get-parameter \
  --region "${aws_region}" \
  --name "${django_debug_param_name}" \
  --query Parameter.Value --output text)

ALLOWED_HOSTS=$(aws ssm get-parameter \
  --region "${aws_region}" \
  --name "${django_allowed_hosts_param_name}" \
  --query Parameter.Value --output text)

# ---- Extract DB credentials ----
DB_HOST=$(echo "$DB_SECRET_JSON" | jq -r .host)
DB_PORT=$(echo "$DB_SECRET_JSON" | jq -r .port)
DB_NAME=$(echo "$DB_SECRET_JSON" | jq -r .dbname)
DB_USER=$(echo "$DB_SECRET_JSON" | jq -r .username)
DB_PASSWORD=$(echo "$DB_SECRET_JSON" | jq -r .password)

# ---- Extract Africa's Talking credentials ----
AT_USERNAME=$(echo "$AFRICASTALKING_SECRET_JSON" | jq -r .AT_USERNAME)
AT_API_KEY=$(echo "$AFRICASTALKING_SECRET_JSON" | jq -r .AT_API_KEY)
AT_SMS_SHORTCODE=$(echo "$AFRICASTALKING_SECRET_JSON" | jq -r .AT_SMS_SHORTCODE)

# ---- Extract Django Super Admin credentials ----
DJANGO_ADMIN_USERNAME=$(echo "$DJANGO_ADMIN_SECRET_JSON" | jq -r .DJANGO_ADMIN_USERNAME)
DJANGO_ADMIN_EMAIL=$(echo "$DJANGO_ADMIN_SECRET_JSON" | jq -r .DJANGO_ADMIN_EMAIL)
DJANGO_ADMIN_PASSWORD=$(echo "$DJANGO_ADMIN_SECRET_JSON" | jq -r .DJANGO_ADMIN_PASSWORD)

mkdir -p /opt/app
cat > /opt/app/.env <<EOF
DEBUG=$DEBUG
ALLOWED_HOSTS=$ALLOWED_HOSTS

SECRET_KEY=$DJANGO_SECRET_KEY
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

AT_USERNAME=$AT_USERNAME
AT_API_KEY=$AT_API_KEY
AT_SMS_SHORTCODE=$AT_SMS_SHORTCODE

DJANGO_ADMIN_USERNAME=$DJANGO_ADMIN_USERNAME
DJANGO_ADMIN_EMAIL=$DJANGO_ADMIN_EMAIL
DJANGO_ADMIN_PASSWORD=$DJANGO_ADMIN_PASSWORD
EOF
chmod 600 /opt/app/.env

# ---- nginx reverse proxy config -> forwards to django on 8000 ----
mkdir -p /opt/app/nginx
cat > /opt/app/nginx/default.conf <<'EOF'
server {
    listen 80;

    location /healthz {
        return 200 "ok";
        add_header Content-Type text/plain;
    }

    location / {
        proxy_pass http://orderlee:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# ---- docker-compose: nginx + django on a shared internal network ----
cat > /opt/app/docker-compose.yml <<EOF
services:
  orderlee:
    image: ${app_container_image}
    restart: always
    env_file: /opt/app/.env
    expose:
      - "9000:9000"
    logging:
      driver: awslogs
      options:
        awslogs-region: ${aws_region}
        awslogs-group: ${log_group_name}
        awslogs-stream: orderlee

  nginx:
    image: ${nginx_container_image}
    restart: always
    volumes:
      - /opt/app/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - "80:80"
    depends_on:
      - orderlee
    logging:
      driver: awslogs
      options:
        awslogs-region: ${aws_region}
        awslogs-group: ${log_group_name}
        awslogs-stream: nginx
EOF

cd /opt/app
docker-compose up -d