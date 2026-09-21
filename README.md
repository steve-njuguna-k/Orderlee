# Orderlee

Orderlee is a Django-based customer order management application backed by PostgreSQL.

## Running Locally with Docker Compose

The application can be run locally using Docker Compose. Docker Compose starts the following services:

* **Orderlee API** — Django application running on port `9000`
* **PostgreSQL** — PostgreSQL 17 database
* **Nginx** — Reverse proxy exposed on port `80`

### Prerequisites

Make sure the following are installed:

* [Docker](https://docs.docker.com/get-docker/)
* Docker Compose

Verify the installation:

```bash
docker --version
docker compose version
```

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
DB_NAME=orderlee
DB_USER=orderlee
DB_PASSWORD=change-me

# Django
DJANGO_SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Application
PORT=9000
```

> Do not commit the `.env` file or real credentials to source control.

The same `.env` file is loaded into the Django container through Docker Compose.

### 3. Build and Start the Application

From the project root, run:

```bash
docker compose up --build
```

This will:

1. Build the Orderlee Django image.
2. Start PostgreSQL 17.
3. Start the Django application.
4. Run Django migrations.
5. Create the application superuser using the project's `create_superadmin` management command.
6. Start the Django development server.
7. Start Nginx as the reverse proxy.

### 4. Run in the Background

To start the application in detached mode:

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
```

Expected services:

```text
orderlee
postgres
nginx
```

### 5. Access the Application

The Django application is available directly at:

```text
http://localhost:9000
```

The Nginx reverse proxy is available at:

```text
http://localhost
```

If Nginx is configured to proxy requests to the Django application, use:

```text
http://localhost
```

as the primary application URL.

### 6. View Application Logs

View logs for all services:

```bash
docker compose logs
```

Follow the logs in real time:

```bash
docker compose logs -f
```

View only the Django application logs:

```bash
docker compose logs -f orderlee
```

View PostgreSQL logs:

```bash
docker compose logs -f postgres
```

View Nginx logs:

```bash
docker compose logs -f nginx
```

### 7. Run Django Management Commands

Run Django commands inside the running application container:

```bash
docker compose exec orderlee python manage.py <command>
```

For example:

```bash
docker compose exec orderlee python manage.py createsuperuser
```

Check the Django configuration:

```bash
docker compose exec orderlee python manage.py check
```

### 8. Database Access

PostgreSQL is exposed locally on port `5432`.

From the host machine, you can connect using:

```text
Host: localhost
Port: 5432
Database: <DB_NAME>
Username: <DB_USER>
Password: <DB_PASSWORD>
```

From inside the Orderlee container, PostgreSQL should be accessed using the Docker Compose service name:

```text
Host: postgres
Port: 5432
```

Do **not** use `localhost` as the PostgreSQL host from inside the Django container because `localhost` refers to the Django container itself.

### 9. Stop the Application

Stop the running services:

```bash
docker compose down
```

This stops and removes the containers while preserving the PostgreSQL named volume.

### 10. Stop the Application and Delete the Database

To remove the containers **and** the PostgreSQL data:

```bash
docker compose down -v
```

> **Warning:** `docker compose down -v` deletes the `postgres_data` volume and therefore removes the local PostgreSQL database.

### 11. Rebuild from Scratch

If dependencies or Docker configuration have changed, rebuild the images:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

Alternatively:

```bash
docker compose up --build -d
```

## Development Notes

The Django source directory is mounted into the container:

```yaml
volumes:
  - .:/app
```

This allows local source-code changes to be reflected inside the running container.

The application container listens on:

```text
0.0.0.0:9000
```

and Docker publishes it as:

```text
localhost:9000
```

PostgreSQL data is persisted using the Docker named volume:

```yaml
postgres_data:/var/lib/postgresql/data/
```

Therefore, restarting or recreating the containers with:

```bash
docker compose down
docker compose up -d
```

does not remove the database.

## Useful Commands

### Start

```bash
docker compose up -d
```

### Build and start

```bash
docker compose up --build -d
```

### Stop

```bash
docker compose down
```

### View status

```bash
docker compose ps
```

### Follow logs

```bash
docker compose logs -f
```

### Open a shell in the Django container

```bash
docker compose exec orderlee /bin/bash
```

### Run migrations manually

```bash
docker compose exec orderlee python manage.py migrate
```

### Run tests

```bash
docker compose exec orderlee python manage.py test
```

### Remove containers and database volume

```bash
docker compose down -v
```

## CI/CD Pipeline

The Orderlee CI/CD pipeline implements a security-focused deployment workflow that validates source code, executes automated tests, scans the application and dependencies for security issues, builds and scans the container image, signs the image cryptographically, deploys it to the appropriate environment, verifies the deployment, and provides rollback and notification mechanisms.

The pipeline is organized into the following stages:

```text
validate
   ↓
test
   ↓
security
   ↓
build
   ↓
image-security
   ↓
release
   ↓
deploy
   ↓
verify
   ↓
rollback
   ↓
cleanup
   ↓
notify
```

Jobs within earlier stages must satisfy their configured conditions before dependent jobs in subsequent stages can execute.

---

## Pipeline Flow

```text
Developer
    │
    │ Git Push / Merge Request / Version Tag
    ▼
┌───────────────┐
│    VALIDATE    │
│ Lint           │
│ Django Checks  │
│ Migration Check│
└───────┬───────┘
        ▼
┌───────────────┐
│      TEST      │
│ Unit Tests     │
│ ≥ 80% Coverage │
└───────┬───────┘
        ▼
┌───────────────┐
│    SECURITY    │
│ Semgrep        │
│ Gitleaks       │
│ detect-secrets │
│ OWASP          │
│ ClamAV         │
└───────┬───────┘
        ▼
┌───────────────┐
│     BUILD      │
│ Kaniko         │
│ Docker Image   │
│ SHA256 Digest  │
└───────┬───────┘
        ▼
┌──────────────────┐
│  IMAGE SECURITY  │
│ Trivy            │
│ Vulnerability    │
│ Scan + SBOM      │
└────────┬─────────┘
         ▼
┌──────────────────┐
│      RELEASE     │
│ Cosign Sign      │
│ Cosign Verify    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│      DEPLOY       │
│ Development      │─── Ansible
│ Staging          │─── Ansible
│ Production       │─── Terraform/AWS
└────────┬─────────┘
         ▼
┌──────────────────┐
│      VERIFY       │
│ /healthz          │
│ /ready             │
│ Application Root  │
└────────┬─────────┘
         │
         ├──────── Deployment successful
         │
         ▼
┌──────────────────┐
│      CLEANUP      │
│ Remove temporary  │
│ files and secrets │
└────────┬─────────┘
         ▼
┌──────────────────┐
│      NOTIFY       │
│ Microsoft Teams   │
└──────────────────┘

Production failure
         │
         ▼
┌──────────────────┐
│      ROLLBACK     │
│ AWS ASG Instance  │
│ Refresh Rollback  │
└──────────────────┘
```

---

# 1. Validate

The `validate` stage performs early quality and configuration checks before tests or security scanning are executed.

### Jobs

| Job                     | Purpose                                             |
| ----------------------- | --------------------------------------------------- |
| `lint`                  | Checks Python formatting, imports, and code quality |
| `django-security-check` | Runs Django's deployment security checks            |
| `migration-check`       | Detects model changes without committed migrations  |

### Lint

The `lint` job runs:

* Black
* isort
* Flake8

```bash
black --check .
isort --check-only .
flake8 . --max-line-length=88
```

This ensures that the code follows the project's formatting and style standards.

### Django Security Check

The pipeline runs:

```bash
python manage.py check --deploy
```

This uses Django's deployment checks to identify configuration issues that could create security risks in a production deployment.

### Migration Check

The pipeline verifies that Django models and migration files are synchronized:

```bash
python manage.py makemigrations --check --dry-run
```

The job fails if Django detects model changes that would require new migration files.

---

# 2. Test

The `test` stage validates application functionality and enforces a minimum test coverage requirement.

### Job

```text
unit-tests
```

The job executes the Django test suite using Python's coverage tooling:

```bash
coverage run --source='.' manage.py test --noinput
```

A minimum coverage threshold of **80%** is enforced:

```bash
coverage report --fail-under=80
```

If coverage falls below 80%, the pipeline fails and subsequent dependent stages do not proceed.

The pipeline also generates:

* `coverage.xml`
* HTML coverage reports

These are stored as GitLab CI artifacts for review.

---

# 3. Security

The `security` stage performs multiple independent security checks against the application source code, secrets, dependencies, and workspace.

The pipeline uses several scanners because each tool addresses a different security concern.

### Security Jobs

| Job                      | Tool                   | Purpose                              |
| ------------------------ | ---------------------- | ------------------------------------ |
| `semgrep`                | Semgrep                | Static application security analysis |
| `gitleaks`               | Gitleaks               | Detects exposed secrets              |
| `detect-secrets`         | detect-secrets         | Secondary secret detection           |
| `owasp-dependency-check` | OWASP Dependency-Check | Dependency vulnerability analysis    |
| `clamav-antivirus-scan`  | ClamAV                 | Malware scanning                     |

### Semgrep

Semgrep performs static analysis using Python and Django security rules:

```bash
semgrep scan \
  --config=p/python \
  --config=p/django \
  --error
```

It is intended to identify potentially insecure application patterns before the application is packaged.

### Gitleaks

Gitleaks scans the repository for potentially exposed:

* API keys
* tokens
* passwords
* private keys
* other credentials

The pipeline explicitly fails when findings are detected.

### detect-secrets

`detect-secrets` provides an additional secret-detection layer using its own detection heuristics.

This reduces reliance on a single secret-scanning implementation.

### OWASP Dependency-Check

OWASP Dependency-Check analyzes third-party dependencies for known vulnerabilities.

The pipeline is configured to fail when vulnerabilities meet or exceed a **CVSS score of 7**.

### ClamAV

ClamAV recursively scans the workspace for known malicious files or embedded malware signatures.

The pipeline fails if malware is detected.

---

# 4. Build

The `build` stage creates the production container image.

### Job

```text
build-orderlee-api
```

The image is built using **Kaniko** rather than Docker-in-Docker.

This allows the pipeline to build container images without requiring a Docker daemon.

### Image Repository

The image is published to Docker Hub:

```text
stevenjugunakamau/orderlee
```

### Image Tags

Each build receives an immutable commit-based tag:

```text
<commit-short-sha>
```

Environment tags are also generated:

| Git Reference                | Image Tag |
| ---------------------------- | --------- |
| `development`                | `dev`     |
| `staging`                    | `uat`     |
| Version tag such as `v1.0.0` | `v1.0.0`  |

For example:

```text
stevenjugunakamau/orderlee:a1b2c3d
stevenjugunakamau/orderlee:dev
```

The pipeline also generates a SHA256 image digest.

Example:

```text
sha256:abcdef...
```

The digest is stored as:

```text
digest.txt
```

This digest is subsequently used by the security scanning and signing stages.

Using the digest ensures that subsequent operations reference the exact image that was built rather than relying only on a mutable tag.

---

# 5. Image Security

The `image-security` stage validates the built container image.

It consists of:

```text
trivy-scan
generate-sbom
```

## Trivy Vulnerability Scan

The `trivy-scan` job scans the immutable image digest for:

* HIGH vulnerabilities
* CRITICAL vulnerabilities

The security gate is configured with:

```bash
--severity HIGH,CRITICAL
--ignore-unfixed
--exit-code 1
```

Therefore, known fixed HIGH or CRITICAL vulnerabilities can prevent the pipeline from continuing.

Trivy also generates a comprehensive HTML security report covering:

* Vulnerabilities
* Misconfigurations
* Secrets
* Licenses

The report is stored as a CI artifact.

## SBOM Generation

The `generate-sbom` job generates a CycloneDX Software Bill of Materials.

The resulting artifact is:

```text
sbom.cdx.json
```

The SBOM provides a machine-readable inventory of the components contained within the application image and supports software supply-chain tracking.

---

# 6. Release

The `release` stage establishes image authenticity using **Cosign**.

It contains two jobs:

```text
cosign-sign-image
cosign-verify-image
```

## Image Signing

The `cosign-sign-image` job signs the immutable SHA256 image digest using a Cosign private key.

The signature includes metadata annotations such as:

* Commit SHA
* Pipeline ID
* Project path

The private signing key is supplied through GitLab CI/CD protected variables rather than being committed to the repository.

The key is removed after signing.

## Signature Verification

Before deployment, `cosign-verify-image` verifies the image signature using the corresponding public key.

The deployment therefore depends on successful signature verification.

The flow is:

```text
Build Image
     │
     ▼
Generate SHA256 Digest
     │
     ▼
Trivy Scan
     │
     ▼
Generate SBOM
     │
     ▼
Cosign Sign
     │
     ▼
Cosign Verify
     │
     ▼
Deployment
```

---

# 7. Deploy

The `deploy` stage deploys the verified image to the appropriate environment.

The deployment mechanism differs by environment.

| Environment | Deployment Method            | Trigger                      |
| ----------- | ---------------------------- | ---------------------------- |
| Development | Ansible over SSH             | Push to `development`        |
| Staging     | Ansible over SSH             | Push to `staging`            |
| Production  | Terraform + AWS Auto Scaling | Version tag, manual approval |

---

## Development Deployment

The `deploy:development` job executes the Ansible deployment playbook against the development server.

The deployment passes:

* Image repository
* Commit SHA image tag
* Image digest
* Environment name

Example:

```text
image_repository=stevenjugunakamau/orderlee
image_tag=<commit-sha>
image_digest=sha256:...
env=development
```

SSH credentials and known hosts are supplied through GitLab CI/CD variables.

---

## Staging Deployment

The `deploy:staging` job follows the same deployment model as Development but targets the Staging environment.

Deployment is performed through Ansible over SSH.

The staging deployment uses the same immutable image digest generated during the build stage.

---

## Production Deployment

Production deployments are triggered by semantic version tags matching:

```text
v1.0.0
v1.2.3
v2.0.0
```

The production deployment is **manual**.

The job uses Terraform to apply the application configuration and then retrieves the AWS Auto Scaling Group managed by Terraform.

The pipeline starts an AWS EC2 Auto Scaling instance refresh:

```text
Terraform Apply
      │
      ▼
Retrieve ALB DNS
      │
      ▼
Retrieve ASG
      │
      ▼
Start Instance Refresh
      │
      ▼
Poll Refresh Status
      │
      ▼
Successful Refresh
```

The pipeline waits for the instance refresh to complete and fails if AWS reports:

```text
Failed
```

or:

```text
Cancelled
```

The production deployment also exports the ALB endpoint as a dotenv artifact for subsequent jobs.

---

# 8. Verify

The `verify` stage performs post-deployment validation against the live environment.

The reusable `.post_deploy_template` performs three levels of verification.

## 8.1 Health Check

The pipeline repeatedly calls:

```text
/api/v1/healthz
```

and expects:

```text
HTTP 200
```

The number of retries differs by environment.

### Development

```text
6 attempts
5 seconds between attempts
```

### Staging

```text
10 attempts
5 seconds between attempts
```

### Production

```text
12 attempts
10 seconds between attempts
```

This allows newly deployed instances time to become healthy.

---

## 8.2 API Smoke Test

The pipeline calls:

```text
/api/v1/ready
```

and validates that the JSON response contains:

```json
{
  "status": "ok"
}
```

This provides a basic application-level assertion rather than relying only on HTTP availability.

---

## 8.3 Root Endpoint Check

Finally, the pipeline verifies that the application's root endpoint responds successfully.

The verification flow is therefore:

```text
Deployment
    │
    ▼
/api/v1/healthz
    │
    ▼
/api/v1/ready
    │
    ▼
/
    │
    ▼
Deployment Verified
```

A failure in post-deployment verification causes the verification job to fail.

---

# 9. Rollback

The `rollback` stage provides a manual production recovery mechanism.

### Job

```text
rollback:production
```

Rollback is available for version-tagged production pipelines and must be manually triggered.

The job uses AWS Auto Scaling's instance refresh rollback capability to restore the previous launch template configuration.

The process is:

```text
Production Deployment
        │
        ▼
Deployment Failure / Detected Issue
        │
        ▼
Operator manually triggers rollback
        │
        ▼
AWS Instance Refresh Rollback
        │
        ▼
Previous Launch Template Version
        │
        ▼
Production Restored
```

The rollback job monitors the AWS rollback operation and waits for:

```text
RollbackSuccessful
```

If AWS reports:

```text
RollbackFailed
```

the pipeline exits with a failure and requires manual intervention.

### Important

After a rollback, the running infrastructure may differ from the image configuration represented in the current Terraform configuration.

The Terraform configuration should therefore be reconciled with the restored production version before the next production deployment.

---

# 10. Cleanup

The `cleanup` stage sanitizes the CI runner workspace.

Cleanup is configured to execute regardless of whether the preceding pipeline stages succeed or fail.

Temporary files removed include:

```text
./tmp
./coverage
./.cache
./cosign.key
./cosign.pub
```

This helps prevent sensitive material and temporary build artifacts from remaining in the runner workspace.

Cleanup is executed separately for:

* Development
* Staging
* Production

---

# 11. Notify

The final stage broadcasts pipeline status to Microsoft Teams.

Notifications are sent for:

* Successful deployments
* Failed deployments

The notification contains information including:

* Project
* Environment
* Branch or tag
* Commit SHA
* Triggered by
* Commit title
* GitLab pipeline ID
* Pipeline URL

Example notification flow:

```text
Pipeline
   │
   ├── Successful ──► 🟢/🚀/🎉 Teams Notification
   │
   └── Failed ──────► 🔴/⚠️/🚨 Teams Notification
```

The notification payload is generated as a Microsoft Teams Adaptive Card.

`jq` is used to safely construct the JSON payload so that commit messages and other dynamic values are correctly escaped.

The webhook request uses retry handling:

```text
3 attempts
3 seconds between retries
```

---

# Pipeline Execution Rules

The pipeline does not execute for every Git reference.

Pipelines are created for:

### Merge Requests

```text
merge_request_event
```

Merge requests run the validation, testing, and application security checks.

### Development

```text
development
```

Pushes to the `development` branch execute the development CI/CD workflow and deploy to the Development environment.

### Staging

```text
staging
```

Pushes to the `staging` branch execute the staging CI/CD workflow and deploy to the Staging environment.

### Version Tags

Semantic version tags beginning with `v` trigger the release and production workflow.

Examples:

```text
v1.0.0
v1.1.0
v2.0.0
```

Production deployment remains a manual action even when a valid release tag is created.

Other branches and references are excluded by the top-level workflow rules.

---

# Environment Deployment Matrix

| Environment | Git Reference | Deployment          | Verification           | Rollback                |
| ----------- | ------------- | ------------------- | ---------------------- | ----------------------- |
| Development | `development` | Ansible / SSH       | HTTP + API smoke tests | —                       |
| Staging     | `staging`     | Ansible / SSH       | HTTP + API smoke tests | —                       |
| Production  | `vX.Y.Z` tag  | Terraform + AWS ASG | HTTP + API smoke tests | Manual AWS ASG rollback |

---

# Security Controls

The pipeline implements security controls at multiple points in the software delivery lifecycle.

```text
Source Code
    │
    ├── Black / isort / Flake8
    ├── Django deployment checks
    └── Migration validation
    │
    ▼
Application
    │
    ├── Unit tests
    └── ≥80% coverage
    │
    ▼
Security
    │
    ├── Semgrep
    ├── Gitleaks
    ├── detect-secrets
    ├── OWASP Dependency-Check
    └── ClamAV
    │
    ▼
Container
    │
    ├── Kaniko build
    ├── SHA256 digest
    ├── Trivy
    └── CycloneDX SBOM
    │
    ▼
Release
    │
    ├── Cosign signing
    └── Cosign verification
    │
    ▼
Deployment
    │
    ├── Ansible
    └── Terraform / AWS
    │
    ▼
Runtime
    │
    ├── Health check
    ├── Readiness check
    └── API smoke test
```

This creates multiple gates before an image reaches production.

---

# Container Image Lifecycle

The application image follows an immutable artifact lifecycle:

```text
Source Code
     │
     ▼
Kaniko Build
     │
     ▼
Docker Hub
     │
     ├── Commit SHA Tag
     ├── Environment Tag
     └── SHA256 Digest
             │
             ▼
       Trivy Scan
             │
             ▼
          SBOM
             │
             ▼
       Cosign Sign
             │
             ▼
      Cosign Verify
             │
             ▼
         Deploy
```

The SHA256 digest provides a stable reference to the exact image produced by the pipeline.

---

# CI/CD Secrets

Sensitive values are supplied through GitLab CI/CD variables rather than being hardcoded in the repository.

Examples include:

```text
DOCKERHUB_USERNAME
DOCKERHUB_PASSWORD
COSIGN_PRIVATE_KEY
COSIGN_PUBLIC_KEY
DEV_SSH_PRIVATE_KEY
DEV_KNOWN_HOSTS
STAGING_SSH_PRIVATE_KEY
STAGING_KNOWN_HOSTS
TEAMS_WEBHOOK_URL
AWS credentials
```

Secrets should be configured as protected and masked GitLab CI/CD variables where appropriate.

Private signing keys and SSH private keys must never be committed to the repository.

---

# Summary

The Orderlee CI/CD pipeline follows a gated software delivery model:

```text
Validate
   ↓
Test
   ↓
Security Scan
   ↓
Build
   ↓
Container Security
   ↓
Sign & Verify
   ↓
Deploy
   ↓
Verify
   ↓
Cleanup
   ↓
Notify
```

Production releases additionally provide a manual deployment gate and a manual AWS Auto Scaling rollback mechanism.

This workflow provides automated code-quality enforcement, test coverage validation, application and dependency security scanning, container security scanning, SBOM generation, cryptographic image verification, environment-specific deployment, post-deployment testing, production rollback, workspace cleanup, and operational notifications.

## Project Assumptions

The following assumptions were made during the project to provide a realistic CI/CD, deployment, and infrastructure design for Orderlee:

* **Early-stage startup with a growing customer base**
  Orderlee is assumed to be an early-stage startup with a growing customer base. The infrastructure and CI/CD design therefore prioritizes automation, security, reliability, and the ability to scale as adoption increases, while avoiding unnecessary operational complexity.

* **Hybrid infrastructure environment**
  Orderlee is assumed to operate a hybrid environment consisting of both **on-premises servers and cloud infrastructure**. The deployment strategy therefore uses different tools depending on the target environment.

* **GitLab as the Version Control System**
  Orderlee is assumed to store its application source code and configuration in **GitLab**. GitLab CI/CD is therefore used to implement the CI/CD pipeline, including validation, testing, security scanning, container image creation, release, deployment, and verification.

* **Development & Staging environment — On-premises**
  The development & staging environment are assumed to run on **on-premises servers**. **Ansible** is therefore used for application deployment because it provides a straightforward and agentless approach for managing and deploying applications to existing servers.

* **Development & Staging environment — DB, Docker & Nginx Already Setup**
  The Development and Staging environments already have the required database, Docker Engine, and Nginx infrastructure provisioned and configured. Therefore, the assessment focuses on deploying and updating the application container through Ansible rather than provisioning these underlying services.

* **Production environment — AWS Cloud**
  The production environment is assumed to run in **Amazon Web Services (AWS)**. **Terraform** is therefore used for Infrastructure as Code (IaC) and production infrastructure deployment, providing a declarative and reproducible way to provision and manage AWS resources.

### Environment and Deployment Model

| Environment | Infrastructure | Deployment Tool | Primary Purpose                                      |
| ----------- | -------------- | --------------- | ---------------------------------------------------- |
| Development | On-premises    | Ansible         | Development and integration testing                  |
| Staging     | On-premises    | Ansible         | Pre-production validation                            |
| Production  | AWS Cloud      | Terraform       | Production infrastructure and application deployment |

These assumptions are intended to provide the context behind the technology and deployment decisions made in this project. If the actual Orderlee infrastructure differs from these assumptions, the deployment architecture and tooling can be adjusted accordingly.

---

## One Improvement I Would Make With More Time

### Separate Nginx and Django Containers / Services

**Current:**
Nginx and Django currently run alongside each other on the same EC2 instances. This keeps the deployment architecture relatively simple, but it couples the web-serving layer with the application compute layer.

**Improvement:**
Consider separating static asset delivery and application compute. Static assets such as CSS, JavaScript, and images could be served from **Amazon S3 through Amazon CloudFront**, reducing the need to serve static content directly from the EC2 instances.

For the application layer, the containerized Django service could alternatively be migrated to **Amazon ECS with Fargate** or **Amazon EKS**. This would decouple the application from the underlying EC2 hosts, reduce manual server patching and maintenance, and provide more automated container deployment and rollout capabilities.

This would result in a more independently scalable architecture where:

* **Amazon S3** stores static assets.
* **Amazon CloudFront** provides global content delivery and caching.
* **ECS Fargate or EKS** runs the Django application containers.
* Application deployments can be rolled out independently of the underlying compute infrastructure.
* Infrastructure and application scaling can be managed separately.

This improvement would be considered as the application and customer base grow, rather than being required for the initial deployment architecture.
