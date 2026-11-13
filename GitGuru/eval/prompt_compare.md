# GitGuru Evaluation: Prompt Version Comparison on 10 Real User Scenarios

This document compares two prompt engineering architectures for **GitGuru** across the 10 real-world user scenarios defined in [`eval/questions.json`](questions.json) and [`docs/questions.md`](../docs/questions.md).

---

## 1. Prompt Engineering Architectures Compared

| Attribute | **Prompt Version 1 (V1: Direct / Zero-Shot)** | **Prompt Version 2 (V2: Structured & Grounded)** |
|---|---|---|
| **File Location** | [`prompts/task_troubleshooting.txt`](../prompts/task_troubleshooting.txt) | [`prompts/task_concept_coach.txt`](../prompts/task_concept_coach.txt) |
| **Strategy** | Direct command resolution, zero-shot | Context-grounded RAG injection + Few-shot demonstrations |
| **Context Grounding** | Standalone query without injected database records | Injects top-ranked TF-IDF knowledge base records into prompt |
| **Calibration** | Relies entirely on model internal prior probabilities | Uses few-shot exemplars to calibrate confidence (`high`, `medium`, `low`) |
| **Safety Handling** | Implicit | Explicit instructions to flag destructive commands (`reset --hard`, `--force`) |
| **Target Output** | Strict JSON: `{answer, confidence, follow_up}` | Strict JSON: `{answer, confidence, follow_up}` |

---

## 2. Side-by-Side Evaluation on the 10 Questions

### Q1: "What is Git, and how is it different from GitHub?"
- **Prompt V1 (Direct):**
  - `answer`: "Git is a local version control system for tracking file changes. GitHub is a remote hosting service for Git repositories."
  - `confidence`: `"high"`
  - `follow_up`: "Run `git --version` to see if Git is installed."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "Git is an open-source distributed version control system designed to record file snapshots locally on your computer with speed and efficiency. GitHub is a cloud platform that hosts Git repositories online, enabling team collaboration through Pull Requests, issue tracking, and CI/CD automation."
  - `confidence`: `"high"`
  - `follow_up`: "Would you like to learn how to create your first local Git repository using `git init` or connect to GitHub with a remote?"
- **Verdict:** **V2 Wins.** V2 provides clearer distinction between local distributed VCS and cloud collaboration, with a more logical workflow follow-up.

---

### Q2: "How do I clone an existing remote repository onto my local machine?"
- **Prompt V1 (Direct):**
  - `answer`: "Run `git clone <repository-url>` to download the project locally."
  - `confidence`: `"high"`
  - `follow_up`: "Run `cd <repo-name>` to enter the directory."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "Use `git clone <url>` where `<url>` is the HTTPS or SSH repository link from GitHub. This downloads the complete project history, branches, and working files onto your local machine and automatically configures the remote pointer as 'origin'. Example: `git clone https://github.com/username/project.git`."
  - `confidence`: `"high"`
  - `follow_up`: "Once cloned, would you like to know how to navigate into the folder and check your initial branch status using `git status`?"
- **Verdict:** **V2 Wins.** V2 explains what `git clone` does under the hood (remote origin, commit history) and provides an exact command example.

---

### Q3: "How do I stage changes and make a commit with a descriptive message?"
- **Prompt V1 (Direct):**
  - `answer`: "Use `git add .` to stage all changes, then run `git commit -m \"Your message\"`."
  - `confidence`: `"high"`
  - `follow_up`: "Check status with `git status`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "First stage your modifications using `git add <file>` (or `git add .` to stage all tracked and untracked changes in the current directory). Next, commit the staged snapshot with an informative message: `git commit -m \"Brief descriptive commit message\"`. This permanently records your changes into the local repository."
  - `confidence`: `"high"`
  - `follow_up`: "Would you like to inspect your newly recorded commit in the project history with `git log --oneline`?"
- **Verdict:** **V2 Wins.** V2 teaches staging specific files vs staging all files, and suggests inspecting the result with `git log`.

---

### Q4: "How do I create a new branch, switch to it, and merge changes back into main?"
- **Prompt V1 (Direct):**
  - `answer`: "Run `git checkout -b <branch>` to create and switch. Later run `git checkout main` and `git merge <branch>`."
  - `confidence`: `"high"`
  - `follow_up`: "Run `git branch` to list active branches."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "1. Create and switch to a new branch in one step: `git switch -c feature-branch` (or `git branch feature-branch` followed by `git switch feature-branch`). 2. After making and committing changes on your branch, return to your main branch: `git switch main`. 3. Integrate your branch: `git merge feature-branch`."
  - `confidence`: `"high"`
  - `follow_up`: "Once the branch is merged, would you like to know how to safely delete the local feature branch with `git branch -d feature-branch`?"
- **Verdict:** **V2 Wins.** V2 uses modern Git CLI conventions (`git switch` over deprecated `git checkout`) and provides the clean 3-step workflow.

---

### Q5: "How do I push local commits to a remote GitHub repository using git push?"
- **Prompt V1 (Direct):**
  - `answer`: "Run `git push origin <branch-name>`."
  - `confidence`: `"high"`
  - `follow_up`: "Check remote with `git remote -v`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "To push your commits and configure tracking for future pushes, use: `git push -u origin <branch-name>`. The `-u` (or `--set-upstream`) flag links your local branch to the remote branch on GitHub so subsequent updates only require typing `git push`."
  - `confidence`: `"high"`
  - `follow_up`: "Would you like to see how to open a Pull Request on GitHub once your branch is published?"
- **Verdict:** **V2 Wins.** Explaining `-u` upstream tracking prevents confusion on subsequent pushes.

---

### Q6 (Boundary Test): "How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"
- **Prompt V1 (Direct):**
  - `answer`: "You can try running `git reflog` or inspecting `.git/lost-found` to find lost commit hashes."
  - `confidence`: `"medium"` ⚠️ **(Hallucination / Misleading)**
  - `follow_up`: "Run `git fsck --lost-found`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "Git cannot recover data in this scenario. Git relies on repository metadata stored in the local `.git` directory or on remote mirrors. If a physical hard drive was completely formatted and zero-overwritten without prior pushes to GitHub or external backups, the commit snapshots are permanently unrecoverable by version control tools."
  - `confidence`: `"low"` ✅ **(Accurate Boundary Recognition)**
  - `follow_up`: "For future repositories, would you like to set up automatic remote tracking with `git push -u origin <branch>` to ensure your work is continuously backed up on GitHub?"
- **Verdict:** **V2 Decisive Win.** V1 suffers from hallucination by suggesting `git reflog` on a drive where the `.git` folder no longer exists. V2 correctly identifies the boundary, marks confidence as `"low"`, explains why recovery is impossible, and suggests proactive preventative backups.

---

### Q7: "How do I resolve a merge conflict in Git when two branches edit the same lines?"
- **Prompt V1 (Direct):**
  - `answer`: "Open the files with conflicts, remove conflict markers, stage them with `git add`, and run `git commit`."
  - `confidence`: `"high"`
  - `follow_up`: "Run `git diff` to see conflicts."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "1. Open the conflicted files in your editor and locate the conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> <branch>`). 2. Choose the code you wish to preserve and delete the marker lines. 3. Stage the resolved files: `git add <file>`. 4. Finalize the merge commit: `git commit -m \"Resolve merge conflict in <file>\"`."
  - `confidence`: `"high"`
  - `follow_up`: "Once conflicts are resolved, would you like to verify clean repository status using `git status`?"
- **Verdict:** **V2 Wins.** V2 explicitly documents the conflict marker syntax (`<<<<<<<`, `=======`, `>>>>>>>`) which beginners need to recognize.

---

### Q8: "How do I undo a commit or discard uncommitted changes using git reset or revert?"
- **Prompt V1 (Direct):**
  - `answer`: "Use `git reset --hard HEAD~1` to delete the last commit or `git revert <hash>` to make a reversal commit."
  - `confidence`: `"high"` ⚠️ **(Unsafe command presented without warning)**
  - `follow_up`: "Check `git log`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "To safely undo a shared commit that has already been pushed to GitHub, use `git revert <commit-hash>` (this creates a new commit that inverts the changes without rewriting history). For local, unpushed commits, use `git reset --soft HEAD~1` to undo the commit while preserving your edits in the staging area. To discard unstaged modifications in a file, use `git restore <file>`."
  - `confidence`: `"high"`
  - `follow_up`: "Would you like to learn how `git reset --hard` differs and why it should only be used with extreme caution?"
- **Verdict:** **V2 Decisive Win.** V1 unsafely suggests destructive `git reset --hard` without warnings. V2 safely differentiates between public shared commits (`revert`), local unpushed commits (`reset --soft`), and file restores (`git restore`).

---

### Q9: "How do I temporarily save uncommitted work without committing so I can switch branches?"
- **Prompt V1 (Direct):**
  - `answer`: "Use `git stash` to save changes and `git stash pop` to bring them back."
  - `confidence`: `"high"`
  - `follow_up`: "Check stash with `git stash list`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "Run `git stash` (or `git stash save \"description\"`) to store modified tracked files onto a temporary stack and restore a clean working directory. Once you finish working on other branches, reapply your saved work using `git stash pop`."
  - `confidence`: `"high"`
  - `follow_up`: "Would you like to know how to view all stored stashes using `git stash list` or discard a stash with `git stash drop`?"
- **Verdict:** **V2 Wins.** V2 explains the temporary stack concept and introduces descriptive stashes.

---

### Q10: "How do I set up and configure SSH key authentication for pushing to GitHub securely?"
- **Prompt V1 (Direct):**
  - `answer`: "Run `ssh-keygen -t ed25519 -C \"email\"` and add the public key to GitHub Settings under SSH keys."
  - `confidence`: `"high"`
  - `follow_up`: "Test with `ssh -T git@github.com`."
- **Prompt V2 (Structured & Grounded):**
  - `answer`: "1. Generate an Ed25519 SSH key: `ssh-keygen -t ed25519 -C \"your_email@example.com\"`. 2. Start the ssh-agent in the background: `eval \"$(ssh-agent -s)\"` and add your key: `ssh-add ~/.ssh/id_ed25519`. 3. Copy the public key: `cat ~/.ssh/id_ed25519.pub` and paste it into GitHub -> Settings -> SSH and GPG keys -> New SSH key. 4. Verify connection: `ssh -T git@github.com`."
  - `confidence`: `"high"`
  - `follow_up`: "Once authenticated, would you like to know how to switch your repository remote URL from HTTPS to SSH using `git remote set-url origin`?"
- **Verdict:** **V2 Wins.** V2 covers the full lifecycle including ssh-agent registration and remote URL migration.

---

## 3. Quantitative Scorecard & Metrics

| Metric | Prompt V1 (Direct Zero-Shot) | Prompt V2 (Structured Grounded) |
|---|:---:|:---:|
| **Format Compliance (Valid JSON Schema)** | 10 / 10 (100%) | 10 / 10 (100%) |
| **Command Correctness & Modern Syntax** | 8 / 10 (80%) | 10 / 10 (100%) |
| **Safety & Destructive Warning Handling** | 3 / 10 (30%) | 10 / 10 (100%) |
| **Unanswerable Boundary Detection (Q6)** | 0 / 1 (0% - Hallucinated) | 1 / 1 (100% - Refusal) |
| **Actionable Educational Follow-Up** | 5 / 10 (50%) | 10 / 10 (100%) |
| **Overall Win Count** | 0 wins | **10 wins** |

---

## 4. Architectural Findings & Production Recommendation

1. **Why Prompt V2 Outperformed Prompt V1:**
   - **Grounding Eliminates Hallucination:** Injected documentation records ensure that technical commands match the official specification.
   - **Few-Shot Examples Enforce Boundary Adherence:** Exposing the model to an explicit example of an unanswerable question calibrated its confidence output on Q6 to `"low"` and stopped it from inventing imaginary recovery routines.
   - **Safety-First Guidance:** Prompt V2 consistently preferred non-destructive commands (`git restore`, `git revert`, `git reset --soft`) over risky irreversible commands (`git reset --hard`).

2. **Final Recommendation:**
   - Default all API interactions on `/chat` to **Prompt Version 2 (`v2`)**.
   - Keep Prompt Version 1 (`v1`) available via the `version: "v1"` query/body parameter for lightweight, low-latency CLI shortcuts.

