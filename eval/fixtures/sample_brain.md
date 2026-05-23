# WORKSPACE BRAIN — Acme Payments Dashboard
> Auto-injected at session start. Updated before any context compaction.
> Last sync: 2026-05-22 · Maintainer: Claude (with you)

## ACTIVE FOCUS

**Current goal**: Ship the merchant dashboard rewrite (React 19 + tRPC) by end of Q2.

**Current sprint (week of May 20)**: Stripe webhook signing + retry logic — required by
Acme Compliance before we can charge real cards. **Deadline: 2026-05-29.**

**Next on deck**: Multi-tenant subdomain routing (#412), invoice PDF export (#418).

## ACTIVE THREADS

- (in-progress) #432 Stripe webhook signing — branch `feat/stripe-signing`, ~80% done
- (in-progress) #429 Retry logic with exponential backoff — needs review
- (blocked) #418 Invoice PDF export — waiting on legal-approved template (Maria, by Fri)
- (pending) #412 Multi-tenant subdomain routing
- (done) #428 Migrate `users` table to UUID primary keys (2026-05-19)

## DECISIONS LOG

- **2026-05-21**: Going with HMAC-SHA256 for webhook signing, not JWS. Reason:
  Stripe's own SDK uses HMAC; matching them simplifies their SDK examples and removes
  a JWT library dependency.
- **2026-05-18**: Skipping Redis Cluster, sticking with single-node Redis. Reason:
  50k req/day is well under single-node limit; cluster ops cost isn't justified
  pre-product-market-fit.
- **2026-05-12**: Dropped Storybook. Reason: 90% of components are used in exactly
  one place; Storybook overhead exceeded documentation value.

## SYNAPSES

- **Stripe webhook handler** <-> `orders.fulfillment_state` enum — adding new
  webhook events requires schema enum update first
- **`api/auth/middleware.ts`** <-> all `/api/admin/*` routes — middleware order
  matters; `requireAdmin` MUST come after `requireAuth`
- **`prisma/schema.prisma`** <-> `staging` schema — migrations applied to staging
  manually until #420 ships the auto-apply GH Action

## KEY NUMBERS

- **Production**: `app.acmepay.com` (Vercel, region `iad1`, Postgres on Neon)
- **Staging**: `staging.acmepay.com`
- **Free-tier quotas**: Neon 100h compute/mo, Vercel 100GB bandwidth/mo
- **Build time budget**: < 4 min (currently 3:12)
- **p95 API latency target**: 200ms (currently 184ms)

## RECENT SESSIONS

- **2026-05-22**: Wired Stripe webhook signing into handler, mocked tests pass
- **2026-05-21**: Decided HMAC vs JWS, prototyped both
- **2026-05-19**: UUID migration shipped to prod; users table now ~2M rows

## OPEN QUESTIONS

- Do we need PCI compliance for the dashboard if all card data flows through
  Stripe Elements (i.e., never touches our servers)? Need legal answer by 2026-05-30.
- Should #418 (invoice PDF) be server-rendered (Puppeteer) or client-side (react-pdf)?
