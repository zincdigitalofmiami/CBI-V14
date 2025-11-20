# Gemini API Rate Limits - CBI-V14

**Date:** January 2025  
**Project:** CBI-V14  
**Tier:** Paid Tier 1

---

## 📊 CURRENT USAGE (28 Days)

### Model: `gemini-3-pro`

| Metric | Usage | Limit | Percentage | Status |
|--------|-------|-------|------------|--------|
| **RPM** (Requests/Minute) | 2 | 50 | 4% | ✅ Safe |
| **TPM** (Tokens/Minute) | 847.84K | 1M | 85% | ⚠️ Close to limit |
| **RPD** (Requests/Day) | 3 | 1K | 0.3% | ✅ Safe |

---

## 🎯 ANALYSIS

### ✅ Good News
- **RPM:** Only 4% usage - plenty of headroom for more requests
- **RPD:** Only 0.3% usage - can handle many more requests per day
- **Overall:** You're not hitting request limits

### ⚠️ Warning
- **TPM:** 85% usage - **This is your bottleneck**
- You're using ~848K tokens per minute out of 1M limit
- Close to hitting the token limit if usage spikes

---

## 💡 OPTIMIZATION STRATEGIES

### 1. Reduce Token Usage

**Use smaller models for simple tasks:**
- `gemini-1.5-flash` - Faster, cheaper, lower token usage
- `gemini-1.5-pro` - Good balance
- `gemini-3-pro` - Use only for complex tasks

**Reduce prompt size:**
- Remove unnecessary context
- Use concise prompts
- Summarize long inputs before sending

**Batch requests efficiently:**
- Combine multiple queries when possible
- Cache responses for repeated queries

### 2. Monitor Usage

**Set up alerts:**
- Monitor TPM usage in Google Cloud Console
- Set alerts at 80% and 90% thresholds
- Track usage patterns

**Track by use case:**
- Identify which operations use most tokens
- Optimize high-usage operations first

### 3. Upgrade Options

**If you consistently hit limits:**
- **Tier 2:** Higher limits (check pricing)
- **Enterprise:** Custom limits (contact Google)

**Current Tier 1 Limits:**
- RPM: 50 requests/minute
- TPM: 1M tokens/minute
- RPD: 1K requests/day

---

## 🔧 IMPLEMENTATION TIPS

### Use Appropriate Models

```python
# For simple tasks - use Flash
simple_query = "What is the weather?"
model = "gemini-1.5-flash"  # Faster, lower token usage

# For complex analysis - use Pro
complex_query = "Analyze this 10-page document..."
model = "gemini-3-pro"  # More capable, higher token usage
```

### Optimize Prompts

```python
# ❌ Bad: Too verbose
prompt = f"""
Here is a very long document with lots of context...
{very_long_document}
Now please analyze this in detail and provide comprehensive insights...
"""

# ✅ Good: Concise
prompt = f"""
Analyze key points:
{document_summary}
Focus on: pricing trends, market impact
"""
```

### Cache Responses

```python
# Cache common queries
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(query):
    # Check cache first
    # Only call API if not cached
    pass
```

---

## 📈 MONITORING

### Google Cloud Console
1. Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/metrics
2. Select project: `cbi-v14`
3. View metrics:
   - Requests per minute
   - Tokens per minute
   - Requests per day
   - Error rates

### Set Up Alerts
1. Go to: https://console.cloud.google.com/monitoring/alerting
2. Create alert policy:
   - Metric: `api/request_count` or `api/token_count`
   - Threshold: 80% of limit
   - Notification: Email/Slack

---

## 🚨 WHAT HAPPENS AT LIMIT

### If You Hit TPM Limit (1M tokens/minute)
- **Error:** `429 Resource Exhausted`
- **Response:** Requests will be rate-limited
- **Solution:** 
  - Wait for rate limit window to reset
  - Reduce token usage
  - Upgrade tier

### If You Hit RPM Limit (50 requests/minute)
- **Error:** `429 Resource Exhausted`
- **Response:** Requests will be queued/rejected
- **Solution:**
  - Implement exponential backoff
  - Batch requests
  - Upgrade tier

---

## 📊 CURRENT STATUS

**Your Usage Pattern:**
- Low request volume (2 RPM, 3 RPD)
- High token usage per request (848K TPM / 2 RPM = ~424K tokens per request)
- This suggests: **Long prompts or complex queries**

**Recommendation:**
- ✅ You're safe on RPM and RPD
- ⚠️ Monitor TPM closely - you're at 85%
- 💡 Consider optimizing prompts to reduce token usage
- 💡 Use `gemini-1.5-flash` for simpler tasks

---

## 🔗 RELATED

- Gemini API Documentation: https://ai.google.dev/docs
- Rate Limits: https://ai.google.dev/pricing
- Google Cloud Console: https://console.cloud.google.com

---

**Current Status: ⚠️ TPM at 85% - Monitor closely, optimize token usage**


