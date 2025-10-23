# Contributing Guidelines

This document outlines the development workflow and standards for the `social-listening-toolbox` project. All contributors, including AI assistants, are expected to adhere to these guidelines.

## Core Workflow

The core development cycle for any change, no matter how small, is: **Modify -> Add -> Commit -> Push**.

### 1. Atomic Commits

Each commit should be "atomic" — it must represent a single, logical, and complete unit of work. The codebase should be in a stable, runnable state after each commit.

- **DO:** Commit a single feature, bug fix, or refactoring.
- **DO NOT:** Mix multiple unrelated changes (e.g., a feature and a bug fix) in one commit.

### 2. Commit Messages

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. The format is:

`type: subject`

- **Common types:**
    - `feat`: A new feature
    - `fix`: A bug fix
    - `refactor`: A code change that neither fixes a bug nor adds a feature
    - `docs`: Documentation only changes
    - `test`: Adding missing tests or correcting existing tests

### 3. Commit & Push Frequency

**A `push` must be performed immediately after every `commit`.**

This is a strict rule for this project to ensure:
- **Safety:** All committed work is immediately backed up to the remote repository.
- **Synchronization:** All collaborators (human or AI) are always working on the latest version of the code, preventing conflicts and misunderstandings.

### Workflow Summary

```bash
# 1. Make your changes and test them
# 2. Stage the changes for the commit
git add .

# 3. Commit the single, logical change with a clear message
git commit -m "type: subject"

# 4. Immediately push the commit to the remote repository
git push origin <branch-name>
```
