# Chat Context Distiller

Group chats pile up. Decisions, action items, and open questions get buried under jokes, memes, and side threads. Chat Context Distiller pulls out what matters: a short summary, decisions, tasks, and open questions. You paste or upload a chat log, run the pipeline, and get a distilled view plus a Q&A layer so you can ask things like "What is Alice responsible for?" or "What was decided about deployment?" without scrolling through hundreds of messages. It acts as a context distillation layer: raw chat goes in, structured intelligence comes out. You can filter by person, topic, or time, or use the Ask box to query the stored context. The backend embeds messages with sentence-transformers, clusters them with HDBSCAN, filters noise, and runs Mistral for extraction and summarization. ChromaDB holds the embeddings; when you ask a question, we retrieve the closest chunks and pass them to Mistral instead of the full transcript. That keeps token usage down and answers focused.

![Ingest](Screenshot%202026-02-02%20022837.jpg)

**Flow:** Ingest (paste or upload) → Analyze & Extract Context → Dashboard with summary, metrics, and Ask. The pipeline parses chat, embeds it, clusters by topic, filters low-signal messages, and calls Mistral for decisions, action items, open questions, and a ~250-word summary. The chat feature embeds your question, fetches the top-k similar messages from ChromaDB, and sends only those chunks to Mistral for the answer. No full-context dumps.

![Dashboard Summary](Screenshot%202026-02-02%20022921.jpg)

**Architecture:** FastAPI backend, React frontend, ChromaDB for vectors, Mistral for extraction and chat. Embeddings are local (sentence-transformers); only extraction and chat hit the API. Tokenomics is optimized by (1) only sending retrieved chunks to Mistral, not the full log; (2) using a single summary call per session instead of re-processing; (3) structuring extraction so we store decisions and action items once and reuse them. Future plans include caching repeated queries, batching small clusters, and using cheaper models for simple filters. An optional Discord bot lets you run `/distill` in a channel to process recent messages through the same pipeline.

![Ask about this chat](Screenshot%202026-02-02%20023114.jpg)
