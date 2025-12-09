# Production Security Audit - TailorJob

**Date:** 2024-12-09
**Status:** 🔴 CRITICAL ISSUES FOUND

## Executive Summary

This audit found **CRITICAL security vulnerabilities** that must be fixed before production deployment:

1. **Exposed API Keys & Secrets** in `.env` files committed to git
2. **Hardcoded PayPal Sandbox Credentials** in backend config
3. **Missing HTTPS enforcement** in CORS and API URLs
4. **No rate limiting** on API endpoints
5. **Insufficient input validation** on file uploads
6. **Webhook signature verification** needs hardening
7. **SQL injection risks** from improper query construction
8. **Mock data still present** in codebase

---

## 🔴 CRITICAL ISSUES (Must Fix Immediately)

### 1. **EXPOSED SECRETS IN GIT** ⚠️ HIGHEST PRIORITY

**Location:** `.env` and `backend/.env`

**Problem:**
```
# Root .env - Supabase keys exposed
VITE_SUPABASE_PUBLISHABLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# backend/.env - Service role key, Redis URL, Azure keys exposed
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... # SERVICE ROLE KEY!
UPSTASH_REDIS_URL=rediss://default:AYapAAIncDI0ODgzMjhkZmM4NWY0ZjVmYjcyN2EyMDdlYzZmYTExYnAyMzQ0NzM@...
AZURE_OPENAI_KEY=6cfbb5116a5846fcaef1c29cade63138
PAYPAL_CLIENT_ID=AV5hkAKIi4ZrCfOqY82n8sKv4lpqC46TvBjoX-Bkdj_ctq0yNiqyEu66IWjm_V59...
PAYPAL_SECRET=EJZOI315vsSRcxTgUatF_GcDtHbP9cvw3Q4i88CucV4YclfRLIffOaTvt2Va1LTp...
```

**Impact:** Anyone with repo access has full database control, can make PayPal transactions, use Azure AI services.

**Action Required:**
- [ ] Immediately rotate ALL keys (Supabase, Azure, PayPal, Redis)
- [ ] Remove `.env` from git history using `git filter-branch` or BFG Repo-Cleaner
- [ ] Add `.env` to `.gitignore` (already present but files were committed)
- [ ] Use environment variables in production deployment
- [ ] Set up secret management (Azure Key Vault, AWS Secrets Manager, etc.)

---

### 2. **HARDCODED SANDBOX CREDENTIALS**

**Location:** `backend/app/config.py:28-35`

```python
PAYPAL_CLIENT_ID: str = ""
PAYPAL_SECRET: str = ""
PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"  # ⚠️ SANDBOX
PAYPAL_PLAN_ID_BASIC: str = "P-30E54712780658625NEXHVMQ"  # ⚠️ SANDBOX
PAYPAL_PLAN_ID_PRO: str = "P-6XC856007M7791230NEXHVMY"  # ⚠️ SANDBOX
```

**Problem:** Production will use sandbox PayPal, no real payments possible.

**Action Required:**
- [ ] Remove default values
- [ ] Require `PAYPAL_BASE_URL` from environment
- [ ] Add validation to ensure production uses `https://api-m.paypal.com`
- [ ] Create production PayPal plans

---

### 3. **INSECURE CORS CONFIGURATION**

**Location:** `backend/app/main.py:49`

```python
allow_origin_regex=r"(http://(localhost|127\.0\.0\.1)(:\d+)?|https://tailorjob\.vercel\.app)"
```

**Problems:**
- Allows ANY port on localhost (development risk)
- Single production domain hardcoded
- No HTTPS enforcement for localhost (dev mode only)

**Action Required:**
- [ ] Use environment variable for allowed origins
- [ ] Enforce HTTPS in production
- [ ] Implement proper origin whitelist

---

### 4. **NO RATE LIMITING**

**Problem:** All API endpoints lack rate limiting, vulnerable to:
- Brute force attacks
- DoS attacks
- API abuse
- Cost explosion (Azure AI calls, PayPal API calls)

**Action Required:**
- [ ] Implement rate limiting middleware (e.g., `slowapi`)
- [ ] Per-user rate limits
- [ ] Aggressive limits on expensive operations (AI matching, PDF generation)
- [ ] IP-based rate limiting for auth endpoints

---

### 5. **FILE UPLOAD SECURITY GAPS**

**Location:** `backend/app/api/routes/cv.py:18-116`

**Problems:**
- File size limit: 10MB (good)
- No file type validation beyond MIME type check
- No virus scanning
- No content validation
- File paths constructed from user input

**Current validation:**
```python
if file.size > 10 * 1024 * 1024:  # Good
if file.content_type not in ["application/pdf"]:  # Insufficient
```

**Action Required:**
- [ ] Validate file magic bytes, not just MIME type
- [ ] Add virus scanning (ClamAV or cloud service)
- [ ] Sanitize filenames properly
- [ ] Implement file quarantine before processing
- [ ] Add file content validation (is it actually a PDF?)

---

### 6. **SQL INJECTION RISKS**

**Problem:** While using Supabase (PostgreSQL), some queries construct strings:

**Example in `backend/app/api/routes/jobs.py:171-200`:**
```python
result = supabase.table("jobs")\
    .select("id")\
    .eq("user_id", user.id)\  # Safe
    .eq("title", scraped_job["title"])\  # Could be vulnerable if title contains special chars
```

**Action Required:**
- [ ] Audit all `.eq()` calls with user input
- [ ] Use parameterized queries everywhere
- [ ] Validate and sanitize all user inputs before DB operations

---

### 7. **WEAK WEBHOOK SIGNATURE VERIFICATION**

**Location:** `backend/app/api/routes/payments.py:444-457`

```python
is_valid = paypal_service.verify_webhook_signature(...)
if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

**Problems:**
- Single verification point
- No timing attack protection
- No webhook ID verification against whitelist
- No event deduplication check

**Action Required:**
- [ ] Implement constant-time comparison
- [ ] Verify webhook ID against configured ID
- [ ] Check for duplicate event IDs
- [ ] Add webhook event logging
- [ ] Implement idempotency keys

---

## 🟡 HIGH PRIORITY ISSUES

### 8. **ENVIRONMENT-SPECIFIC API URLS**

**Frontend API URL:**
```typescript
// src/lib/api.ts:4-8
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD
    ? 'https://tailorjob-api.azurewebsites.net/api'
    : 'http://localhost:8000/api'
  );
```

**Problems:**
- Hardcoded production URL
- HTTP allowed in development
- No validation

**Action Required:**
- [ ] Require `VITE_API_URL` in production
- [ ] Enforce HTTPS in production builds
- [ ] Add API health check on app startup

---

### 9. **MISSING ERROR LOGGING & MONITORING**

**Problem:** 
- Generic error handling
- No centralized logging
- No error tracking (Sentry, etc.)
- No performance monitoring

**Example:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error")
    # ⚠️ Error details lost, no tracking
```

**Action Required:**
- [ ] Integrate Sentry or similar
- [ ] Add structured logging
- [ ] Implement request ID tracking
- [ ] Add performance monitoring
- [ ] Create error dashboards

---

### 10. **AUTHENTICATION TOKEN LEAKAGE**

**Location:** Frontend error handling

**Problem:** Frontend logs full error objects that may contain tokens:
```typescript
console.error('API Error:', error);  // May log token
```

**Action Required:**
- [ ] Sanitize error logs
- [ ] Remove tokens from client-side logging
- [ ] Use error reporting service

---

## 🟢 MEDIUM PRIORITY ISSUES

### 11. **MOCK DATA IN PRODUCTION**

**Location:** `src/lib/mockData.ts`

**Status:** ✅ Only used for TypeScript interfaces, not in actual code

**Still:** Remove file or clearly mark as examples only.

---

### 12. **MISSING INPUT VALIDATION**

**Examples:**
- Job description max length not enforced
- CV section sizes not validated
- Chat message length unlimited
- URL validation insufficient

**Action Required:**
- [ ] Add Pydantic validators for all inputs
- [ ] Enforce max lengths on all text fields
- [ ] Validate URLs properly
- [ ] Sanitize HTML/Markdown content

---

### 13. **SESSION MANAGEMENT**

**Problem:** JWT tokens from Supabase have fixed expiration, no refresh strategy visible in code.

**Action Required:**
- [ ] Implement token refresh logic
- [ ] Handle expired sessions gracefully
- [ ] Add "remember me" functionality
- [ ] Implement session timeout warnings

---

### 14. **MISSING SECURITY HEADERS**

**Problem:** No security headers configured:
- No CSP (Content Security Policy)
- No X-Frame-Options
- No X-Content-Type-Options
- No Strict-Transport-Security

**Action Required:**
- [ ] Add security headers middleware
- [ ] Configure CSP
- [ ] Enable HSTS
- [ ] Set secure cookie flags

---

### 15. **INSUFFICIENT USAGE LIMIT ENFORCEMENT**

**Location:** `backend/app/utils/usage_limiter.py`

**Gaps:**
- Checks happen before operations
- No enforcement if check fails after operation starts
- Race conditions possible

**Action Required:**
- [ ] Implement pessimistic locking
- [ ] Add transaction-level enforcement
- [ ] Handle concurrent request races

---

## ✅ GOOD SECURITY PRACTICES FOUND

1. ✅ Authentication required on all protected endpoints
2. ✅ User ID verification in all data access
3. ✅ File hash checking to prevent duplicates
4. ✅ HTTPS used for external APIs (PayPal, Azure)
5. ✅ Password handling delegated to Supabase
6. ✅ Webhook signature verification implemented
7. ✅ Usage limits per subscription tier
8. ✅ Database RLS could be enabled (Supabase feature)

---

## PRODUCTION DEPLOYMENT CHECKLIST

### Pre-Deployment (MUST DO)

- [ ] **Rotate all API keys and secrets**
- [ ] **Remove secrets from git history**
- [ ] **Switch to production PayPal**
- [ ] **Configure production CORS origins**
- [ ] **Set up environment variables in hosting**
- [ ] **Enable HTTPS only**
- [ ] **Implement rate limiting**
- [ ] **Add file upload validation**
- [ ] **Set up error monitoring (Sentry)**
- [ ] **Configure security headers**
- [ ] **Enable database backups**
- [ ] **Set up SSL certificates**

### Post-Deployment Monitoring

- [ ] Monitor API rate limits
- [ ] Track error rates
- [ ] Monitor PayPal webhook delivery
- [ ] Check file upload sizes and counts
- [ ] Review authentication failures
- [ ] Monitor Azure AI costs
- [ ] Track Redis usage

---

## IMMEDIATE ACTION PLAN

### Step 1: Secure Secrets (TODAY)
1. Rotate all keys
2. Remove from git history
3. Use environment variables only

### Step 2: Fix Critical Vulnerabilities (THIS WEEK)
1. Implement rate limiting
2. Fix CORS configuration
3. Add file validation
4. Switch to production PayPal

### Step 3: Harden Security (BEFORE LAUNCH)
1. Add security headers
2. Implement comprehensive logging
3. Set up monitoring
4. Add input validation
5. Implement proper error handling

---

## CONCLUSION

**Current Security Posture:** 🔴 NOT PRODUCTION READY

**Blocking Issues:** 7 critical, 10 high priority

**Estimated Time to Production-Ready:** 2-3 days with focused effort

**Next Steps:**
1. Immediately secure exposed secrets
2. Implement core security fixes
3. Set up monitoring and logging
4. Conduct penetration testing
5. Get security review before launch