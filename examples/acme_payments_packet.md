# Vendor Risk Decision Packet: Acme Payments

## Intake

- Vendor: Acme Payments
- Domain: acmepayments.example
- Business unit: SuiteScrape
- Requested service: Payment orchestration and subscription billing analytics
- Contract value: $36,000
- Data access: payment
- Urgency: expedited

## Recommendation

- Recommendation: `approve_with_controls`
- Weighted risk score: 30.98
- Risk level: `moderate`
- Confidence: 69.44
- Residual risk: `moderate`

## Rationale

Moderate weighted risk driven by payment data access, incomplete security assurance, and missing price benchmark.

## Domain Scores

| Domain | Score | Rationale | Evidence |
| --- | ---: | --- | --- |
| cybersecurity | 45 | Assurance incomplete. | ev_cyber_001 |
| data_privacy | 58 | Payment metadata requires DPA. | ev_privacy_001 |
| sanctions | 5 | No hit in supplied evidence set. | ev_sanctions_001 |
| litigation | 18 | No material litigation found. | ev_litigation_001 |
| financial_stability | 35 | Limited financial evidence. | ev_financial_001 |
| operational_dependency | 28 | Exit path available. | ev_dependency_001 |
| geographic | 12 | No elevated jurisdictional exposure. | ev_geo_001 |
| commercial | 32 | Benchmark required. | ev_commercial_001 |
| reputation | 20 | No severe reputation issue. | ev_reputation_001 |

## Missing Evidence

- completed_security_questionnaire
- dpa
- soc2_or_equivalent
- price_benchmark

## Required Controls

| Control | Owner | Due Before | Status |
| --- | --- | --- | --- |
| Execute DPA or equivalent privacy terms | legal | contract_signature | proposed |
| Complete vendor security questionnaire | security | production_access | proposed |
| Collect SOC 2 Type II or equivalent assurance report | security | production_access | proposed |
| Add breach notification clause with 72-hour notice window | legal | contract_signature | proposed |
| Benchmark quote against at least two alternatives | procurement | contract_signature | proposed |

## Negotiation Points

- Request DPA.
- Benchmark pricing.
- Ask for SOC 2 Type II.
- Negotiate data export rights.

## Evidence Register

| ID | Domain | Source | Confidence | Summary |
| --- | --- | --- | ---: | --- |
| ev_cyber_001 | cybersecurity | placeholder://questionnaire/acme-payments | 60 | Questionnaire requested but incomplete. |
| ev_privacy_001 | data_privacy | placeholder://contract/acme-payments-draft | 75 | Payment metadata and customer identifiers require DPA. |
| ev_sanctions_001 | sanctions | placeholder://watchlist/acme-payments | 80 | No sanctions hit in supplied evidence set. |
| ev_litigation_001 | litigation | placeholder://litigation-search/acme-payments | 65 | No material litigation found. |
| ev_financial_001 | financial_stability | placeholder://financial-profile/acme-payments | 55 | Private vendor; audited financials not supplied. |
| ev_dependency_001 | operational_dependency | placeholder://business-owner-note/suitescrape | 75 | Service is useful but not merchant of record; exit feasible. |
| ev_geo_001 | geographic | placeholder://vendor-profile/acme-payments | 70 | Primary operations listed as United States. |
| ev_commercial_001 | commercial | placeholder://quote/acme-payments | 80 | Quote plausible but not benchmarked. |
| ev_reputation_001 | reputation | placeholder://reputation-search/acme-payments | 65 | No severe reputation issue identified. |

## Approval Chain

| Role | Required | Status |
| --- | --- | --- |
| business_owner | True | pending |
| security | True | pending |
| legal | True | pending |
