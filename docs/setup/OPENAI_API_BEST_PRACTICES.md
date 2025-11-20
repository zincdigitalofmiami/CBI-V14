# OpenAI API Best Practices - CBI-V14

**Date:** November 2025  
**Status:** ✅ Implemented

---

## ✅ IMPLEMENTATION STATUS

Our Deep Research implementation follows OpenAI API best practices:

### 1. Authentication ✅
- **Method:** Bearer token authentication
- **Key Storage:** macOS Keychain (secure, no hardcoding)
- **Retrieval:** `src/utils/keychain_manager.py`
- **Header:** `Authorization: Bearer $OPENAI_API_KEY`

### 2. Request ID Tracking ✅
- **Implementation:** Unique UUID per request
- **Header:** `X-Client-Request-Id`
- **Purpose:** Troubleshooting and support
- **Format:** UUID (e.g., `123e4567-e89b-12d3-a456-426614174000`)

### 3. Error Handling ✅
- **Request IDs:** Logged with all errors
- **Exception Handling:** Proper try/catch blocks
- **Logging:** Request ID included in error messages

### 4. Response Headers ✅
- **Metadata:** Logged when available
- **Rate Limits:** Can be inspected from headers
- **Request IDs:** Captured for support

---

## 📋 OPENAI API HEADERS

### Request Headers (We Set)
```python
{
    "Authorization": "Bearer $OPENAI_API_KEY",
    "X-Client-Request-Id": "unique-uuid-per-request"
}
```

### Response Headers (We Log)
- `openai-organization` - Organization associated with request
- `openai-processing-ms` - Processing time
- `openai-version` - API version used
- `x-request-id` - Server-generated request ID
- `x-ratelimit-*` - Rate limiting information

---

## 🔧 IMPLEMENTATION DETAILS

### Deep Research Client
**File:** `src/utils/deep_research.py`

**Key Features:**
```python
# Generate unique request ID
request_id = str(uuid.uuid4())

# Include in request
response = client.responses.create(
    ...,
    extra_headers={
        "X-Client-Request-Id": request_id
    }
)

# Log for troubleshooting
logger.info(f"Request ID: {request_id}")
```

---

## 🚨 SECURITY BEST PRACTICES

### ✅ What We Do
1. **API Keys in Keychain** - Never hardcoded
2. **Server-Side Only** - Keys never exposed to client
3. **Environment Variables** - Fallback to env vars if needed
4. **No Client-Side Exposure** - Keys stay on server

### ❌ What We Don't Do
1. ❌ Hardcode keys in code
2. ❌ Commit keys to git
3. ❌ Expose keys in browser/client code
4. ❌ Share keys publicly

---

## 📊 RATE LIMITING

### Headers to Monitor
- `x-ratelimit-limit-requests` - Request limit
- `x-ratelimit-remaining-requests` - Remaining requests
- `x-ratelimit-reset-requests` - Reset time
- `x-ratelimit-limit-tokens` - Token limit
- `x-ratelimit-remaining-tokens` - Remaining tokens

### Implementation
```python
# Check rate limits from response headers
if hasattr(response, 'response_headers'):
    remaining = response.response_headers.get('x-ratelimit-remaining-requests')
    logger.info(f"Remaining requests: {remaining}")
```

---

## 🔍 TROUBLESHOOTING

### Using Request IDs
1. **Client Request ID:** Set by us (`X-Client-Request-Id`)
2. **Server Request ID:** Returned by OpenAI (`x-request-id`)
3. **Both logged** for support requests

### Support Requests
When contacting OpenAI support:
- Provide both request IDs
- Include error messages
- Share request timestamps
- Include rate limit headers

---

## 📚 REFERENCES

- OpenAI API Reference: https://platform.openai.com/docs/api-reference
- Authentication: https://platform.openai.com/docs/api-reference/authentication
- Rate Limits: https://platform.openai.com/docs/guides/rate-limits
- Error Handling: https://platform.openai.com/docs/guides/error-codes

---

**Status:** ✅ All best practices implemented in `src/utils/deep_research.py`


