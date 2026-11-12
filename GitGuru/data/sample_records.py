records = [
    {
        "id": 1,
        "category": "Git",
        "title": "About Git",
        "keyword": "git",
        "question": "What is Git?",
        "answer": "Git is a free and open source distributed version control system designed to handle everything from small to very large projects with speed and efficiency.",
        "source_url": "https://git-scm.com/doc"
    },
    {
        "id": 2,
        "category": "GitHub",
        "title": "About GitHub",
        "keyword": "github",
        "question": "What is GitHub?",
        "answer": "GitHub is a cloud-based hosting platform that lets developers store, manage, track, and collaborate on Git repositories using pull requests, issues, and discussions.",
        "source_url": "https://docs.github.com/en/get-started"
    },
    {
        "id": 3,
        "category": "Git",
        "title": "Initialize Repository (git init)",
        "keyword": "init",
        "question": "How do I create a new local Git repository?",
        "answer": "Run 'git init' inside your project directory. This initializes a new Git repository by creating a hidden .git subdirectory containing Git metadata.",
        "source_url": "https://git-scm.com/docs/git-init"
    },
    {
        "id": 4,
        "category": "Git",
        "title": "Clone Repository (git clone)",
        "keyword": "clone",
        "question": "How do I clone an existing repository?",
        "answer": "Use 'git clone <url>' to download a full copy of a remote repository including all files, branches, and commit history onto your local machine.",
        "source_url": "https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository"
    },
    {
        "id": 5,
        "category": "Git",
        "title": "Stage Changes (git add)",
        "keyword": "stage",
        "question": "How do I stage files for a commit?",
        "answer": "Use 'git add <filename>' to stage specific file changes, or 'git add .' to stage all tracked and untracked modifications in the current directory.",
        "source_url": "https://git-scm.com/docs/git-add"
    },
    {
        "id": 6,
        "category": "Git",
        "title": "Commit Changes (git commit)",
        "keyword": "commit",
        "question": "How do I commit staged changes?",
        "answer": "Run 'git commit -m \"Descriptive commit message\"' to record your staged snapshot into the repository commit history with an informative description.",
        "source_url": "https://git-scm.com/docs/git-commit"
    },
    {
        "id": 7,
        "category": "Git",
        "title": "Check Repository Status (git status)",
        "keyword": "status",
        "question": "How do I check the status of my working directory and staging area?",
        "answer": "Run 'git status' to inspect current branch status, view which files are staged for commit, modified but not staged, or untracked.",
        "source_url": "https://git-scm.com/docs/git-status"
    },
    {
        "id": 8,
        "category": "Git",
        "title": "View Commit History (git log)",
        "keyword": "log",
        "question": "How do I see past commits and history?",
        "answer": "Run 'git log' to see full commit details including author, timestamp, and commit hashes, or 'git log --oneline --graph' for a compact visual branch graph.",
        "source_url": "https://git-scm.com/docs/git-log"
    },
    {
        "id": 9,
        "category": "Git Branching",
        "title": "Create and Switch Branches (git branch & git switch)",
        "keyword": "branch",
        "question": "How do I create and switch between branches?",
        "answer": "Create a branch with 'git branch <branch-name>'. Switch to it with 'git switch <branch-name>' or create and switch simultaneously with 'git switch -c <branch-name>'.",
        "source_url": "https://git-scm.com/docs/git-branch"
    },
    {
        "id": 10,
        "category": "Git Branching",
        "title": "Merge Branches (git merge)",
        "keyword": "merge",
        "question": "How do I merge changes from one branch into another?",
        "answer": "First switch to your target branch ('git switch main'), then run 'git merge <feature-branch>' to combine the commits into your target branch.",
        "source_url": "https://git-scm.com/docs/git-merge"
    },
    {
        "id": 11,
        "category": "Troubleshooting",
        "title": "Resolve Merge Conflicts",
        "keyword": "conflict",
        "question": "How do I resolve a merge conflict in Git?",
        "answer": "Open conflicted files, inspect conflict markers (<<<<<<<, =======, >>>>>>>), choose the desired code, remove markers, stage resolved files with 'git add', and complete the commit.",
        "source_url": "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line"
    },
    {
        "id": 12,
        "category": "Troubleshooting",
        "title": "Undo Changes and Commits (git reset & git revert)",
        "keyword": "undo",
        "question": "How do I undo a commit or discard uncommitted changes?",
        "answer": "Use 'git revert <commit-hash>' to create a new commit that safely reverses changes without rewriting history. For local unpushed commits, use 'git reset --soft HEAD~1'. Discard unstaged file edits with 'git restore <file>'.",
        "source_url": "https://git-scm.com/docs/git-revert"
    },
    {
        "id": 13,
        "category": "Git",
        "title": "Stash Working Changes (git stash)",
        "keyword": "stash",
        "question": "How do I temporarily save uncommitted work without committing?",
        "answer": "Run 'git stash' to store modified tracked files onto a stack and revert to a clean working directory. Reapply your saved work anytime with 'git stash pop'.",
        "source_url": "https://git-scm.com/docs/git-stash"
    },
    {
        "id": 14,
        "category": "GitHub",
        "title": "Push Commits to Remote (git push)",
        "keyword": "push",
        "question": "How do I upload local commits to GitHub?",
        "answer": "Use 'git push -u origin <branch-name>' to upload local branch commits to GitHub and set upstream tracking for future straightforward 'git push' commands.",
        "source_url": "https://git-scm.com/docs/git-push"
    },
    {
        "id": 15,
        "category": "GitHub",
        "title": "Pull Changes from Remote (git pull)",
        "keyword": "pull",
        "question": "How do I fetch and integrate changes from GitHub?",
        "answer": "Run 'git pull origin <branch-name>' to retrieve new commits from GitHub and merge them directly into your current local branch.",
        "source_url": "https://git-scm.com/docs/git-pull"
    },
    {
        "id": 16,
        "category": "GitHub",
        "title": "Pull Requests and Code Review",
        "keyword": "pull-request",
        "question": "What is a Pull Request (PR) and how do I create one?",
        "answer": "A Pull Request lets you propose changes pushed to a GitHub branch so team members can review code differences, discuss changes, run automated tests, and merge into main.",
        "source_url": "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests"
    },
    {
        "id": 17,
        "category": "GitHub",
        "title": "SSH Key Authentication for GitHub",
        "keyword": "ssh",
        "question": "How do I configure SSH key authentication for GitHub?",
        "answer": "Generate an SSH key with 'ssh-keygen -t ed25519 -C \"email@example.com\"', start ssh-agent, add the key, and add the public key contents (.pub) into GitHub Settings -> SSH Keys.",
        "source_url": "https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent"
    },
    {
        "id": 18,
        "category": "GitHub Actions",
        "title": "GitHub Actions CI/CD",
        "keyword": "actions",
        "question": "What are GitHub Actions and how do I automate tests?",
        "answer": "GitHub Actions is an integrated CI/CD platform that executes automated workflows on GitHub events (such as push or pull_request) defined in .github/workflows/*.yml.",
        "source_url": "https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions"
    },
    {
        "id": 19,
        "category": "Git",
        "title": "Git Rebase (git rebase)",
        "keyword": "rebase",
        "question": "What is git rebase and when should I use it instead of merge?",
        "answer": "Rebasing transfers a sequence of commits to a new base commit, creating a clean linear project history. Never rebase commits that have already been pushed to a public shared branch.",
        "source_url": "https://git-scm.com/docs/git-rebase"
    },
    {
        "id": 20,
        "category": "Git",
        "title": "Release Tagging (git tag)",
        "keyword": "tag",
        "question": "How do I create release tags in Git?",
        "answer": "Create an annotated release tag using 'git tag -a v1.0.0 -m \"Release version 1.0.0\"' and publish it to the remote repository using 'git push origin --tags'.",
        "source_url": "https://git-scm.com/docs/git-tag"
    }
]
