# AWS Deployment Guide — AI Finance Assistant

This guide walks you through deploying the AI Finance Assistant to AWS EC2 with a public URL. By the end you will have two services running:

| Service | URL | What it is |
|---------|-----|-----------|
| **FastAPI** | `http://<EC2_IP>:8000/docs` | Interactive API documentation (Swagger UI) |
| **Streamlit** | `http://<EC2_IP>:8501` | Original chat/tab UI |

---

## Architecture

```
Your Browser
    │
    ├── :8000  →  FastAPI (uvicorn)   ─── LangGraph Router ──┬── FinanceQA Agent (RAG + OpenAI)
    │                                                         ├── Market Agent (yfinance)
    └── :8501  →  Streamlit UI        ─── LangGraph Router ──┼── Portfolio Agent
                                                              └── Goal Agent
Both services run inside Docker containers on a single EC2 t2.micro instance.
```

---

## Prerequisites Checklist

Before starting, confirm you have these:

- [ ] AWS personal account (free tier eligible)
- [ ] OpenAI API key (`sk-...`)
- [ ] This project pushed to a **public** GitHub repository
- [ ] Docker Desktop installed (Phase 0)
- [ ] AWS CLI installed (Phase 1)
- [ ] AWS CLI configured with personal profile (Phase 2)

---

## Phase 0: Install Docker Desktop

> **Why?** Docker packages your app and all its Python dependencies into a portable container image. You build it once locally, then run the exact same image on EC2. No "works on my machine" problems.

1. Go to https://www.docker.com/products/docker-desktop/ and download the Mac (Apple Silicon or Intel) installer.
2. Open the `.dmg` and drag Docker to Applications.
3. Launch Docker Desktop from your Applications folder. Wait for the whale icon in the menu bar to stop animating.
4. Verify it works:
   ```bash
   docker --version      # e.g. Docker version 26.x.x
   docker ps             # should return an empty table, not an error
   ```

---

## Phase 1: Install AWS CLI

> **Why?** The AWS CLI lets you interact with AWS services (EC2, IAM, etc.) directly from your terminal. You'll use it to verify your credentials are set up correctly. The actual EC2 setup in this guide is done through the AWS Console (browser), so CLI usage here is minimal — but it's good practice to have it configured.

### Step 1.1 — Check if it's already installed

```bash
aws --version
```

- If you see something like `aws-cli/2.x.x Python/3.x.x ...` → **skip to Phase 2**.
- If you get `command not found` → follow the steps below.

### Step 1.2 — Install AWS CLI v2 on Mac

**Option A: Using the official PKG installer (recommended — no package manager needed)**

1. Download the installer:
   ```bash
   curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
   ```
2. Run the installer:
   ```bash
   sudo installer -pkg AWSCLIV2.pkg -target /
   ```
3. Clean up the downloaded file:
   ```bash
   rm AWSCLIV2.pkg
   ```

**Option B: Using Homebrew (if you already have Homebrew installed)**

```bash
brew install awscli
```

### Step 1.3 — Verify the installation

Open a **new terminal window** (important — the shell needs to reload its PATH) and run:

```bash
aws --version
```

Expected output:
```
aws-cli/2.x.x Python/3.x.x Darwin/...
```

---

## Phase 2: Configure AWS CLI (without affecting work credentials)

> **Why?** The AWS CLI lets you control AWS from your terminal. Right now you have it installed but not pointed at your personal account. We need to add your personal credentials **without touching whatever your work uses**.

### Will this conflict with my work AWS setup?

Short answer: **No, as long as you use a named profile** — which is exactly what this guide does.

The AWS CLI stores credentials in `~/.aws/credentials`. Each entry is a **profile**. Your work may use the `[default]` profile (or its own named profile). By creating a separate `[personal]` profile, the two are completely isolated:

```
~/.aws/credentials

[default]          ← your work credentials, untouched
access_key_id = ...
secret_access_key = ...

[personal]         ← what we add now, separate
access_key_id = ...
secret_access_key = ...
```

Every command in this guide uses `--profile personal`, so your work profile is never affected. You can verify your current setup first:

```bash
cat ~/.aws/credentials    # see what profiles already exist
```

If the file does not exist yet, that is fine — you have no credentials configured, and we are starting fresh.

---

### Step 2.1 — Create an IAM user in the AWS Console

> **Why IAM instead of root?** Your AWS root account has unlimited power (including deleting your entire account). IAM users have scoped permissions. Best practice is to never use root for day-to-day work.

1. Sign in to https://console.aws.amazon.com with your **personal** account.
2. In the search bar, type **IAM** and open the IAM service.
3. Click **Users** → **Create user**.
4. Username: `ai-finance-deploy` → Next.
5. Select **Attach policies directly** → search and check `AdministratorAccess` → Next → Create user.
   > (For a portfolio/personal project, AdministratorAccess is fine. In a real company you would scope this to only EC2 and ECR.)
6. Click the new user → **Security credentials** tab → **Create access key**.
7. Choose **Command Line Interface (CLI)** → Next → Create.
8. **Copy both the Access Key ID and Secret Access Key now** — you cannot see the secret again.

### Step 2.2 — Add a named profile (safe — does not touch work credentials)

```bash
aws configure --profile personal
```

You will be prompted for:
```
AWS Access Key ID:     <paste your Access Key ID>
AWS Secret Access Key: <paste your Secret Access Key>
Default region name:   us-east-1
Default output format: json
```

This adds a `[personal]` block to `~/.aws/credentials` and leaves any existing `[default]` (work) block completely unchanged.

### Step 2.3 — Verify it works

```bash
aws sts get-caller-identity --profile personal
```

Expected output (account ID will be your own personal account):
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/ai-finance-deploy"
}
```

> **Tip:** If you want to avoid typing `--profile personal` every time in a terminal session, run `export AWS_PROFILE=personal`. This only lasts for that session — your next terminal window will be back to normal.

---

## Phase 3: Push Code to GitHub

> **Why?** You will `git clone` your project directly onto the EC2 instance. That is the simplest way to get files onto the server without manually copying them.

1. Create a new **public** repository on GitHub (e.g. `ai-finance-assistant`).
2. Push your code:
   ```bash
   git remote add origin https://github.com/<your-username>/ai-finance-assistant.git
   git push -u origin main
   ```
3. Confirm `.env` is **not** pushed — check that `.env` is listed in `.gitignore`.

---

## Phase 4: Test Docker Locally First

> **Why?** Catching issues locally is much faster than debugging on a remote server. If `docker-compose up` works on your Mac, it will work on EC2.

### Step 4.1 — Create your local `.env` file

```bash
# In the project root (this file is gitignored — never commit it)
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

### Step 4.2 — Build and run

```bash
docker-compose up --build
```

This will:
- Build a Docker image from `Dockerfile` (~3–5 minutes first time)
- Start two containers: `api` (port 8000) and `ui` (port 8501)

### Step 4.3 — Test both services

Open in your browser:
- **FastAPI docs**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501

Try the `/api/market/{ticker}` endpoint in Swagger with `AAPL`.

### Step 4.4 — Stop the containers

```bash
docker-compose down
```

---

## Phase 5: Launch an EC2 Instance

> **Why EC2?** EC2 is a virtual machine you rent by the hour. It runs your Docker containers 24/7 so others can access your app anytime. We use `t2.micro` which is in the **AWS Free Tier** (750 hours/month free for 12 months).

### Step 5.1 — Create a Key Pair

> **Why?** Key pairs are how you SSH (securely log in) to your EC2 instance. AWS keeps the public key on the instance; you keep the private key (`.pem` file) on your laptop.

1. In the AWS Console, go to **EC2** (search bar).
2. In the left sidebar: **Network & Security → Key Pairs**.
3. Click **Create key pair**:
   - Name: `ai-finance-key`
   - Key pair type: **RSA**
   - Private key file format: **.pem** (for Mac/Linux)
4. Click **Create key pair** — a `.pem` file downloads automatically.
5. Move it somewhere safe and set permissions:
   ```bash
   mv ~/Downloads/ai-finance-key.pem ~/.ssh/
   chmod 400 ~/.ssh/ai-finance-key.pem
   ```

### Step 5.2 — Launch the Instance

1. In EC2, click **Launch instance** (orange button).
2. Fill in the settings:

   | Setting | Value |
   |---------|-------|
   | Name | `ai-finance-assistant` |
   | AMI | **Amazon Linux 2023 AMI** (free tier eligible) |
   | Instance type | **t2.micro** (free tier — 1 vCPU, 1 GB RAM) |
   | Key pair | `ai-finance-key` |

3. Under **Network settings** → **Create security group**:
   - Keep the default SSH rule (port 22, source `0.0.0.0/0`)
   - Click **Add security group rule**:
     - Type: Custom TCP, Port: `8000`, Source: `0.0.0.0/0` (FastAPI)
   - Click **Add security group rule** again:
     - Type: Custom TCP, Port: `8501`, Source: `0.0.0.0/0` (Streamlit)

   > **What is a Security Group?** Think of it as a virtual firewall for your EC2 instance. It controls which traffic is allowed in (inbound) and out (outbound). By default it blocks everything inbound — you explicitly open ports you need.

4. Under **Configure storage**: keep the default 8 GiB (enough for Docker images).
5. Click **Launch instance**.

### Step 5.3 — Get the Public IP

1. Go to **EC2 → Instances**.
2. Wait until the instance state shows **Running** and the status checks pass (2–3 minutes).
3. Click the instance → copy the **Public IPv4 address** (e.g. `54.123.45.67`).

> **Tip:** Every time the instance restarts, the public IP changes. For a permanent URL you can allocate an **Elastic IP** (still free while the instance is running): EC2 → Elastic IPs → Allocate → Associate with your instance.

---

## Phase 6: Deploy on EC2

### Step 6.1 — SSH into the instance

```bash
ssh -i ~/.ssh/ai-finance-key.pem ec2-user@<YOUR_EC2_PUBLIC_IP>
```

> The default username for Amazon Linux is `ec2-user`.

### Step 6.2 — Install Docker

> **Why install Docker on EC2?** EC2 is a bare virtual machine — nothing is pre-installed. You need Docker to run your containers.

```bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker          # start Docker automatically on reboot
sudo usermod -aG docker ec2-user      # allow ec2-user to run docker without sudo
```

**Log out and log back in** for the group change to take effect:
```bash
exit
ssh -i ~/.ssh/ai-finance-key.pem ec2-user@<YOUR_EC2_PUBLIC_IP>
```

Verify:
```bash
docker ps    # should show empty table, no "permission denied"
```

### Step 6.3 — Install Docker Compose

```bash
sudo curl -SL \
  "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version    # should print v2.24.6
```

### Step 6.4 — Clone your repository

```bash
git clone https://github.com/<your-username>/ai-finance-assistant.git
cd ai-finance-assistant
```

### Step 6.5 — Set your OpenAI API key

> **Why not commit it?** API keys in git are a serious security risk. GitHub scans for leaked keys and OpenAI may revoke them automatically. We create the `.env` file directly on the server — it never touches git.

```bash
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

### Step 6.6 — Build and start the containers

```bash
docker-compose up -d --build
```

- `--build`: builds the image from scratch on this machine
- `-d`: detached mode (runs in background so your SSH session can close)

This takes ~5 minutes the first time (downloading Python, installing packages).

### Step 6.7 — Verify the containers are running

```bash
docker-compose ps          # both services should show "running"
docker-compose logs api    # check FastAPI logs
docker-compose logs ui     # check Streamlit logs
```

---

## Phase 7: Access Your Live App

Replace `<YOUR_EC2_PUBLIC_IP>` with your actual IP:

| URL | What you get |
|-----|-------------|
| `http://<YOUR_EC2_PUBLIC_IP>:8000/docs` | FastAPI Swagger UI — try all endpoints interactively |
| `http://<YOUR_EC2_PUBLIC_IP>:8000/api/market/AAPL` | Direct API call (returns JSON) |
| `http://<YOUR_EC2_PUBLIC_IP>:8501` | Streamlit chat UI |

Share the Swagger URL in your resume/portfolio — it lets interviewers test the API without any setup.

---

## Phase 8: Keep It Running After Closing SSH

The `-d` flag in `docker-compose up -d` already runs containers in the background. They will keep running after you close your terminal. They also restart automatically if they crash (`restart: unless-stopped` in docker-compose.yml).

To stop everything:
```bash
docker-compose down
```

To view live logs:
```bash
docker-compose logs -f    # Ctrl+C to exit
```

To redeploy after a code change:
```bash
git pull
docker-compose up -d --build
```

---

## Useful Commands Cheat Sheet

```bash
# SSH in
ssh -i ~/.ssh/ai-finance-key.pem ec2-user@<IP>

# Restart services
docker-compose restart

# See resource usage
docker stats

# Rebuild just one service
docker-compose up -d --build api

# Check disk space (Docker images can fill disk)
df -h
docker system prune -f    # remove unused images/containers
```

---

## Interview Preparation

### Why FastAPI over Flask or Django?

- **Auto-generated Swagger UI** (`/docs`) — zero extra work for interactive API documentation; interviewers and users can try the API immediately
- **Pydantic validation** — request and response bodies are validated and typed automatically; you get clear error messages for free
- **Python type hints everywhere** — matches modern Python style, integrates with IDEs
- **Performance** — comparable to Node.js/Go for I/O-bound workloads (async under the hood)

### Why Docker?

- **Reproducibility** — the same container image runs identically on your Mac and on EC2; eliminates dependency conflicts
- **Isolation** — Python version, packages, and system libraries are locked inside the image
- **Portability** — if you want to move from EC2 to ECS or any other service, you just bring the same image

### Why EC2 over AWS Lambda (serverless)?

| | EC2 | Lambda |
|---|---|---|
| **Always on** | Yes | No (cold starts) |
| **Good for Streamlit** | Yes | No (requires persistent server) |
| **Cost** | Fixed hourly rate | Pay per invocation |
| **Control** | Full OS access | Runtime constraints |

For this app: Lambda would not work well because Streamlit requires a persistent HTTP server, and loading FAISS + model weights on every cold start would be very slow.

### What is an EC2 Security Group?

A security group is a **stateful virtual firewall** attached to an EC2 instance. Key points for interviews:
- **Stateful**: if you allow inbound traffic on port 8000, the response traffic is automatically allowed out
- **Default deny**: all inbound is blocked by default; you explicitly open ports
- You can reference other security groups as sources (useful for allowing traffic only from a load balancer)

### What is a Key Pair?

Asymmetric SSH authentication. AWS keeps the **public key** on the instance (`~/.ssh/authorized_keys`). You hold the **private key** (`.pem`). No password needed — possession of the private key proves identity.

### Multi-Agent Architecture talking points

**LangGraph** is used for orchestration:
- Represents the workflow as a directed graph where nodes are agents and edges are routing decisions
- Separates routing logic from agent logic — the router node classifies intent; agent nodes handle execution
- Stateful: each invocation carries a `GraphState` object through the graph

**RAG (Retrieval-Augmented Generation)**:
- Problem: LLMs have stale knowledge and hallucinate facts
- Solution: retrieve relevant chunks from your own documents at query time and inject them as context
- Pipeline: chunk documents → embed with `text-embedding-3-small` → store in FAISS → at query time, embed query, find top-5 similar chunks, pass as context to GPT-4o-mini

**Routing strategy** (3 layers):
1. UI tab forces a route directly (most specific)
2. Keyword classifier (`classify_route()`) matches patterns
3. Default fallback to `finance_qa`

### What would you do differently in production?

This is a great question to show maturity. Expected answer:

- **HTTPS**: Add Nginx as a reverse proxy with Let's Encrypt SSL certificates. Right now traffic is unencrypted HTTP.
- **Secrets management**: Use AWS Secrets Manager instead of a `.env` file. Never store secrets on the instance filesystem.
- **Container orchestration**: Move from EC2 + docker-compose to **ECS Fargate** (managed, auto-scales, no server patching).
- **CI/CD**: GitHub Actions pipeline that builds and pushes a Docker image to ECR, then triggers a new ECS deployment on every push to `main`.
- **Monitoring**: CloudWatch for logs, metrics, and alarms (e.g., alert if error rate > 5%).
- **Load balancing**: Application Load Balancer in front of EC2 for zero-downtime deployments and health checks.
- **Persistent storage**: If conversation history is added, use DynamoDB (serverless) or RDS PostgreSQL.
- **Multi-AZ**: Deploy across two Availability Zones for high availability.
