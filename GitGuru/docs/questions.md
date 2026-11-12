# GitGuru Evaluation Questions: 10 Real User Scenarios

This document defines 10 representative user questions for the **GitGuru** Git and GitHub assistant.
Questions 1 to 6 stem directly from the **GitGuru Project Card** core beginner competencies.
**Q6 is intentionally designed as an out-of-scope question that GitGuru's curated dataset cannot answer**, testing the system's boundary detection and fallback mechanism.

---

## The 10 User Questions

| # | Question | Category | Grounded in Knowledge Base? | Expected System Behavior |
|---|---|---|---|---|
| **Q1** | *"What is Git, and how is it different from GitHub?"* | Git & GitHub Fundamentals | **Yes** (Record IDs 1, 2) | Explains Git as distributed version control and GitHub as cloud hosting and collaboration platform. |
| **Q2** | *"How do I clone an existing remote repository onto my local machine?"* | Repository Operations | **Yes** (Record ID 4) | Recommends `git clone <url>` and explains local repository setup. |
| **Q3** | *"How do I stage changes and make a commit with a descriptive message?"* | Staging & Commits | **Yes** (Record IDs 5, 6) | Explains `git add <file>` / `git add .` followed by `git commit -m "<msg>"`. |
| **Q4** | *"How do I create a new branch, switch to it, and merge changes back into main?"* | Git Branching | **Yes** (Record IDs 9, 10) | Guides user through `git switch -c <branch>` and `git merge <branch>`. |
| **Q5** | *"How do I push local commits to a remote GitHub repository using git push?"* | Remote & GitHub Collaboration | **Yes** (Record ID 14) | Explains `git push -u origin <branch>` and upstream tracking. |
| **Q6** | *"How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"* | **Unanswerable / Out of Scope** | **NO (Cannot Answer)** | System should identify low similarity, refuse to hallucinate false recovery methods, and provide official documentation fallback. |
| **Q7** | *"How do I resolve a merge conflict in Git when two branches edit the same lines?"* | Troubleshooting & Conflicts | **Yes** (Record ID 11) | Explains conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), manual resolution, staging, and committing. |
| **Q8** | *"How do I undo a commit or discard uncommitted changes using git reset or revert?"* | Troubleshooting & Undo | **Yes** (Record ID 12) | Explains `git revert` for shared history vs `git reset --soft HEAD~1` for local, and `git restore` for unstaged files. |
| **Q9** | *"How do I temporarily save uncommitted work without committing so I can switch branches?"* | Working State & Stashing | **Yes** (Record ID 13) | Recommends `git stash` and `git stash pop`. |
| **Q10** | *"How do I set up and configure SSH key authentication for pushing to GitHub securely?"* | GitHub Authentication | **Yes** (Record ID 17) | Details `ssh-keygen -t ed25519`, ssh-agent configuration, and adding public keys to GitHub Settings. |

---

## Evaluation Benchmark & Analysis

### 1. In-Scope Questions (Q1-Q5, Q7-Q10)
All in-scope questions map directly to curated entries in `data/records.json`. When queried against the FastAPI endpoint `/search?q=...` or `POST /questions`, the TF-IDF vectorizer and cosine similarity engine rank the exact documentation records with high similarity scores ($> 0.25$).

### 2. The Unanswerable Question (Q6)
- **Prompt:** *"How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"*
- **Reason it cannot be answered:** GitGuru stores official Git SCM and GitHub documentation. It does not contain low-level forensic disk sector reconstruction routines, nor can Git restore data from a zero-overwritten physical storage medium without remote backups.
- **System Safeguard:** When processed by `POST /questions`, the highest similarity score falls below threshold or yields no actionable recovery method. The API gracefully triggers its fallback:
  > *"No high-confidence match found for your query. Consider checking official documentation."*

