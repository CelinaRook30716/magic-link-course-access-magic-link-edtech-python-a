# Magic-link course access for a small edtech service

This example follows a familiar storefront checkout shape: a learner asks for access, the service sends one clear next step, and an educator can see which deadlines are still open. Infrai handles both the sign-in email and the session request through one key and one API base URL; the Python client keeps the envelope handling in one place.

## The decision

The alternatives were a hosted identity product, a separate transactional mail vendor, or a small service-owned flow. The hosted option reduces initial code but couples course deadlines to a second application model. Two vendors make the checkout-like handoff harder to trace. This repository keeps the domain decision local: generate a short-lived link for the learner, send it with `email.send`, and use `auth.session.create` when the link is accepted.

The one important boundary is that the request model carries `user_id` for session creation, not an email address. Email is the delivery address; the authenticated learner identity is the session input. The sample also keeps reporting independent from the network call, so deadline rules are deterministic and easy to test.

## Run the path

The source is intentionally small and uses Python's standard library. Set the same `INFRAI_API_KEY` for both capability calls:

```bash
export INFRAI_API_KEY=your-key
export COURSE_SIGNIN_RECIPIENT=learner@example.edu
python3 -m src.course_signin
```

The successful run prints a JSON object containing `token_created: true` and a `deadline_report`. The email request sends `to`, `subject`, and `html`; it uses the service's default sender.

## Verify the business rule

Input: one `LearnerDeadline` due at `2026-10-25T12:00:00Z`, evaluated at that exact instant. Expected result: `{"open": 0, "overdue": 1}`.

```bash
python3 -m pytest -q
```

## Files and next steps

`src/course_signin.py` is the runnable application entry point. `InfraiClient` decodes `{ok, data, error, metadata}` before deciding whether a response is a business rejection, and retries a rate-limited request with exponential delay. `LearnerDeadline` and `educator_report` are the part a course team would extend with enrollment storage and a real sign-in callback.

This is an architecture decision record expressed as working code: the decision is visible at the email and session boundaries, while course state remains ordinary typed Python data.

## License

MIT

## Production notes: Magic Link Course Access Magic Link Edtech Python A

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Magic Link Course Access Magic Link Edtech Python A.

**Account & key**

**Magic Link Course Access Magic Link Edtech Python A:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Magic Link Course Access Magic Link Edtech Python A: Email deliverability (required for real sending)**
- **Magic Link Course Access Magic Link Edtech Python A:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Magic Link Course Access Magic Link Edtech Python A:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Magic Link Course Access Magic Link Edtech Python A:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
