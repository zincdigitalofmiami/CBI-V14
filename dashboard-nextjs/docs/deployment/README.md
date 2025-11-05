# Dashboard Deployment Documentation

Vercel deployment, CI/CD, environment configuration.

## Structure

- **active/** - Current deployment configs (2 files)
  - DEPLOYMENT.md
  - VERCEL_SETUP.md
- **old/** - Historical deployment docs
- **new/** - Pending deployment changes

## Current Deployment

**Platform:** Vercel  
**URL:** https://cbi-dashboard.vercel.app  
**Framework:** Next.js 14

## Active Documentation

### DEPLOYMENT.md
Main deployment guide, process, troubleshooting

### VERCEL_SETUP.md
Vercel configuration, environment variables, domains

## Deployment Topics

### Environment Variables
- Development
- Staging
- Production

### Build Configuration
- next.config.js
- Build commands
- Output settings

### CI/CD Pipeline
- GitHub integration
- Auto-deploy branches
- Preview deployments

### Domain Configuration
- Custom domains
- SSL certificates
- DNS settings

### Performance
- Edge functions
- Caching strategy
- CDN configuration

### Monitoring
- Vercel Analytics
- Error tracking
- Performance monitoring

## Deployment Checklist

```markdown
# Deployment Checklist

Pre-Deployment:
- [ ] Tests passing
- [ ] No linter errors
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] API endpoints tested

Deployment:
- [ ] Deploy to preview
- [ ] Test preview deployment
- [ ] Deploy to production
- [ ] Verify production

Post-Deployment:
- [ ] Monitor errors
- [ ] Check performance
- [ ] Verify all pages load
- [ ] Test critical paths
```

## Rollback Procedure

1. Go to Vercel dashboard
2. Select previous deployment
3. Click "Promote to Production"
4. Verify rollback successful

