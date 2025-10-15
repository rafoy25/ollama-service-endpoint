# Remove Large Models from Git History

## Problem
You committed and pushed the `models/` folder (~1.2GB) to Git.

## Solution: Remove from Git, Keep Locally

### Step 1: Add to .gitignore (Already Done ✅)
```bash
# .gitignore already contains:
models/
```

### Step 2: Remove from Git Tracking (Keep Local Files)
```bash
# This removes models from Git but KEEPS your local files
git rm -r --cached models/

# Verify models/ is gone from Git (but still on disk)
git status
# Should show: deleted: models/...
```

### Step 3: Commit the Removal
```bash
git add .gitignore
git commit -m "Remove large model files from Git tracking

- Added models/ to .gitignore
- Models will be generated during deployment via convert_model_simple.py
- Reduces repo size by ~1.2GB"
```

### Step 4: Push Changes
```bash
git push origin main
```

---

## ⚠️ WARNING: Git History Still Contains Models

**The above only removes from CURRENT commit.**

To completely remove from Git history (optional, advanced):

### Option A: Use BFG Repo-Cleaner (Recommended)
```bash
# Install BFG
# Windows: choco install bfg
# Mac: brew install bfg
# Linux: download from https://rtyley.github.io/bfg-repo-cleaner/

# Backup your repo first!
cd ..
cp -r work work-backup

# Remove all files in models/ from entire history
cd work
bfg --delete-folders models

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (rewrites history - WARNING!)
git push origin --force --all
```

### Option B: Use git filter-branch (Manual)
```bash
# Backup first!
git clone --mirror <your-repo-url> repo-backup.git

# Remove models/ from all commits
git filter-branch --force --index-filter \
  "git rm -r --cached --ignore-unmatch models/" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
git push origin --force --tags
```

---

## 🎯 Recommended Approach for Most Users

**If repo is private or small team:**
1. Just use Step 1-4 above (remove from tracking)
2. Don't worry about Git history
3. Models will be regenerated on deployment

**If repo is public or history matters:**
1. Use BFG Repo-Cleaner (Option A)
2. Completely removes models from history
3. Reduces repo size permanently

---

## After Removal: Deployment Instructions

Update your README to include:

```markdown
## Setup on New Server

1. Clone repo (models NOT included)
git clone <repo-url>
cd <repo>

2. Run deployment setup (downloads and converts models)
bash deploy_setup.sh

3. Start services
docker-compose up -d
```

---

## Verify Models Are Ignored

```bash
# Check what Git is tracking
git ls-files | grep models
# Should return NOTHING

# Check local files still exist
ls -la models/
# Should show your models (on disk, not in Git)
```

---

## Future: Prevent Accidental Commits

Add pre-commit hook (optional):

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached --name-only | grep -q "^models/"; then
    echo "ERROR: Attempting to commit files in models/"
    echo "Models should not be in Git. Run:"
    echo "  git rm -r --cached models/"
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```
