# Deployment Guide 🚀

Production deployment options for ScholarEval.

## Local Development

```bash
python main.py
```

Server runs on `http://localhost:8000` with hot reload.

## Docker Deployment

### Build Image

```bash
docker build -t scholareval:latest .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e MISTRAL_API_KEY=sk-xxx \
  -v scholareval_data:/app/data \
  --name scholareval \
  scholareval:latest
```

### Docker Compose

```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f scholareval
```

Stop:
```bash
docker-compose down
```

## Cloud Deployment

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/scholareval
gcloud run deploy scholareval \
  --image gcr.io/YOUR_PROJECT/scholareval \
  --platform managed \
  --region us-central1 \
  --set-env-vars MISTRAL_API_KEY=sk-xxx
```

### AWS ECS

1. Push to ECR:
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ECR_URL
docker tag scholareval:latest $AWS_ECR_URL/scholareval:latest
docker push $AWS_ECR_URL/scholareval:latest
```

2. Create task definition and service in ECS console

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name scholareval \
  --image scholareval:latest \
  --environment-variables MISTRAL_API_KEY=sk-xxx \
  --ports 8000 \
  --cpu 1 --memory 1
```

## Self-Hosted (VPS)

### Using systemd

Create `/etc/systemd/system/scholareval.service`:

```ini
[Unit]
Description=ScholarEval Service
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/scholareval
Environment="MISTRAL_API_KEY=sk-xxx"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable scholareval
sudo systemctl start scholareval
sudo systemctl status scholareval
```

View logs:
```bash
sudo journalctl -u scholareval -f
```

### Using Gunicorn (Production WSGI)

```bash
pip install gunicorn uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

## Reverse Proxy Setup

### Nginx + SSL

```nginx
upstream scholareval {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name scholareval.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scholareval.example.com;

    ssl_certificate /etc/letsencrypt/live/scholareval.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scholareval.example.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://scholareval;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Cache static files
    location ~* \.(js|css|html)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

Certbot SSL:
```bash
sudo certbot certonly --nginx -d scholareval.example.com
```

### Caddy (Simple Alternative)

```caddyfile
scholareval.example.com {
    reverse_proxy localhost:8000
}
```

## Performance Tuning

### Environment Variables

```env
# Parallel workers (gunicorn)
# Use: CPU_COUNT * 2 + 1
WORKER_COUNT=9

# Cache embeddings
CACHE_EMBEDDINGS=true

# Increase chunk size for faster RAG
CHUNK_SIZE=500

# Reduce context size
TOP_K=3
```

### Database Optimization

For production, persist RAG index:

```python
# In rag_engine.py
import pickle

def save_index(self, path):
    with open(path, 'wb') as f:
        pickle.dump({
            'texts': self.texts,
            'embeddings': self.embeddings,
            'bm25': self.bm25
        }, f)

def load_index(self, path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
        self.texts = data['texts']
        self.embeddings = data['embeddings']
        self.bm25 = data['bm25']
        # Rebuild FAISS index
        self.build_index(self.texts)
```

## Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Check status
curl http://localhost:8000/status
```

### Logging to File

```env
LOG_FILE=/var/log/scholareval/app.log
LOG_LEVEL=INFO
```

### Application Performance Monitoring (APM)

Add to `main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Security Checklist

- [ ] Use environment variables for secrets
- [ ] Set `DEBUG=False` in production
- [ ] Enable HTTPS with valid SSL cert
- [ ] Restrict CORS origins (update from "*")
- [ ] Implement rate limiting
- [ ] Validate all file uploads
- [ ] Use strong API keys
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Monitor error logs
- [ ] Setup backup strategy

## Backup & Recovery

### Backup Uploaded PDFs

```bash
# Backup data directory
tar -czf scholareval_backup_$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf scholareval_backup_20240115.tar.gz
```

### Database Backup (if using persistence)

```bash
# Regular backup
0 2 * * * tar -czf /backups/scholareval_$(date +\%Y\%m\%d).tar.gz /app/data/
```

## Scaling

### Horizontal Scaling (Multiple Instances)

1. Run multiple instances behind load balancer
2. Use shared storage for RAG indices
3. Configure sticky sessions (optional)

```nginx
# Load balancer config
upstream scholareval_backend {
    least_conn;
    server instance1.local:8000;
    server instance2.local:8000;
    server instance3.local:8000;
}
```

### Database Clustering

Consider Redis for caching embedding results:

```python
import redis
cache = redis.Redis(host='redis.local', port=6379)
```

## Troubleshooting

### High Memory Usage
- Reduce `CHUNK_SIZE`
- Lower `TOP_K`
- Use FAISS with fewer shards

### Slow Responses
- Check network to Mistral API
- Verify PDF size
- Monitor CPU/memory

### SSL Certificate Issues
```bash
# Renew cert
sudo certbot renew
```

## Support

Issues? Check logs:

```bash
# Docker
docker logs scholareval

# Systemd
journalctl -u scholareval -n 100

# Direct
# Check terminal output running `python main.py`
```

---

**Deployed successfully? Add your deployment to the docs!**
