# Gemini Code Assist - Quotas and Limits

**Date:** November 20, 2025  
**Source:** Google Cloud Documentation  
**Last Updated:** 2025-11-14 UTC

---

## 📋 OVERVIEW

This document lists the quotas and system limits that apply to Gemini Code Assist and Gemini CLI.

**Key Concepts:**
- **Quotas:** Specifies the amount of a countable, shared resource you can use
- **System Limits:** Fixed values that cannot be changed

---

## 🔢 QUOTAS FOR GEMINI CODE ASSIST

### Feature-Specific Quotas

| Quota | Value |
|-------|-------|
| **Local codebase awareness** | 1,000,000 token context window |
| **Code customization repositories** | 20,000 |

---

## ⚡ QUOTAS FOR AGENT MODE AND GEMINI CLI

**Important:** Quotas for requests from Gemini Code Assist agent mode and Gemini CLI are **combined**. When in agent mode or using Gemini CLI, one prompt might result in multiple model requests.

### Requests Per User Per Minute

| License Type | Way(s) to Purchase | Value |
|--------------|-------------------|-------|
| **For individuals (free)** | N/A | 60 requests/minute |
| **Gemini Code Assist via Google AI Pro** | Google AI Pro | 120 requests/minute |
| **Gemini Code Assist via Google AI Ultra** | Google AI Ultra | 120 requests/minute |
| **Standard** | Google Developer Program premium or Google Cloud console | 120 requests/minute |
| **Enterprise via Google Cloud** | Google Cloud console | 120 requests/minute |

### Requests Per User Per Day

| License Type | Way(s) to Purchase | Value |
|--------------|-------------------|-------|
| **For individuals (free)** | N/A | 1,000 requests/day |
| **Gemini Code Assist via Google AI Pro** | Google AI Pro | 1,500 requests/day |
| **Gemini Code Assist via Google AI Ultra** | Google AI Ultra | 2,000 requests/day |
| **Standard** | Google Developer Program premium or Google Cloud console | 1,500 requests/day |
| **Enterprise** | Google Cloud console | 2,000 requests/day |

---

## 🐙 QUOTAS FOR GEMINI CODE ASSIST ON GITHUB

**Important:** Usage of Gemini Code Assist on GitHub is **NOT counted** as part of the general quotas for Gemini Code Assist.

### Consumer Version (GitHub)
- **Quota:** 33 pull request reviews per day

### Enterprise Version (GitHub Preview)
- **Quota:** At least 100 pull request reviews per day
- **Note:** The exact number depends on the codebase and how many model calls are required to complete each code review. In some cases, the quota can be significantly greater than 100.

---

## 📊 QUOTAS FOR GEMINI IN BIGQUERY

### Code Assistance Features
For code assistance features, the quota for Gemini Code Assist and Gemini in BigQuery code requests (code completion, code generation) is the **same**.

### Advanced Features (Data Insights)
For customers using Gemini in BigQuery with:
- BigQuery on-demand compute, OR
- Enterprise or Enterprise Plus editions

Quotas for advanced features (data insights) are provided based on:
- **Daily average use of TiB scanned** (on-demand), OR
- **Slot-hours for the last full calendar month** (Enterprise/Enterprise Plus)

This quota applies at the **organization level** and is available to all projects in that organization. Quotas are rounded up to the nearest 100 slot-hour usage.

### Quotas Per 100 Slot-Hours

| Quota Type | Value |
|------------|-------|
| **Requests per day** for chat, visualization, table scans, and other requests that display responses in the Cloud Assist panel | 5 requests/day |

### Example Calculation

**Scenario:** An organization has an Enterprise edition reservation with 100 slots as its baseline.

**Calculation:**
- 100 slots × 24 hours = 2,400 slot-hours per day
- 2,400 slot-hours ÷ 100 = 24 (units of 100 slot-hours)
- 24 × 5 requests = **120 requests per day**

**Result:** They get 120 chat, visualizations, data insights table scans, and automated metadata generations per day in the following month.

### Default Quota (First Month)

If your organization has **not purchased** any BigQuery Enterprise edition, Enterprise Plus edition slots, or on-demand compute (TiB) until now, then after your first usage you will receive the default quota for the first full calendar month:

- **250 requests per day** for chat, visualizations, data insights table scans, and automated metadata generations

**Note:** If you start using on-demand compute, Enterprise edition, or Enterprise Plus edition reservations mid-month, then the default quota applies until the end of the following month.

---

## 🚀 HOW TO OBTAIN HIGHER DAILY MODEL REQUEST LIMITS

### For Individual Developers

To adjust agent mode and Gemini CLI quotas, you can purchase:

1. **Google Developer Program premium**
2. **Google AI Pro**
3. **Google AI Ultra**

### For Businesses/Organizations

We recommend purchasing:

1. **Standard edition** of Gemini Code Assist
2. **Enterprise edition** of Gemini Code Assist

**For more information:** See [View and manage quotas](https://cloud.google.com/generative-ai/code-assist/docs/manage-quotas) in the Google Cloud documentation.

---

## 📊 QUOTA COMPARISON TABLE

### Free vs Paid Tiers

| Feature | Free (Individual) | Google AI Pro | Google AI Ultra | Standard | Enterprise |
|---------|------------------|---------------|-----------------|----------|------------|
| **Requests/minute** | 60 | 120 | 120 | 120 | 120 |
| **Requests/day** | 1,000 | 1,500 | 2,000 | 1,500 | 2,000 |
| **Codebase context** | 1M tokens | 1M tokens | 1M tokens | 1M tokens | 1M tokens |
| **Repositories** | 20,000 | 20,000 | 20,000 | 20,000 | 20,000 |
| **GitHub PR reviews/day** | 33 | 33 | 33 | 33 | 100+ |

---

## ⚠️ IMPORTANT NOTES

### Rate Limiting
- If you exceed the per-minute quota, requests will be rate-limited
- If you exceed the per-day quota, you'll need to wait until the next day or upgrade

### Agent Mode
- One prompt in agent mode can result in **multiple model requests**
- This means you can hit quota limits faster than expected
- Monitor your usage in the Google Cloud Console

### GitHub Usage
- GitHub usage is **separate** from general Gemini Code Assist quotas
- You can use both without affecting each other's quotas

### BigQuery Integration
- Code assistance features share quotas with Gemini Code Assist
- Advanced features (data insights) have separate quotas based on BigQuery usage

---

## 🔍 TROUBLESHOOTING QUOTA ISSUES

### If You Hit Rate Limits

1. **Check Your Current Usage:**
   - Go to Google Cloud Console
   - Navigate to Gemini Code Assist quotas
   - Review your current usage

2. **Wait for Reset:**
   - Per-minute quotas reset every minute
   - Per-day quotas reset at midnight (your timezone)

3. **Upgrade Your License:**
   - Free tier: 60 req/min, 1,000 req/day
   - Pro/Standard: 120 req/min, 1,500 req/day
   - Ultra/Enterprise: 120 req/min, 2,000 req/day

### If You Need More Quota

1. **Individual Developers:**
   - Purchase Google AI Pro or Ultra
   - Join Google Developer Program premium

2. **Organizations:**
   - Purchase Standard or Enterprise edition
   - Contact Google Cloud sales for custom quotas

---

## 📚 RELATED DOCUMENTATION

- [Gemini Code Assist Documentation](https://cloud.google.com/generative-ai/code-assist/docs)
- [View and Manage Quotas](https://cloud.google.com/generative-ai/code-assist/docs/manage-quotas)
- [Gemini Code Assist Pricing](https://cloud.google.com/generative-ai/code-assist/pricing)
- `docs/setup/ALL_CURSOR_PROBLEMS_COMPREHENSIVE.md` - Complete problem documentation
- `docs/setup/GEMINI_CODE_ASSIST_LICENSE_ERROR.md` - License troubleshooting

---

## ✅ SUMMARY

**Key Takeaways:**

1. **Free tier is limited:** 60 req/min, 1,000 req/day
2. **Paid tiers offer more:** 120 req/min, 1,500-2,000 req/day
3. **GitHub usage is separate:** Doesn't count against general quotas
4. **Agent mode uses more:** One prompt = multiple requests
5. **BigQuery has separate quotas:** Based on slot-hours or TiB scanned

**For CBI-V14:**
- We're using Gemini Code Assist extension
- Current API key: `AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY`
- Project: `cbi-v14`
- If hitting quotas, consider upgrading to Pro/Standard/Enterprise

---

**Last Updated:** November 20, 2025  
**Source:** Google Cloud Documentation (2025-11-14 UTC)

