# FMNA Platform - Simple Deployment Guide

## 🌐 Deploy for Remote Access - Users from Anywhere

This guide provides **3 simple deployment options** to make your FMNA platform accessible to users anywhere in the world.

---

## Option 1: Docker Deployment (RECOMMENDED - Easiest)

### ✅ Advantages
- One-command deployment
- Works on any machine with Docker
- Includes Redis for caching
- Easy to update and restart
- Can deploy to any cloud VM

### 📋 Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)

### 🚀 Quick Start

**1. Create environment file:**
```powershell
# Copy the example file
copy .env.example .env

# Edit .env and add your API keys
# notepad .env
```

**Required in .env file:**
```env
FMP_API_KEY=your_fmp_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
LLM_MODEL=deepseek-reasoner
LLM_MAX_TOKENS=32000
```

**2. Build and start the application:**
```powershell
# Build and start in one command
docker-compose up -d

# View logs
docker-compose logs -f
```

**3. Access the application:**
- Open browser: http://localhost:8501
- Login with admin credentials (see USER_MANAGEMENT_GUIDE.md)

**4. Stop the application:**
```powershell
docker-compose down
```

**5. Update the application:**
```powershell
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose up -d --build
```

### 🌍 Make It Accessible from Internet

To allow users from anywhere to access your Docker deployment:

**Option A: Deploy to Cloud VM (AWS, Azure, GCP)**

1. **Create a VM instance:**
   - AWS EC2: t3.medium or larger (2 vCPU, 4GB RAM minimum)
   - Azure VM: Standard_B2s or larger
   - GCP Compute Engine: e2-medium or larger
   
2. **Install Docker on the VM:**
   ```bash
   # Ubuntu/Debian example
   sudo apt-get update
   sudo apt-get install docker.io docker-compose -y
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Copy your code to the VM:**
   ```bash
   # Clone from git (recommended)
   git clone <your-repo-url>
   cd fmna
   
   # Or use SCP
   scp -r /path/to/fmna username@vm-ip:/home/username/
   ```

4. **Set up environment variables:**
   ```bash
   cd fmna
   nano .env
   # Add your API keys
   ```

5. **Start the application:**
   ```bash
   sudo docker-compose up -d
   ```

6. **Configure firewall to allow port 8501:**
   ```bash
   # AWS: Add inbound rule for port 8501 in Security Group
   # Azure: Add inbound rule in Network Security Group
   # GCP: Add firewall rule for port 8501
   ```

7. **Access from anywhere:**
   - URL: `http://YOUR-VM-PUBLIC-IP:8501`
   - Users can access via this URL from any location

**Option B: Use ngrok for Quick Testing**

```powershell
# Install ngrok: https://ngrok.com/download

# Start your Docker container first
docker-compose up -d

# Expose it to the internet (temporary)
ngrok http 8501
```
- ngrok will provide a public URL (e.g., https://abc123.ngrok.io)
- Share this URL with users
- ⚠️ Free tier has limitations, use for testing only

---

## Option 2: Streamlit Cloud Deployment (FREE)

### ✅ Advantages
- Completely free for public apps
- No server management needed
- Automatic HTTPS
- Global CDN
- Auto-deploys from Git

### 📋 Prerequisites
- GitHub account
- Streamlit Cloud account (free at https://streamlit.io/cloud)

### 🚀 Deployment Steps

**1. Push your code to GitHub:**
```powershell
# Initialize git if not already done
git init
git add .
git commit -m "Initial FMNA platform commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR-USERNAME/fmna-platform.git
git push -u origin main
```

**2. Create `.streamlit/config.toml` file:**
```powershell
mkdir .streamlit
```

Create `.streamlit/config.toml`:
```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
serverAddress = "0.0.0.0"
gatherUsageStats = false
```

**3. Create `packages.txt` (system dependencies):**
```
build-essential
```

**4. Deploy to Streamlit Cloud:**

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub repository
4. Select:
   - Repository: your-username/fmna-platform
   - Branch: main
   - Main file: frontend_app.py
5. Click "Advanced settings" and add secrets:
   ```
   FMP_API_KEY = "your_key_here"
   DEEPSEEK_API_KEY = "your_key_here"
   LLM_MODEL = "deepseek-reasoner"
   LLM_MAX_TOKENS = "32000"
   ```
6. Click "Deploy"

**5. Access your app:**
- Streamlit Cloud will provide a URL like: https://your-app.streamlit.app
- Share this URL with users worldwide
- They can access from anywhere with authentication

### ⚠️ Limitations
- Free tier has resource limits (1GB RAM)
- App sleeps after inactivity (wakes on access)
- Public apps are visible to everyone (use authentication)
- For production use, consider Streamlit Cloud Teams ($250/month)

---

## Option 3: Cloud Platform Deployment

### AWS Elastic Beanstalk

**Quick Deploy:**
```bash
# Install AWS CLI and EB CLI
pip install awsebcli

# Initialize EB application
eb init -p docker fmna-platform

# Create environment and deploy
eb create fmna-prod --instance-type t3.medium

# Set environment variables
eb setenv FMP_API_KEY=your_key DEEPSEEK_API_KEY=your_key

# Open application
eb open
```

### Google Cloud Run

**Quick Deploy:**
```bash
# Install gcloud CLI
# Set up project
gcloud config set project YOUR-PROJECT-ID

# Build and deploy
gcloud run deploy fmna-platform \
  --source . \
  --port 8501 \
  --allow-unauthenticated \
  --region us-central1 \
  --memory 2Gi

# Set environment variables
gcloud run services update fmna-platform \
  --set-env-vars FMP_API_KEY=your_key,DEEPSEEK_API_KEY=your_key
```

### Azure Container Apps

**Quick Deploy:**
```bash
# Install Azure CLI
az login

# Create resource group
az group create --name fmna-rg --location eastus

# Deploy container
az containerapp up \
  --name fmna-platform \
  --resource-group fmna-rg \
  --location eastus \
  --source . \
  --target-port 8501 \
  --ingress external \
  --env-vars FMP_API_KEY=your_key DEEPSEEK_API_KEY=your_key
```

---

## 🔐 Security Configuration

### 1. Environment Variables

**Never commit API keys to Git!** Always use environment variables.

**Create `.env` file:**
```env
# API Keys
FMP_API_KEY=your_fmp_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# LLM Configuration
LLM_MODEL=deepseek-reasoner
LLM_MAX_TOKENS=32000

# Redis (if using external Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=fmna_user
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=fmna

# Security
SECRET_KEY=generate_a_random_32_char_key_here
JWT_SECRET=another_random_key_for_jwt_tokens
```

### 2. Firewall Rules

**For cloud VMs, only open necessary ports:**
- Port 8501: Streamlit web interface (HTTPS recommended)
- Port 6379: Redis (only if external access needed)

**Do NOT expose:**
- Database ports (5432 for PostgreSQL)
- Internal service ports

### 3. HTTPS/SSL Setup

**Option A: Using Nginx Reverse Proxy**

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option B: Using Cloudflare Tunnel (Free)**
```bash
# Install cloudflared
# Create tunnel
cloudflared tunnel create fmna-platform

# Configure tunnel
cloudflared tunnel route dns fmna-platform your-subdomain.yourdomain.com

# Run tunnel
cloudflared tunnel run fmna-platform --url http://localhost:8501
```

---

## 📊 Deployment Comparison

| Feature | Docker (Local) | Docker (Cloud VM) | Streamlit Cloud | Cloud Platform |
|---------|---------------|-------------------|-----------------|----------------|
| **Cost** | Free | $5-50/month | Free (limited) | $20-100/month |
| **Setup Time** | 5 minutes | 15 minutes | 10 minutes | 20 minutes |
| **Scalability** | Limited | Medium | Low | High |
| **Control** | Full | Full | Limited | Full |
| **Maintenance** | Manual | Manual | Automatic | Manual |
| **HTTPS** | Manual | Manual | Automatic | Manual |
| **Best For** | Development | Small teams | Testing/Demo | Production |

---

## 🎯 Recommended Deployment Path

### For Small Teams (2-5 users)
**Use Docker on Cloud VM**
- Cost: ~$10-20/month
- Full control
- Easy to manage
- Good performance

**Steps:**
1. Create small VM (AWS t3.small, 2GB RAM)
2. Install Docker
3. Deploy with docker-compose
4. Add HTTPS with Let's Encrypt/Nginx
5. Share public IP or domain with users

### For Larger Teams (5-20 users)
**Use Cloud Platform with Load Balancing**
- Cost: ~$50-100/month
- Auto-scaling
- High availability
- Professional setup

**Recommended:**
- AWS: Elastic Beanstalk + RDS
- Azure: Container Apps + Azure Database
- GCP: Cloud Run + Cloud SQL

### For Demo/Testing
**Use Streamlit Cloud (Free)**
- Cost: $0
- Quick setup
- Good for initial testing
- Automatic updates from Git

---

## 🔧 Common Issues & Solutions

### Issue: Application won't start
```bash
# Check logs
docker-compose logs fmna-app

# Common causes:
# 1. Missing API keys in .env
# 2. Port 8501 already in use
# 3. Insufficient memory
```

### Issue: Users can't connect
```bash
# Check if app is running
docker ps

# Check if port is open
netstat -an | findstr 8501

# Check firewall rules on cloud VM
sudo ufw status
```

### Issue: Slow performance
```bash
# Increase VM size
# Or add more memory to Docker container in docker-compose.yml:

services:
  fmna-app:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

---

## 📱 Mobile Access

The Streamlit app is mobile-responsive. Users can access from:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Android Chrome)
- Tablet browsers

---

## 🎬 Quick Start - 3 Commands

**Fastest deployment (Docker):**
```powershell
# 1. Create .env with your API keys
echo FMP_API_KEY=your_key >> .env
echo DEEPSEEK_API_KEY=your_key >> .env

# 2. Start the platform
docker-compose up -d

# 3. Access at http://localhost:8501
```

**For cloud deployment, add:**
```bash
# Open firewall port
sudo ufw allow 8501/tcp

# Access at http://YOUR-VM-IP:8501
```

---

## 💰 Cost Estimates

### Monthly Costs (Estimated)

**Self-Hosted on Cloud VM:**
- **Small (2-5 users):** $10-20/month
  - AWS t3.small: $15/month
  - Azure B2s: $30/month
  - GCP e2-small: $13/month
  
- **Medium (5-20 users):** $50-100/month
  - AWS t3.medium: $30/month
  - Load balancer: $20/month
  - Managed database: $15-30/month
  
- **Large (20+ users):** $200-500/month
  - Multiple instances
  - Auto-scaling
  - Managed services
  - Backup/disaster recovery

**Streamlit Cloud:**
- Free tier: $0 (limited resources, public)
- Teams: $250/month (more resources, private)
- Enterprise: Custom pricing

**Platform-as-a-Service:**
- AWS Elastic Beanstalk: $50-150/month
- Google Cloud Run: Pay per use (~$20-80/month)
- Azure Container Apps: $30-100/month

---

## 🛡️ Production Checklist

Before deploying to production:

- [ ] Change admin default password
- [ ] Set up HTTPS/SSL (Let's Encrypt recommended)
- [ ] Configure firewall rules
- [ ] Set up automated backups for `data/` directory
- [ ] Configure log rotation
- [ ] Set up monitoring (uptime, performance)
- [ ] Test authentication with multiple users
- [ ] Document your deployment for your team
- [ ] Set up domain name (optional but recommended)
- [ ] Configure CORS if using API separately
- [ ] Test from different networks/locations

---

## 📖 Detailed Deployment Walkthroughs

### Walkthrough 1: AWS EC2 Deployment (Step-by-Step)

**1. Create EC2 Instance:**
```
- AMI: Ubuntu Server 22.04 LTS
- Instance type: t3.small (2 vCPU, 2GB RAM) - $15/month
- Storage: 20GB gp3
- Security Group: Allow SSH (22), HTTP (80), HTTPS (443), Custom TCP (8501)
```

**2. Connect to instance:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

**3. Install Docker:**
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
```

**4. Deploy application:**
```bash
# Clone repository
git clone <your-repo> fmna
cd fmna

# Create .env file
nano .env
# Add your API keys

# Start application
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

**5. Set up domain (optional):**
```bash
# Install Nginx
sudo apt-get install nginx certbot python3-certbot-nginx -y

# Configure Nginx (create /etc/nginx/sites-available/fmna)
sudo nano /etc/nginx/sites-available/fmna
```

Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fmna /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Access at https://your-domain.com
```

**6. Set up automatic updates (optional):**
```bash
# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/fmna
git pull
docker-compose down
docker-compose up -d --build
EOF

chmod +x update.sh

# Run manually or schedule with cron
```

### Walkthrough 2: Streamlit Cloud Deployment (Step-by-Step)

**1. Prepare repository:**
```powershell
# Commit all changes
git add .
git commit -m "Prepare for Streamlit Cloud"
git push origin main
```

**2. Create Streamlit Cloud account:**
- Go to https://share.streamlit.io/
- Sign up with GitHub
- Connect your repository

**3. Deploy app:**
- Click "New app"
- Select repository: your-username/fmna-platform
- Branch: main
- Main file: frontend_app.py
- Click "Advanced settings"

**4. Add secrets (IMPORTANT):**
```toml
# In Streamlit Cloud secrets section, add:
FMP_API_KEY = "your_fmp_key_here"
DEEPSEEK_API_KEY = "your_deepseek_key_here"
LLM_MODEL = "deepseek-reasoner"
LLM_MAX_TOKENS = "32000"
```

**5. Deploy:**
- Click "Deploy"
- Wait 2-5 minutes
- App will be live at https://your-app.streamlit.app

**6. Update the app:**
- Just push to GitHub
- Streamlit Cloud auto-deploys from main branch
- Or click "Reboot app" in Streamlit Cloud dashboard

---

## 🌟 Best Practices

### For Development/Testing
```
Use: Local Docker or Streamlit Cloud free tier
Cost: $0-5/month
Access: You and 1-2 collaborators
```

### For Small Business (2-10 users)
```
Use: Docker on small cloud VM + domain
Cost: $20-40/month
Components:
  - Cloud VM (t3.small): $15/month
  - Domain name: $12/year
  - SSL: Free (Let's Encrypt)
Access: Team members worldwide via https://your-domain.com
```

### For Enterprise (10+ users)
```
Use: Managed cloud platform + database
Cost: $200-500/month
Components:
  - Container service (auto-scaling)
  - Managed database (PostgreSQL)
  - Load balancer
  - CDN
  - Monitoring
Access: All employees + clients via branded domain
```

---

## 🆘 Support & Troubleshooting

### Check Application Health
```bash
# Docker deployment
docker-compose ps
docker-compose logs --tail=50

# Test endpoint
curl http://localhost:8501/_stcore/health
```

### Restart Services
```bash
# Restart everything
docker-compose restart

# Restart just the app
docker-compose restart fmna-app

# Full rebuild
docker-compose down
docker-compose up -d --build
```

### Backup User Data
```bash
# Backup user database
cp data/users.db data/users_backup_$(date +%Y%m%d).db

# Backup DuckDB
cp data/fmna.duckdb data/fmna_backup_$(date +%Y%m%d).duckdb

# Automated daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup_script.sh
```

---

## 📞 Getting Help

**Issues with deployment?**
- Check logs: `docker-compose logs`
- Verify environment variables: `docker-compose config`
- Test locally first before cloud deployment

**Need modifications?**
- Edit `frontend_app.py` for UI changes
- Edit `docker-compose.yml` for configuration
- Rebuild after changes: `docker-compose up -d --build`

---

## ✅ Summary - Choose Your Path

**🚀 Quickest (5 minutes):**
Local Docker deployment → Great for testing

**💰 Free (10 minutes):**
Streamlit Cloud → Perfect for demos and small teams

**🏢 Professional (30 minutes):**
Docker on Cloud VM with domain → Best for business use

**🌐 Enterprise (1-2 hours):**
Managed cloud platform → Scalable for large organizations

---

**Last Updated:** November 7, 2025  
**Status:** ✅ Ready for Production Deployment
