# Framework Coverage Audit

Authoritative source: the interview assignment supplied outside the repository; its
repository-safe requirement summary is `docs/requirements-traceability.md`.

This audit checks framework coverage, not implementation completion. `PASS` means the
final framework assigns an owner, behavior, and verification method to the requirement.

| Assignment section | Required coverage | Framework evidence | Result |
|---|---|---|---|
| 一、背景与目标 | Config → DB/charts/LLM/PDF; CLI first, API later; generated-list handoff | Final framework §§1, 13, 15; trace R-19 | PASS, index ownership explicit |
| 2.1 输入契约 | Exact config fields, 19-section order, unknown type fallback | Final framework §2; trace R-01/R-02 | PASS; project defines all 19 IDs |
| 2.2 输出契约 | `out/{id}`, md/pdf/charts/meta and fixed metadata fields | Final framework §3; trace R-03/R-04 | PASS; project defines metadata extensions |
| 核心要求 1 | Fixed-SQL → chart → one narration per section; max 19 | Final framework §§6/8; trace R-05/R-06 | PASS with explicit retry conflict decision |
| 核心要求 2 | All numbers code-calculated and traceable | Final framework §§5/7; trace R-07 | PASS |
| 核心要求 3 | Viewpoints grounded in real summaries/titles | Final framework §§5/7; trace R-08 | PASS |
| 核心要求 4 | Section failure isolation, visible missing mark, meta failure, retry/backoff | Final framework §§3/8/9; trace R-06/R-09 | PASS with bounded retry decision |
| 核心要求 5 | `.env` for PG and OpenAI-compatible LLM; no secrets | Final framework §§8/11; trace R-10 | PASS |
| 核心要求 6 | Cross-platform A4 PDF, CJK fonts, gold CSS | Final framework §10; trace R-11 | PASS; project creates the visual baseline |
| 核心要求 7 | Exact chart colors/style/150 dpi/insight title | Final framework §10; trace R-12 | PASS |
| 四、参考架构 | Shared scope; report type/language as parameters | Final framework §§4/5/6 | PASS; reference not treated as fixed contract |
| 五、开发环境 | Fixture Docker, env, sample SQL, gold report, 30-minute setup | Final framework §§14/17; trace R-16 | PASS; all supporting assets are project deliverables |
| M1 | CLI, Chinese 7/11 defaults, exact numbers, PDF quality, failure isolation | Final framework §§13–15; trace R-13 | PASS; default examples and fixtures are project deliverables |
| M2 | 19 sections, three input sections, English, arbitrary combinations | Final framework §§2/15/17; trace R-14 | PASS; project-defined section catalog is complete |
| M3 | POST/status/download, two concurrent jobs, restart persistence | Final framework §§3/13–15; trace R-15 | PASS |
| 上线范围 | Deployment, production switch, frontend integration/publishing excluded | Final framework §§1/13/16; trace R-18/R-19 | PASS |
| 七、工作约定 | Small commits, SQL integration, LLM stub, issue/PR decisions | Final framework §§14/16; trace R-17 | PASS |

## Audit conclusion

- Every assignment section is represented in the final framework.
- Every binding requirement has an implementation owner and verification evidence in
  the requirements traceability matrix.
- The fixed input/output contracts are preserved.
- The two textual tensions (LLM retry vs call cap; failure metadata vs shown schema)
  have explicit bounded product decisions.
- Every referenced but unprovided artifact is owned and delivered by this project.
