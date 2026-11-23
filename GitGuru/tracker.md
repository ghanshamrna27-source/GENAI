# GitGuru — Deployment & CI/CD Tracker

This tracker monitors the CI/CD pipeline, automated testing status, and live production deployment URLs for **GitGuru** (Day 12).

---

## 1. Project Information
- **Project:** GitGuru (Git & GitHub Knowledge Assistant)
- **Domain:** Version Control, GitHub Workflows, and Developer Education
- **Repository:** [`https://github.com/ghanshamrna27-source/GENAI`](https://github.com/ghanshamrna27-source/GENAI)
- **Primary Working Directory:** `GitGuru/`
- **Current Milestone:** Day 12 — CI/CD with GitHub Actions & Production Deployment

---

## 2. CI/CD Pipeline Status
- **Workflow File:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- **CI Workflow URL:** [`https://github.com/ghanshamrna27-source/GENAI/actions/workflows/ci.yml`](https://github.com/ghanshamrna27-source/GENAI/actions/workflows/ci.yml)
- **Pipeline Badge:**  
  [![CI Pipeline](https://github.com/ghanshamrna27-source/GENAI/actions/workflows/ci.yml/badge.svg)](https://github.com/ghanshamrna27-source/GENAI/actions/workflows/ci.yml)
- **Automated Verification Gates:**
  1. **Ruff Lint Check:** Fast static analysis enforcing PEP 8 and clean formatting.
  2. **Pytest Test Suite:** 27 unit and integration tests covering records, search, `/health`, `/ask` with fake LLM, and agent tools.
  3. **Docker Build:** Multi-stage image build testing `Dockerfile` build context.

---

## 3. Production Deployment Tracker
| Service | Platform | Live URL | Endpoint / Function | Health Status |
|---|---|---|---|:---:|
| **GitGuru API Backend** | Render | `https://gitguru-api.onrender.com` | FastAPI Core Service | 🟢 Operational |
| **Public Health Check** | Render | `https://gitguru-api.onrender.com/health` | System & Record Stats (`GET /health`) | 🟢 200 OK |
| **Interactive API Docs** | Render | `https://gitguru-api.onrender.com/docs` | OpenAPI / Swagger UI | 🟢 Available |
| **Streamlit Interactive UI** | Render | `https://gitguru-ui.onrender.com` | Live Chat & Branch Visualizer | 🟢 Operational |
| **Hugging Face Spaces** | HF Spaces | `https://huggingface.co/spaces/ghanshamrna27-source/GitGuru` | Public Community Demo | 🟢 Mirror Ready |

---

## 4. Public Health Check Specification
- **Endpoint:** `GET https://gitguru-api.onrender.com/health`
- **Method:** `GET`
- **Expected Status Code:** `200 OK`
- **Response Schema:**
```json
{
  "status": "ok",
  "project": "GitGuru",
  "description": "Git & GitHub Learning Assistant API",
  "records_count": 20,
  "version": "1.0.0"
}
```

---

## 5. Merged Pull Request Tracker
- **Feature Branch:** `feature/ci-cd-and-deployment`
- **Target Branch:** `main`
- **PR Title:** `Day 12: CI/CD Pipeline (Ruff, Pytest, Docker Build) & Live Deployment`
- **PR Link:** [PR #1 on GitHub](https://github.com/ghanshamrna27-source/GENAI/pull/1)
- **CI Status on PR:** 🟢 Green / Passed ([Run #45088026792](https://github.com/ghanshamrna27-source/GENAI/actions/runs/45088026792))
- **Merge State:** 🟢 Merged into `main` (Merge Commit: `b396f96`)
- **Main Branch CI Run:** 🟢 Green / Passed ([Run #45088418951](https://github.com/ghanshamrna27-source/GENAI/actions/runs/45088418951))
