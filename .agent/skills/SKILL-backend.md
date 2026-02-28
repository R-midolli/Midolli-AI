---

name: backend

description: >

&nbsp; Use este skill antes de criar qualquer arquivo Python no backend:

&nbsp; ingest.py, chain.py, main.py. Ensina as decisões de arquitetura,

&nbsp; o comportamento esperado de cada módulo, como fazer o fallback

&nbsp; de APIs e como configurar o FastAPI corretamente para o portfolio.

---



\# SKILL — Backend FastAPI + RAG Pipeline



\## Decisões de arquitetura



\*\*Por que FastAPI e não direto no JS?\*\*

As chaves de API (Gemini, NVIDIA) nunca podem ficar no JavaScript do frontend — ficam visíveis para qualquer pessoa que abre o DevTools. O backend é o proxy seguro.



\*\*Por que ChromaDB local e não Pinecone/Supabase?\*\*

Free tier sem cartão de crédito, funciona localmente, persiste em disco, simples de fazer deploy junto com o backend no Render.



\*\*Por que Gemini Flash e não Pro?\*\*

Free tier mais generoso (15 RPM, 1M tokens/dia), latência menor. Pro só se Flash não for suficiente.



---



\## Comportamento esperado de cada módulo



\### ingest.py

\- Lê todos os `.md` de `backend/knowledge/` em ordem alfabética

\- Divide cada arquivo em chunks de ~700 chars com overlap de 100

\- Gera embeddings com `models/text-embedding-004` em batches de \*\*50\*\* (respeitar rate limit)

\- Faz `upsert` no ChromaDB usando hash MD5 do `{arquivo}\_{índice\_chunk}` como ID

\- Imprime progresso a cada batch e total de chunks ao final

\- Se a collection não existir, cria. Se existir, atualiza só o que mudou.



\### chain.py

\- `retrieve(query)`: embeda a query com task\_type `retrieval\_query`, busca top-5 chunks

\- `answer(query, history)`: monta prompt com os 5 chunks como contexto → chama Gemini KEY\_1 → se falhar, KEY\_2 → se falhar, NVIDIA

\- O system prompt deve instruir o modelo a: responder no idioma da pergunta (FR ou EN automático), basear-se APENAS no contexto, ser conciso (máx 3 parágrafos), usar markdown para código/stack

\- Retornar sempre `{"reply": str, "sources": list\[str], "api\_used": str}`

\- Nunca levantar exceção para o caller — capturar e retornar mensagem de erro no campo `reply`



\### main.py

\- CORS configurado para: `https://r-midolli.github.io`, `http://localhost:3000`, `http://127.0.0.1:5500` e `http://localhost:8000`

\- GET `/health` → `{"status": "ok", "service": "Midolli-AI"}`

\- POST `/chat` → recebe `{message: str, history: list, lang: str}` → valida mensagem não vazia → chama `chain.answer()` → retorna `{reply, sources}`

\- Mensagem vazia → HTTP 400 com detalhe claro



---



\## O que NUNCA fazer



\- Não fazer ingestão dentro do endpoint `/chat` (lentíssimo — ingestão é só uma vez)

\- Não expor as chaves de API em nenhuma resposta JSON

\- Não usar `allow\_origins=\["\*"]` em produção sem mencionar para Rafael trocar depois

\- Não colocar lógica de negócio no `main.py` — ela fica no `chain.py`

\- Não criar endpoint sem testar com `curl` antes de marcar checkpoint

