# Document Grading and Query Rewriting Explained

This document describes how the Phase 4 intelligent agent uses **document grading**, **query rewriting**, and **hallucination checking** to improve RAG answer quality.

---

## Why retrieved documents are not always relevant

Vector and hybrid search return chunks by **similarity** (and keyword match), not by **relevance to the question**. A chunk can be similar in wording or topic but not actually answer the user’s question. Passing every retrieved chunk to the LLM can:

- Dilute the context with irrelevant text.
- Encourage the model to “fill in” from irrelevant parts and hallucinate.
- Waste tokens and slow down generation.

**Document grading** fixes this by having the LLM label each retrieved chunk as **relevant** or **irrelevant** before we build the final context. Only relevant chunks are used for the answer.

---

## How the LLM grades each chunk

1. **Input**: The user’s question and the list of retrieved chunks (with short identifiers, e.g. “Chunk 1”, “Chunk 2”).
2. **Prompt**: The model is asked to output one word per line, in order: either “relevant” or “irrelevant”.  
   - **Relevant**: The chunk helps answer the question or contains related information.  
   - **Irrelevant**: The chunk does not help answer the question.
3. **Output**: We parse the lines and keep only chunks marked “relevant”. Those are concatenated into the **context** string passed to the final generate step.

Prompt design keeps the task simple (binary, one line per chunk) so the grader stays fast and reliable. We use the same chat model (e.g. `gpt-4o-mini`) as the rest of the agent.

---

## The conditional rewrite loop

Sometimes the **first** query does not retrieve enough relevant chunks (e.g. wording mismatch). The agent can **rewrite** the question once and retry retrieval and grading.

1. After grading, we count how many chunks are relevant.
2. If that count is below a threshold (e.g. at least one) **and** we have not already rewritten (rewrite count &lt; 1):
   - We call the **rewrite_query** node: the LLM rephrases the user’s question (different wording, synonyms, or slightly different specificity).
   - We run **retrieve** again with the rewritten query.
   - We run **grade_documents** again on the new results.
3. If we still have too few relevant chunks, or we have already used our one rewrite, we proceed to **generate** with whatever relevant chunks we have (possibly none, in which case the model says it has no answer in the documents).

This avoids infinite loops (max one rewrite) while giving the system a second chance when the first query was poorly phrased.

---

## Hallucination checking: how the LLM verifies the answer

After the model generates an answer, we run a **hallucination check**:

1. **Input**: The same **context** (graded chunks) and the **assistant’s answer**.
2. **Prompt**: The model is asked to decide:
   - **Grounded**: Every factual claim in the answer is supported by the context (or is generic/common sense).
   - **Not grounded**: The answer adds facts, numbers, or details not present in the context.
3. **Output**: If the verdict is “not_grounded”, we allow **at most one retry**: we run **generate** again (with the same context) and then run the hallucination check again. If it is still not grounded, or we have already retried once, we keep the last answer and end.

This reduces the chance of the assistant “making up” details that are not in your documents, at the cost of one extra generate + check when the first attempt is flagged.

---

## The full LangGraph agent flow (with decision points)

A simplified view of the Phase 4 graph:

1. **Start** → **analyze_query**  
   - Classify: needs retrieval (factual) vs conversational.

2. **If conversational**  
   - Skip retrieval and go to **generate** with a conversational system prompt → **check_hallucination** → **End**.

3. **If needs retrieval**  
   - **expand_query** → **hybrid_retrieve** → **grade_documents**  
   - **Decision**:  
     - If enough relevant chunks (or already rewrote once) → **generate**.  
     - Else → **rewrite_query** → **retrieve_after_rewrite** → **grade_documents** again → then same decision (eventually **generate**).

4. **generate**  
   - Builds the answer from the graded context (or “no documents” / conversational prompt).  
   - Produces **source references** (filename, chunk index, snippet) from the graded chunks.

5. **check_hallucination**  
   - **Decision**:  
     - If **grounded** → **End**.  
     - If **not_grounded** and retry count &lt; 1 → **increment_hallucination_retry** → **generate** again → **check_hallucination** again → **End** (or one more retry as above).

All of this is reflected in the status labels you see in the UI (“Analyzing question…”, “Grading relevance…”, “Verifying answer…”, etc.) and in LangSmith traces.
