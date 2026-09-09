# NovaTech RAG Chatbot

NovaTech RAG Chatbot is a Streamlit-based internal documentation assistant. It uses retrieval-augmented generation (RAG) to search a local knowledge base, provide relevant document excerpts to a language model hosted by Groq, and return concise answers with source attribution.

The project is designed as a practical reference implementation for building a small, explainable RAG application with Python, ChromaDB, Streamlit, and an OpenAI-compatible API.

## Project Description

The application lets users ask natural-language questions about NovaTech policies, engineering practices, onboarding procedures, security requirements, and product documentation.

For every question, the application:

1. Loads the text documents stored under `Data/`.
2. Splits each document into paragraph-sized chunks.
3. Embeds and indexes eligible chunks in ChromaDB.
4. Retrieves the three chunks most relevant to the question.
5. Sends the question and retrieved context to Groq.
6. Displays the generated answer, source filenames, and retrieved chunks.

The language model is instructed to answer only from the retrieved context. If the documents do not contain enough information, it should say so rather than inventing an answer.

### Features

- Natural-language search across multiple text documents
- Semantic retrieval with ChromaDB's default embedding function
- Context-grounded answer generation through Groq's OpenAI-compatible API
- Source attribution for every generated response
- Expandable display of the exact chunks used to construct an answer
- Streamlit session-based chat history
- Content-addressed Chroma collections that update when source content changes
- Persistent local Chroma storage under `.chroma_db/`
- User-friendly handling for connection, authentication, rate-limit, and model errors
- Local and Docker execution support

### Architecture

```text
User question
     |
     v
Streamlit chat interface
     |
     v
ChromaDB semantic query
     |
     v
Top three document chunks
     |
     v
Groq chat completion
     |
     v
Grounded answer + sources + retrieved chunks
```

### Knowledge Base

The included sample knowledge base contains:

| File | Subjects |
| --- | --- |
| `company_hr_policy.txt` | Leave, remote work, expenses, probation, performance, and conduct |
| `engineering_standard.txt` | Git workflow, code reviews, coding standards, APIs, and databases |
| `onboarding_guide.txt` | First-day setup, credentials, facilities, and first-week expectations |
| `product_knowledge_base.txt` | Cloud Desk Pro, account setup, cancellation, refunds, and integrations |
| `security_policy.txt` | Data privacy, networks, passwords, and incident response |

> **Important:** The supplied documents should be treated as demonstration data unless your organization has explicitly approved their use. Do not publish real internal documentation in a public repository or application.

### Project Structure

```text
NovaTech_RAG_Chatbot/
|-- Data/
|   |-- company_hr_policy.txt
|   |-- engineering_standard.txt
|   |-- onboarding_guide.txt
|   |-- product_knowledge_base.txt
|   `-- security_policy.txt
|-- streamlit_app.py
|-- requirements.txt
|-- Dockerfile
|-- .gitignore
`-- README.md
```

The application creates `.chroma_db/` at runtime. This generated directory is excluded from Git and can be rebuilt from the source documents.

## Prerequisites

Before installing the project, make sure the following tools and accounts are available:

- Python 3.11 or another version compatible with the pinned dependencies
- `pip`, included with a standard Python installation
- Git, for cloning and contributing
- A Groq account and API key
- Docker Desktop or Docker Engine, only if using the container workflow

The application requires outbound HTTPS access to `https://api.groq.com` for answer generation. Document retrieval remains local, but each request sends the retrieved context and the user's question to Groq.

## Installation Steps

### 1. Clone the repository

```bash
git clone https://github.com/komirishettyvinay/Rag_Chatbot_Deployement.git
cd Rag_Chatbot_Deployement
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Confirm that the active interpreter belongs to the new environment:

```bash
python --version
python -c "import sys; print(sys.executable)"
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The first ChromaDB indexing operation may initialize or download its default embedding model. Startup can therefore take longer on the first run.

### 4. Configure environment variables

Create a `.env` file in the repository root:

```dotenv
GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | Yes | None | Authenticates requests to the Groq API |
| `GROQ_MODEL` | No | `openai/gpt-oss-20b` | Selects a model enabled for the Groq account |

The application also recognizes the lowercase name `groq_api_key` for compatibility with older local configurations. `GROQ_API_KEY` is recommended.

Never commit `.env` or paste an API key into source code. The repository's `.gitignore` excludes `.env` by default.

### 5. Start the application

With the virtual environment activated:

```bash
python -m streamlit run streamlit_app.py
```

On Windows, the following command explicitly selects the project interpreter and avoids accidentally using a global Streamlit installation:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open `http://localhost:8501` if Streamlit does not open a browser automatically.

### Docker installation

Build the image from the repository root:

```bash
docker build -t novatech-rag-chatbot .
```

Run the container and load variables from the local `.env` file:

```bash
docker run --rm --env-file .env -p 10000:10000 novatech-rag-chatbot
```

Open `http://localhost:10000`.

The container filesystem is disposable. ChromaDB will rebuild its generated index when a new container is created. For this small knowledge base, rebuilding is usually acceptable. For larger or production workloads, use durable storage or a managed vector database.

## Basic Usage Examples

After the application reports that the document chunks have been indexed, enter a question in the chat input.

### Product account setup

```text
Explain the Cloud Desk Pro account setup process.
```

The answer should explain how to register, verify an email address, configure a support address, and invite team members. The response should cite `product_knowledge_base.txt`.

### Remote-work policy

```text
What is NovaTech's work-from-home policy?
```

The application retrieves the most relevant HR policy chunks and summarizes only the information present in those passages.

### Password requirements

```text
What are the password and MFA requirements for a new employee?
```

This question can retrieve information from both the onboarding and security documents. Source attribution makes the combined answer auditable.

### Engineering workflow

```text
What should an engineer do before merging a pull request?
```

The response should be grounded in `engineering_standard.txt`.

### Unsupported question

```text
What is NovaTech's office address in Tokyo?
```

If the retrieved documents do not answer the question, the model should respond that it does not have enough information.

### Inspecting retrieved evidence

Select **Show retrieved document chunks** below an assistant response to inspect:

- The exact text supplied to the language model
- The filename associated with each chunk
- Whether retrieval selected evidence relevant to the question

This view is useful for distinguishing retrieval problems from generation problems.

### Adding or updating documents

1. Add a UTF-8 `.txt` file under `Data/`, or edit an existing document.
2. Separate meaningful sections with blank lines.
3. Keep useful paragraphs at least 50 characters long because shorter chunks are ignored.
4. Restart the application or clear the Streamlit resource cache.

The application calculates a hash from the indexed content and creates a corresponding Chroma collection. Updated documents therefore produce a new index without deleting a collection that another Streamlit session may still be using.

## Deployment

### Streamlit Community Cloud

Streamlit Community Cloud is the simplest hosting option for this application:

1. Push the repository to GitHub.
2. Sign in to Streamlit Community Cloud.
3. Select the repository, branch, and `streamlit_app.py` entrypoint.
4. Add `GROQ_API_KEY` and `GROQ_MODEL` using the platform's secrets manager.
5. Deploy and review the build logs.

Do not commit `.env` or `.chroma_db/`. If the knowledge base contains non-public information, use private source control and restrict application access.

### Render

The included Dockerfile can be used to deploy a Render web service. Configure the Groq variables in the Render dashboard rather than committing `.env`.

Free instances can have limited CPU and memory and may use an ephemeral filesystem. ChromaDB may consequently rebuild its index after a restart. Verify memory usage and cold-start behavior before treating a free deployment as production-ready.

### Vercel

The Streamlit application is not designed for direct deployment as a conventional Vercel Function. A Vercel-oriented version would normally replace the Streamlit UI with a web frontend, expose the RAG pipeline through an ASGI API such as FastAPI, and use durable external vector storage.

## Troubleshooting

### `Missing GROQ_API_KEY`

Verify that `.env` exists in the repository root and contains a non-empty `GROQ_API_KEY`. Restart Streamlit after changing environment variables.

### `APIConnectionError`

Confirm that the machine or hosting provider permits outbound HTTPS connections to `api.groq.com`. Also check proxy, VPN, firewall, and DNS settings.

### Configured model is unavailable

The available Groq model catalog can change. Set `GROQ_MODEL` to a model enabled for the account and restart the application.

### `sqlite3.OperationalError: no such table: collections`

Make sure the current version of `streamlit_app.py` uses `chromadb.PersistentClient`. Stop all older Streamlit processes, remove `.chroma_db/` only if it is safe to rebuild the generated index, and then start one clean application process.

### Application uses an unexpected Python installation

Use the interpreter-explicit command:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Tracebacks should reference packages under the project's `.venv` directory rather than a global Python installation.

### Retrieval returns weak matches

- Confirm that the answer exists in a paragraph of at least 50 characters.
- Phrase the question with enough subject context.
- Review the retrieved chunks in the interface.
- Consider improving the chunking strategy or increasing `n_results` for a larger knowledge base.

## Security and Privacy

- Never commit `.env`, API keys, personal access tokens, or generated credentials.
- Treat all files under `Data/` as publishable when using a public Git repository.
- Retrieved chunks and user questions are sent to Groq for generation.
- Use authentication and access controls before deploying genuine internal documents.
- Rotate a credential immediately if it is accidentally committed or exposed in logs.
- Review third-party data handling and retention policies before production use.

## Contribution Guidelines

Contributions should remain focused, testable, and safe for users of the sample application.

### Development workflow

1. Fork the repository or create a feature branch:

   ```bash
   git checkout -b feature/short-description
   ```

2. Create and activate a local virtual environment.
3. Install dependencies from `requirements.txt`.
4. Make the smallest coherent change that solves the problem.
5. Run the validation checks described below.
6. Commit with a clear, imperative message.
7. Open a pull request describing the problem, solution, testing, and operational impact.

### Code standards

- Follow PEP 8 and use descriptive names.
- Keep retrieval, prompting, configuration, and presentation concerns understandable.
- Prefer environment variables for deployment-specific configuration.
- Add comments for non-obvious lifecycle behavior, not for self-evident syntax.
- Preserve source attribution and grounded-answer behavior.
- Avoid committing generated Chroma data, virtual environments, caches, or secrets.

### Validation

At minimum, run:

```bash
python -m py_compile streamlit_app.py
python -m pip check
python -m streamlit run streamlit_app.py
```

Then verify manually that:

- The application indexes the expected documents.
- A known question retrieves the correct source.
- The answer is supported by the displayed chunks.
- An unsupported question does not produce an invented answer.
- Missing or invalid API configuration produces a helpful message instead of a traceback.

### Pull-request expectations

A pull request should include:

- A concise summary of the change
- The motivation or issue being addressed
- Test evidence and reproduction steps
- Screenshots for visible interface changes
- Notes about new environment variables or deployment changes
- Confirmation that no secrets or confidential documents were added

Large architectural changes should be discussed before implementation. Dependency upgrades should explain compatibility implications for Streamlit, ChromaDB, the embedding runtime, and the selected Python version.

## License

No license is currently included. Unless a license is added, normal copyright restrictions apply and reuse or redistribution is not automatically granted.
