# Example: a job description drafted from mem0's public code

> **Unofficial example.** This posting was drafted by repo-aware-hiring from the public
> [mem0](https://github.com/mem0ai/mem0) repository (commit f1791da) to show what the tool produces on a large,
> real codebase (about 230,000 lines across Python and TypeScript, 25 packages). It is not a real job opening, and it
> is not affiliated with or endorsed by Mem0. Only the posting is shown: the internal codebase map, which lists the
> codebase's risks, is never published.

How it was made: the hiring manager picked the area (the core memory engine), the level (senior) and a one-line focus
("memory retrieval quality: search, reranking and the vector-store layer"), and skipped the questions about success
criteria, location and pay. Skipped answers became `[insert: …]` placeholders. The leak checker found nothing to
block; the stack is hinted through the work and the requirements, never listed.

---

## Senior Software Engineer, Memory Retrieval
[insert: location and working model] · [insert: employment type] · [insert: salary range]


### About the role
Mem0 gives AI agents a long-term memory. Developers use it to remember what their users said, prefer and decided,
and the quality of that memory comes down to one thing: finding the right memories at the right moment. You'll own
how our open-source memory engine retrieves and ranks memories, and make that quality measurable and consistent for
everyone who builds on it, whichever database they run it on.

### What you'll work on
- Improve how we fuse dense vector similarity, BM25-style keyword search and entity matching into one ranking, and
  prove each change with benchmarks before it ships.
- Make search quality consistent across the more than twenty vector databases we support, from dedicated vector
  engines to Postgres-based and Elasticsearch-style search, so developers get the same results whichever they choose.
- Build the evaluation tooling that turns retrieval tuning from judgement calls into measured decisions, and run it
  as part of development.
- Improve reranking and memory hygiene: rerankers from cross-encoders to LLM-based ones, spotting near-duplicate
  memories, and keeping what an agent remembers relevant over time, whichever LLM and embedding provider it runs on.
- Keep our Python engine and its TypeScript counterpart behaving the same, working with the engineers who own each.
- Review contributions from our open-source community and help them land well-tested changes.

### Must-haves
- You've built and tuned a search or retrieval system that real users depended on, and can explain how you measured
  whether it got better.
- You understand ranking: how keyword scoring such as BM25, dense embeddings and rerankers such as cross-encoders
  work, and the trade-offs in combining them.
- You write well-tested, maintainable Python libraries that other developers depend on, with typed data models
  (Pydantic or similar) and thorough automated tests.
- You can design an evaluation (datasets, metrics, baselines) and use it to make decisions.

### Nice-to-haves
- Experience with vector databases such as Qdrant, pgvector, Elasticsearch or OpenSearch, and how they differ in
  scoring and filtering.
- Natural-language processing in production with tools such as spaCy or NLTK, for example entity extraction or
  lemmatisation.
- Contributions to open-source projects, or experience working with an open-source community.
- Working knowledge of TypeScript.

### How we hire
[insert: interview steps and how long they take]

[insert: how AI-assisted screening is used and how to ask for adjustments or a human-only review; required in some jurisdictions]

### What we offer
[insert: benefits]

[insert: equal opportunity statement]
