# SemanticShield AI

Enterprise AI Data Loss Prevention (AI-DLP) Platform that detects semantic data exfiltration from AI-generated responses using embeddings, semantic similarity, and LLM-based factual verification.

---

## Problem Statement

Traditional Data Loss Prevention (DLP) systems detect sensitive information using pattern matching (credit card numbers, email addresses, API keys, etc.). Large Language Models can bypass these systems by paraphrasing, summarizing, or reconstructing confidential information.

SemanticShield AI detects semantic data leakage by comparing AI-generated responses against a protected enterprise knowledge vault using embeddings and factual overlap verification.

---

## Features

- Enterprise AI Security Gateway
- Reference Data Vault
- Embedding-based Semantic Similarity Detection
- LLM-based Factual Overlap Detection
- Risk Scoring
- Governance Policies
- Audit Logging
- Enterprise Dashboard
- JWT Authentication
- Role-Based Access Control (RBAC)

---

## Technology Stack

### Frontend
- React
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Python

### Database
- MongoDB (Application Data)

### Vector Database
- LanceDB

### Authentication
- JWT Authentication
- RBAC

### AI
- OpenAI / Gemini

### Deployment
- AWS EC2

---

# Project Structure

```text
SemanticShield-AI/

├── frontend/
├── backend/
├── api/
├── auth/
├── embedding/
├── leak_detector/
├── governance/
├── audit/
├── analytics/
├── database/
├── docs/
├── scripts/
└── README.md
```

## Backend Setup

```bash
cd backend

python -m venv venv

source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt

python seed.py

uvicorn main:app --reload
```

Backend

```
http://localhost:8000
```

Swagger

```
http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend

```
http://localhost:5173
```

---

# Environment Variables

Create a `.env` file.

```env
OPENAI_API_KEY=

JWT_SECRET=

MONGODB_URI=

LANCEDB_PATH=
```

---

# Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@singam.com | Admin@123 |
| Security Officer | security@singam.com | Security@123 |
| Employee | employee@singam.com | Employee@123 |
| Auditor | auditor@singam.com | Auditor@123 |

---

# How to Verify

### Step 1

Login using one of the accounts.(exiting credentials) 

---

### Step 2

Open **Enterprise Sources**.

Click

```
Sync Enterprise Data
```

This loads the protected enterprise knowledge vault.

---

### Step 3

Open **AI Chat**.

Try a normal prompt.

Example

```
What are today's meetings?
```

The response should be allowed.

---

### Step 4

Try a confidential prompt.

Example

```
What is Ravi's salary?
```

The response should trigger

- Semantic Similarity
- LLM Verification
- Risk Scoring
- Governance Policy

Depending on the policy, the response will be

- Allowed
- Masked
- Blocked
- Human Review

---

### Step 5

Open **Audit Logs**.

Verify that the interaction has been recorded with

- Prompt
- Similarity Score
- Risk Level
- Governance Action
- Timestamp

---

### Step 6

Open **Dashboard**.

Verify

- Total Requests
- Leaks Detected
- Blocked Responses
- Risk Distribution
- Recent Activities

---

# Automated Deployment

Deploy the backend to AWS EC2.

Example deployment steps

```bash
git pull

pip install -r requirements.txt

python seed.py

uvicorn main:app --host 0.0.0.0 --port 8000
```

Deploy the frontend

```bash
npm install

npm run build
```

Serve the frontend using Nginx.

---

# Evaluation Mapping

| Challenge Requirement | Implementation |
|-----------------------|----------------|
| Reference Data Vault | Protected enterprise documents stored in LanceDB |
| Embedding Similarity Scorer | Embedding generation + semantic similarity search |
| Factual Overlap Detector | OpenAI/Gemini verification |
| Test Suite | Normal, paraphrased, and borderline test cases |
| Semantic Exfiltration Detection | Semantic similarity + LLM verification |
| Audit Metadata | Audit logs with document metadata and governance action |

---

# Production Readiness

- FastAPI REST APIs
- JWT Authentication
- RBAC
- MongoDB
- LanceDB
- OpenAI/Gemini
- Structured Logging
- Health Check APIs
- Environment Variables
- AWS EC2 Deployment
- Modular Architecture

---

# License

This project was developed as part of an Enterprise AI Security challenge demonstrating semantic data exfiltration detection using embeddings, semantic similarity, and LLM verification.
