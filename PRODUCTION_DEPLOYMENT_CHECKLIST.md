# Production Deployment Checklist - Financial Management Service

## Pre-Deployment Verification

### 1. Environment Variables Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `DATABASE_URL` with production PostgreSQL credentials
- [ ] Generate secure `JWT_SECRET_KEY` (use: `openssl rand -hex 32`)
- [ ] Configure `BILLING_SERVICE_URL` (production endpoint)
- [ ] Set `BILLING_SERVICE_API_KEY` or `BILLING_SERVICE_TOKEN`
- [ ] Set Clerk authentication keys:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  - `CLERK_SECRET_KEY`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set appropriate `LOG_LEVEL` (recommended: `WARNING` or `ERROR`)

### 2. Database Setup
- [ ] Create PostgreSQL database (version 15+)
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify all tables created successfully
- [ ] Test database connection from application server
- [ ] Configure database connection pooling settings

### 3. Billing Service Integration
- [ ] Verify Billing Service is deployed and accessible
- [ ] Test endpoint connectivity: `GET /tenants/{tenant_id}/feature-access`
- [ ] Validate API key/authentication works
- [ ] Confirm retry logic is functioning (test with network blips)
- [ ] Verify no hardcoded pricing values in code

### 4. Backend Services Verification
- [ ] All services use database queries (no mock data)
- [ ] GL financial metrics queries tested
- [ ] Operational metrics (AR/AP) queries tested
- [ ] Logging configured and writing to files/stdout
- [ ] Retry logic active for all external API calls
- [ ] Error handling in place with proper logging

### 5. Frontend Configuration
- [ ] Update API base URL to production endpoint
- [ ] Remove any development/mock configurations
- [ ] Verify React Query cache settings appropriate for production
- [ ] Test loading states during API calls
- [ ] Test error states when API fails
- [ ] Verify auto-refresh working (30s interval for stats)

### 6. Security Checks
- [ ] No hardcoded credentials in code
- [ ] All sensitive data in environment variables only
- [ ] CORS configured for production domains only
- [ ] Authentication middleware active
- [ ] Rate limiting enabled (if applicable)
- [ ] HTTPS enforced in production

### 7. Monitoring & Logging
- [ ] Application logs captured (stdout/file)
- [ ] Error logging active with appropriate detail
- [ ] Performance metrics tracked (response times, query times)
- [ ] Health check endpoint accessible: `/health`
- [ ] Alerting configured for critical errors
- [ ] Log aggregation system integrated (e.g., ELK, CloudWatch)

### 8. Performance Optimization
- [ ] Database indexes created on frequently queried columns
- [ ] Connection pooling configured
- [ ] API response caching where appropriate
- [ ] Static assets served via CDN (frontend)
- [ ] Compression enabled (gzip/brotli)
- [ ] Load testing completed

### 9. Backup & Recovery
- [ ] Database backup strategy implemented
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] Rollback procedure defined and tested

### 10. Documentation
- [ ] API documentation updated
- [ ] Deployment runbook created
- [ ] Troubleshooting guide available
- [ ] Contact information for on-call support

## Deployment Steps

### Step 1: Deploy Backend
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start application (choose one):
# Option A: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Option B: Using Docker
docker-compose up -d

# Option C: Using gunicorn (recommended for production)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 2: Deploy Frontend
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
pnpm install

# 3. Build production bundle
pnpm build

# 4. Start production server
pnpm start
# OR deploy to hosting platform (Vercel, AWS, etc.)
```

### Step 3: Verify Deployment
```bash
# 1. Health check
curl http://your-domain.com/health

# 2. Test dashboard stats endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://your-domain.com/api/v1/fm/dashboard/stats?legal_entity_id=YOUR_ENTITY_ID"

# 3. Test pricing endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://your-domain.com/api/v1/fm/pricing/tenants/YOUR_TENANT_ID/feature-access"

# 4. Check logs for errors
tail -f logs/*.log
```

### Step 4: Monitor Post-Deployment
- [ ] Watch error logs for first 24 hours
- [ ] Monitor API response times
- [ ] Track database query performance
- [ ] Verify billing service integration working
- [ ] Check frontend is loading real data (not mock)
- [ ] Monitor retry attempts (should be minimal)

## Rollback Procedure

If deployment fails:

1. **Immediate rollback:**
   ```bash
   git revert HEAD
   alembic downgrade -1
   # Redeploy previous version
   ```

2. **Database rollback:**
   ```bash
   # Restore from backup if needed
   psql -U fm_user fm_database < backup_YYYYMMDD.sql
   ```

3. **Frontend rollback:**
   ```bash
   cd frontend
   git revert HEAD
   pnpm build
   pnpm start
   ```

## Post-Deployment Validation Checklist

- [ ] Dashboard statistics showing real database data
- [ ] Pricing data flowing from Billing Service (no hardcoded values)
- [ ] Company stats widget fetching from API (not mock data)
- [ ] All API endpoints responding within acceptable timeframes
- [ ] No unhandled exceptions in logs
- [ ] Retry logic functioning correctly
- [ ] Logging capturing all required events
- [ ] Frontend displaying correct financial metrics
- [ ] Authentication working correctly
- [ ] All enterprise features operational (toasts, breadcrumbs, sidebar)

## Support Contacts

- **Technical Lead:** [Name] - [Email/Phone]
- **DevOps:** [Name] - [Email/Phone]
- **On-Call Engineer:** [Rotation Schedule]
- **Billing Service Team:** [Contact Information]

## Version Information

- **Deployment Date:** YYYY-MM-DD
- **Version:** 1.0.0
- **Git Commit:** [commit hash]
- **Deployed By:** [name]

---

**IMPORTANT:** This checklist must be completed in full before marking deployment as complete. Any skipped items must be documented with justification and approved by technical lead.
