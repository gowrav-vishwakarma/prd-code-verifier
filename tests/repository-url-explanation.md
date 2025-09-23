# Repository URL Configuration Explained

## 🎯 How Repository URLs Work

The PRD Code Verifier uses a **two-layer configuration system**:

1. **GitHub Action Inputs** → Repository URLs (where to clone from)
2. **Project File** → Verification sections and prompts (what to verify)

## 📋 Configuration Layers

### Layer 1: GitHub Action Inputs (Repository URLs)

```yaml
- name: PRD Code Verification
  uses: gowrav-vishwakarma/prd-code-verifier@main
  with:
    project_file: "prd-verification.json"
    documentation_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/org/docs.git"
    frontend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/org/frontend.git"
    backend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/org/backend.git"
```

### Layer 2: Project File (Verification Configuration)

```json
{
  "project_name": "My Project",
  "output_folder": "./reports",
  "global_system_prompt": "You are an expert...",
  "verification_sections": [
    {
      "name": "API Verification",
      "documentation_files": ["README.md", "api-spec.md"],
      "frontend_code_files": ["src/api/client.js"],
      "backend_code_files": ["api/routes/users.py"]
    }
  ]
}
```

## 🔄 How It Works

1. **GitHub Action** clones repositories using the input URLs
2. **Project File** specifies which files to analyze within those cloned repositories
3. **File paths** in the project file are relative to the cloned repository roots

## ❌ Common Misconception

**WRONG**: Repository URLs in project file are used

```json
{
  "documentation_repo": "$DOCUMENTATION_REPO", // ❌ IGNORED
  "frontend_repo": "$FRONTEND_REPO", // ❌ IGNORED
  "backend_repo": "$BACKEND_REPO" // ❌ IGNORED
}
```

**CORRECT**: Repository URLs only in GitHub Action inputs

```yaml
with:
  documentation_repo: "https://token@github.com/org/docs.git" # ✅ USED
  frontend_repo: "https://token@github.com/org/frontend.git" # ✅ USED
  backend_repo: "https://token@github.com/org/backend.git" # ✅ USED
```

## 🎯 Why This Design?

1. **Security**: Tokens stay in GitHub secrets, not in project files
2. **Flexibility**: Same project file can work with different repositories
3. **Clarity**: Clear separation between "where to get code" vs "what to verify"
4. **Reusability**: Project files can be shared without exposing repository URLs

## 📝 Self-Test Example

Our self-test correctly uses this pattern:

**GitHub Action** (`.github/workflows/self-test.yml`):

```yaml
with:
  project_file: "tests/self-test-project.json"
  documentation_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/gowrav-vishwakarma/prd-code-verifier.git"
  frontend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/gowrav-vishwakarma/prd-code-verifier.git"
  backend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/gowrav-vishwakarma/prd-code-verifier.git"
```

**Project File** (`tests/self-test-project.json`):

```json
{
  "project_name": "PRD Code Verifier Self-Test",
  "output_folder": "./reports",
  "verification_sections": [
    {
      "name": "Web Application Verification",
      "documentation_files": ["README.md"],
      "frontend_code_files": ["templates/index.html"],
      "backend_code_files": ["verification_engine.py"]
    }
  ]
}
```

## ✅ Summary

- **Repository URLs**: Only in GitHub Action inputs
- **File paths**: Only in project file (relative to cloned repos)
- **No duplication**: Each piece of information has one place
- **Clear separation**: "Where to get code" vs "What to verify"
