# Quick Start Guide - Linux Server Deployment

This guide provides step-by-step instructions for deploying the Telegram bot on a Linux server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Docker Installation](#docker-installation)
4. [Project Setup](#project-setup)
5. [Configuration](#configuration)
6. [Running the Bot](#running-the-bot)
7. [Systemd Service Setup](#systemd-service-setup)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Linux server (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- Root or sudo access
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram channel where bot is admin
- Minimum 1GB RAM, 10GB disk space

---

## Server Preparation

### 1. Update System Packages

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Install Required System Packages

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget nano

# CentOS/RHEL
sudo yum install -y git curl wget nano
```

### 3. Create Application User (Optional but Recommended)

```bash
# Create user for running the bot
sudo useradd -m -s /bin/bash botuser

# Switch to bot user
sudo su - botuser
```

---

## Docker Installation

### Option A: Automated Docker Installation (Recommended)

```bash
# Download and run Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Log out and log back in for group changes to take effect
# Or run: newgrp docker
```

### Option B: Manual Docker Installation (Ubuntu/Debian)

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt update
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Option C: Manual Docker Installation (CentOS/RHEL)

```bash
# Remove old versions
sudo yum remove docker \
    docker-client \
    docker-client-latest \
    docker-common \
    docker-latest \
    docker-latest-logrotate \
    docker-logrotate \
    docker-engine

# Install dependencies
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Test Docker installation
docker run hello-world
```

---

## Project Setup

### 1. Clone the Repository

```bash
# Navigate to home directory or desired location
cd ~

# Clone the repository
git clone https://github.com/YOUR_USERNAME/tg-bot-tracker-and-purge-unactive-audience.git

# Navigate to project directory
cd tg-bot-tracker-and-purge-unactive-audience
```

### 2. Create Logs Directory

```bash
# Create logs directory (if not exists)
mkdir -p logs

# Set appropriate permissions
chmod 755 logs
```

---

## Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit environment file
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file with your values:

```bash
# Telegram Bot Configuration
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
CHANNEL_ID=-1001234567890
CHANNEL_USERNAME=your_channel_name
ADMIN_IDS=123456789,987654321

# Timezone (use your timezone)
TIMEZONE=Europe/Moscow

# Database Configuration (for Docker)
DATABASE_URL=postgresql+asyncpg://tg_bot_user:tg_bot_password@postgres:5432/tg_bot_db

# Redis Configuration (for Docker)
REDIS_URL=redis://redis:6379/0

# Logging
LOG_PATH=logs/bot.log
```

**Important Notes:**
- `BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather) using `/newbot` command
- `CHANNEL_ID`: Forward a channel message to [@userinfobot](https://t.me/userinfobot) to get ID (starts with -100)
- `CHANNEL_USERNAME`: Your channel username without @
- `ADMIN_IDS`: Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
- For Docker deployment, use hostnames `postgres` and `redis` in URLs

### 3. How to Get Required IDs

#### Get Bot Token:
```
1. Open Telegram and find @BotFather
2. Send /newbot command
3. Follow the prompts to create your bot
4. Copy the token provided
```

#### Get Channel ID:
```
1. Forward any message from your channel to @userinfobot
2. Bot will reply with channel information including ID
3. Channel ID starts with -100 (e.g., -1001234567890)
```

#### Get Your User ID (Admin ID):
```
1. Send /start to @userinfobot
2. Bot will reply with your user ID
3. Use this ID in ADMIN_IDS
```

#### Multiple Admins:
```
# Separate multiple admin IDs with commas
ADMIN_IDS=123456789,987654321,555666777
```

### 4. Verify Configuration

```bash
# Check .env file
cat .env

# Ensure all variables are set (no empty values)
```

---

## Running the Bot

### 1. Start with Docker Compose (Recommended)

```bash
# Build and start all services (bot, PostgreSQL, Redis)
docker compose up -d --build

# Verify containers are running
docker compose ps

# Expected output:
# NAME                  STATUS              PORTS
# tg_bot_app           Up X seconds        
# tg_bot_postgres      Up X seconds        5432/tcp
# tg_bot_redis         Up X seconds        6379/tcp
```

### 2. View Logs

```bash
# Follow bot logs in real-time
docker compose logs -f bot

# View last 50 lines
docker compose logs --tail=50 bot

# View all service logs
docker compose logs -f

# Stop following logs: Ctrl+C
```

### 3. Verify Bot is Working

```bash
# Check bot logs for "Bot started successfully"
docker compose logs bot | grep "Bot started successfully"

# Check PostgreSQL connection
docker compose logs bot | grep "Database initialized"

# Check Redis connection
docker compose logs bot | grep "Redis initialized"
```

### 4. Test Bot Functionality

1. Open your bot in Telegram
2. Send `/start` command
3. Bot should respond (admins get admin message, users get subscription check)
4. Admin: Send `/admin` to open admin panel

---

## Systemd Service Setup (Optional)

For automatic start on server boot and better process management:

### 1. Create Systemd Service File

```bash
# Create service file
sudo nano /etc/systemd/system/tg-bot.service
```

### 2. Add Service Configuration

```ini
[Unit]
Description=Telegram Channel Audience Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/botuser/tg-bot-tracker-and-purge-unactive-audience
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=botuser
Group=botuser

[Install]
WantedBy=multi-user.target
```

**Note**: Replace `/home/botuser/tg-bot-tracker-and-purge-unactive-audience` with your actual project path.

### 3. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tg-bot.service

# Start the service
sudo systemctl start tg-bot.service

# Check service status
sudo systemctl status tg-bot.service
```

### 4. Manage Service

```bash
# Start bot
sudo systemctl start tg-bot

# Stop bot
sudo systemctl stop tg-bot

# Restart bot
sudo systemctl restart tg-bot

# View service logs
sudo journalctl -u tg-bot.service -f
```

---

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs (Docker)
docker compose logs -f bot

# View log file directly
tail -f logs/bot.log

# Search logs for errors
docker compose logs bot | grep ERROR

# View last 100 lines
docker compose logs --tail=100 bot
```

### Check Container Status

```bash
# List running containers
docker compose ps

# View resource usage
docker stats

# Detailed container info
docker inspect tg_bot_app
```

### Restart Services

```bash
# Restart only bot
docker compose restart bot

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Start all services
docker compose up -d
```

### Update Bot Code

```bash
# Navigate to project directory
cd ~/tg-bot-tracker-and-purge-unactive-audience

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# View logs to ensure successful start
docker compose logs -f bot
```

### Database Backup

```bash
# Create backup
docker exec tg_bot_postgres pg_dump -U tg_bot_user tg_bot_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Create backup directory
mkdir -p ~/backups

# Backup with proper path
docker exec tg_bot_postgres pg_dump -U tg_bot_user tg_bot_db > ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore

```bash
# Restore from backup
docker exec -i tg_bot_postgres psql -U tg_bot_user tg_bot_db < backup_20240115_143000.sql

# Restore from compressed backup
gunzip -c ~/backups/backup_20240115_143000.sql.gz | docker exec -i tg_bot_postgres psql -U tg_bot_user tg_bot_db
```

### Clean Up Docker Resources

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused resources
docker system prune -a --volumes
```

---

## Troubleshooting

### Bot Not Responding

**Check if containers are running:**
```bash
docker compose ps
```

**Check bot logs:**
```bash
docker compose logs bot
```

**Restart bot:**
```bash
docker compose restart bot
```

### Database Connection Error

**Check PostgreSQL container:**
```bash
docker compose ps postgres
docker compose logs postgres
```

**Test database connection:**
```bash
docker exec -it tg_bot_postgres psql -U tg_bot_user tg_bot_db
```

**Verify DATABASE_URL in .env:**
```bash
# Should be:
DATABASE_URL=postgresql+asyncpg://tg_bot_user:tg_bot_password@postgres:5432/tg_bot_db
```

### Redis Connection Error

**Check Redis container:**
```bash
docker compose ps redis
docker compose logs redis
```

**Test Redis connection:**
```bash
docker exec -it tg_bot_redis redis-cli ping
# Expected output: PONG
```

### Subscription Check Fails

**Verify bot is admin in channel:**
1. Go to your Telegram channel
2. Click channel name → Administrators
3. Ensure your bot is in the list with proper permissions

**Check CHANNEL_ID format:**
```bash
# Should start with -100
CHANNEL_ID=-1001234567890
```

**Test channel access:**
```bash
# Check bot logs for subscription check
docker compose logs bot | grep "Subscription check"
```

### Permission Denied Errors

**Fix file permissions:**
```bash
# Fix logs directory
chmod 755 logs

# Fix all project files
chmod -R 755 ~/tg-bot-tracker-and-purge-unactive-audience

# Fix .env file permissions
chmod 600 .env
```

### Docker Permission Issues

**Add user to docker group:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Verify group membership:**
```bash
groups
```

### Port Already in Use

**Check what's using the port:**
```bash
sudo netstat -tulpn | grep 5432  # PostgreSQL
sudo netstat -tulpn | grep 6379  # Redis
```

**Stop conflicting services:**
```bash
# If PostgreSQL is installed locally
sudo systemctl stop postgresql

# If Redis is installed locally
sudo systemctl stop redis
```

### Out of Disk Space

**Check disk usage:**
```bash
df -h
```

**Clean Docker resources:**
```bash
docker system prune -a --volumes
```

**Remove old logs:**
```bash
# Keep only last 7 days of logs
find logs/ -name "*.log" -mtime +7 -delete
```

### Bot Token Invalid

**Verify token format:**
- Should be: `123456789:ABC-DEFabcdef123456789ABCDEFGHIJK`
- Two parts separated by colon
- Numbers before colon, alphanumeric after

**Get new token:**
1. Open [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot
4. Click "API Token"
5. Copy and update in `.env`

---

## Quick Command Reference

```bash
# Start bot
docker compose up -d

# Stop bot
docker compose down

# View logs
docker compose logs -f bot

# Restart bot
docker compose restart bot

# Rebuild and restart
docker compose up -d --build

# Check status
docker compose ps

# Execute commands in container
docker compose exec bot /bin/bash

# Backup database
docker exec tg_bot_postgres pg_dump -U tg_bot_user tg_bot_db > backup.sql

# View resource usage
docker stats
```

---

## Security Recommendations

1. **Protect .env file:**
   ```bash
   chmod 600 .env
   ```

2. **Use firewall:**
   ```bash
   # Ubuntu/Debian
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp   # if using web interface
   sudo ufw allow 443/tcp  # if using HTTPS
   ```

3. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Use strong database password:**
   - Change default password in `docker-compose.yml`
   - Update `DATABASE_URL` in `.env` accordingly

5. **Regular backups:**
   - Set up automated daily backups
   - Store backups in secure location

---

## Additional Resources

- **Telegram Bot API:** https://core.telegram.org/bots/api
- **Docker Documentation:** https://docs.docker.com/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **Redis Documentation:** https://redis.io/documentation

---

## Support

If you encounter issues:

1. Check logs: `docker compose logs -f bot`
2. Review this guide's troubleshooting section
3. Verify all environment variables are set correctly
4. Ensure bot is admin in your channel
5. Check database and Redis connectivity

---

**For detailed information about bot features and usage, see [README.md](README.md)**
