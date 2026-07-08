# 🔬 ClearVoice — AI-Powered Medical Misinformation Checker



<p align="center">

  <b>Verify health claims using live peer-reviewed medical evidence.</b>

</p>



<p align="center">

  <a href="https://clear-voice-five.vercel.app">🌐 Live Demo</a> •

  <a href="https://manan77709-clearvoice-api.hf.space">⚡ API</a>

</p>



---



## 📖 Overview



**ClearVoice** is an AI-powered medical misinformation checker that evaluates health claims against **live peer-reviewed PubMed research** using a multi-agent retrieval and reasoning pipeline.



Unlike traditional RAG systems that rely on a static vector database, ClearVoice searches **PubMed in real time**, retrieves the latest relevant studies, evaluates their quality, and generates an evidence-based verdict with transparent reasoning.



Every prediction includes:



- ✅ Final verdict

- 📚 Supporting research papers

- 🧬 Study types

- ⭐ Evidence quality scores

- ⚖️ Whether studies support or contradict the claim

- 💬 Plain-English explanation

- 🎯 Practical takeaway



---



# ✨ Features



### 🔍 Live Medical Evidence Retrieval



- Searches PubMed in real time

- Uses the latest peer-reviewed studies

- No stale offline database



### 🧠 PubMedBERT Semantic Search



Medical-domain embeddings provide significantly better retrieval than generic embedding models.



- Model: **NeuML/pubmedbert-base-embeddings**

- 768-dimensional embeddings



---



### 🤖 Multi-Agent AI Pipeline



Instead of a single LLM prompt, ClearVoice uses specialized AI agents.



| Agent | Responsibility |

|---------|---------------|

| **Decomposer Agent** | Splits complex medical claims into simpler subclaims |

| **Verdict Agent** | Determines TRUE / FALSE / MISLEADING |

| **Judge Agent** | Scores evidence quality and determines stance |

| **Explainer Agent** | Produces easy-to-understand explanations |



---



### 📊 Evidence Transparency



Every retrieved paper includes:



- Study Type

- Evidence Quality (1–5)

- Supports / Contradicts / Neutral

- Confidence



Examples:



- Meta-analysis

- Systematic Review

- Randomized Controlled Trial

- Cohort Study

- Case-Control Study



---



### 🧾 Plain English Explanations



Medical literature is translated into language that non-experts can understand.



Each response contains:



- Why the claim received its verdict

- What researchers found

- Practical takeaway



---



### ⚡ Multi-Model LLM Fallback



If one Groq model becomes unavailable or rate-limited, ClearVoice automatically switches to another model.



Fallback chain:



```

Llama-3.3-70B

      ↓

Llama-4-Scout

      ↓

GPT-OSS-120B

      ↓

Llama-3.1-8B

```



---



### 🚀 Redis Caching



Repeated claims are cached for 24 hours.



Benefits:



- <100ms responses

- Reduced API cost

- Lower latency



---



# 🏗️ System Architecture



```

                    User Claim

                        │

                        ▼

              Redis Cache Lookup

               │              │

             Hit             Miss

               │              ▼

         Return Cached   Decomposer Agent

             Result            │

                               ▼

                 Live PubMed Retrieval

                               │

                               ▼

                PubMedBERT Embeddings

                               │

                               ▼

                     Retrieve Top Papers

                               │

             ┌─────────────────┴─────────────────┐

             ▼                                   ▼

      Verdict Agent                     Judge Agent

             │                                   │

             └───────────────┬───────────────────┘

                             ▼

                  Verdict Override Logic

                  (Mixed Evidence → MISLEADING)

                             │

                             ▼

                    Explainer Agent

                             │

                             ▼

                  Cache Response in Redis

                             │

                             ▼

                     Return to Frontend

```



---



# 📈 Performance



| Metric | Phase 1 | Phase 2 |

|----------|---------|----------|

| Accuracy | 60% | 90%+ |

| Embeddings | MiniLM (384d) | PubMedBERT (768d) |

| Retrieval | Pre-ingested DB | Live PubMed |

| Avg Response Time | 4.19s | ~10s |

| Cached Response | N/A | <100ms |

| MISLEADING Detection | 0% | 100% |

| Errors | 2/10 | 0/10 |



---



# 🚀 Development Journey



## Phase 1 — Baseline RAG



Implemented:



- FastAPI backend

- PubMed ingestion

- MiniLM embeddings

- Supabase pgvector

- Groq LLM

- Redis cache

- Streamlit frontend



Result:



- 60% benchmark accuracy



---



## Phase 2 — Medical RAG



Major improvements:



- PubMedBERT embeddings

- Live PubMed retrieval

- Multi-agent reasoning

- Judge agent

- Decomposer

- Explainer

- Verdict override logic

- Multi-model fallback



Result:



- 90%+ benchmark accuracy



---



## Phase 3 — Modern Frontend



Current version includes:



- React

- Vite

- Tailwind CSS

- Responsive UI

- Evidence cards

- Complex claim visualization



Deployment:



- Frontend → Vercel

- Backend → Hugging Face Spaces



---



## Phase 4 (Planned)



- 🎤 Whisper voice input

- 🌐 Chrome Extension

- 📱 Mobile responsive improvements

- 📊 50+ benchmark dataset

- 📈 User analytics dashboard



---



# 🛠 Tech Stack



| Layer | Technology |

|---------|-------------|

| Frontend | React + Vite + Tailwind CSS |

| Backend | FastAPI |

| Deployment | Hugging Face Spaces + Vercel |

| Embeddings | PubMedBERT |

| Vector Database | Supabase pgvector |

| Retrieval | PubMed + Biopython Entrez |

| LLM | Groq API |

| Cache | Upstash Redis |

| Language | Python |



---



# 📂 Project Structure



```

ClearVoice

│

├── backend

│   ├── main.py

│   │

│   └── app

│       ├── retrieval.py

│       ├── verify.py

│       ├── groq_client.py

│       │

│       └── agents

│           ├── decomposer.py

│           ├── judge.py

│           └── explainer.py

│

├── frontend-react

│

├── frontend

│

├── benchmark.py

│

├── accuracy.py

│

└── BENCHMARKS.md

```



---



# ⚙️ Installation



## Clone Repository



```bash

git clone https://github.com/MananBabbar07/ClearVoice.git



cd ClearVoice

```



---



## Create Virtual Environment



```bash

python -m venv venv

```



Windows



```bash

venv\Scripts\activate

```



Linux / macOS



```bash

source venv/bin/activate

```



---



## Install Dependencies



```bash

pip install -r requirements.txt

```



---



## Configure Environment Variables



Create a `.env` file.



```env

GROQ_API_KEY=your_key



DATABASE_URL=your_supabase_url



REDIS_URL=your_upstash_url



NCBI_EMAIL=your_email

```



---



## Run Backend



```bash

uvicorn backend.main:app --reload

```



---



## Run Frontend



```bash

cd frontend-react



npm install



npm run dev

```



---



# 🧪 Example Claim



Input:



> **"Vitamin C prevents the common cold."**



Output:



```

Verdict:

MISLEADING



Reason:



Vitamin C does not prevent colds in the general population,

although it may slightly reduce duration in certain individuals.



Evidence:



✓ Meta-analysis (Quality 5/5)



✓ Randomized Controlled Trial (4/5)



✗ One contradictory cohort study



Overall Confidence:

High

```


```

screenshots/



├── homepage.png



├── result.png



├── evidence_cards.png



└── decomposition.png

```



---



# 🔮 Future Work



- Voice-based medical verification

- Browser extension

- Larger benchmark dataset

- Medical citation export

- PDF report generation

- User authentication

- Saved history

- API rate limiting



---



# 👨‍💻 Author



**Manan Babbar**

GitHub:

https://github.com/MananBabbar07



---



# ⭐ If you found this project useful...



Please consider giving the repository a **Star ⭐**.