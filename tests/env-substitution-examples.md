# Environment Variable Substitution Examples

The PRD Code Verifier supports both direct token embedding and environment variable substitution for maximum flexibility.

## Supported Patterns

The system supports these patterns for environment variable substitution:

1. `$VARIABLE_NAME` - Simple variable reference
2. `${VARIABLE_NAME}` - Braced variable reference
3. Direct token embedding - No substitution needed

## Example Configurations

### Method 1: Environment Variable Substitution

**In your project JSON file:**

```json
{
  "project_name": "My Project",
  "documentation_repo": "$DOCUMENTATION_REPO",
  "frontend_repo": "$FRONTEND_REPO",
  "backend_repo": "$BACKEND_REPO"
}
```

**In your .env file:**

```bash
DOCUMENTATION_REPO=https://$GITHUB_TOKEN@github.com/your-org/docs.git
FRONTEND_REPO=https://$GITHUB_TOKEN@github.com/your-org/frontend.git
BACKEND_REPO=https://$GITHUB_TOKEN@github.com/your-org/backend.git
GITHUB_TOKEN=ghp_your_actual_token_here
```

### Method 2: Direct Token Embedding

**In your project JSON file:**

```json
{
  "project_name": "My Project",
  "documentation_repo": "https://ghp_your_actual_token_here@github.com/your-org/docs.git",
  "frontend_repo": "https://ghp_your_actual_token_here@github.com/your-org/frontend.git",
  "backend_repo": "https://ghp_your_actual_token_here@github.com/your-org/backend.git"
}
```

### Method 3: Mixed Approach

**In your project JSON file:**

```json
{
  "project_name": "My Project",
  "documentation_repo": "$DOCUMENTATION_REPO",
  "frontend_repo": "https://$GITHUB_TOKEN@github.com/your-org/frontend.git",
  "backend_repo": "https://ghp_your_actual_token_here@github.com/your-org/backend.git"
}
```

**In your .env file:**

```bash
DOCUMENTATION_REPO=https://$GITHUB_TOKEN@github.com/your-org/docs.git
GITHUB_TOKEN=ghp_your_actual_token_here
```

## GitHub Actions Usage

### Using Secrets with Environment Variables

```yaml
- name: PRD Code Verification
  uses: gowrav-vishwakarma/prd-code-verifier@main
  with:
    project_file: "prd-verification.json"
    documentation_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/docs.git"
    frontend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/frontend.git"
    backend_repo: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/backend.git"
```

### Using Project File with Environment Variables

**In your project JSON:**

```json
{
  "project_name": "My Project",
  "documentation_repo": "$DOCUMENTATION_REPO",
  "frontend_repo": "$FRONTEND_REPO",
  "backend_repo": "$BACKEND_REPO"
}
```

**In your GitHub Actions workflow:**

```yaml
- name: PRD Code Verification
  uses: gowrav-vishwakarma/prd-code-verifier@main
  with:
    project_file: "prd-verification.json"
  env:
    DOCUMENTATION_REPO: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/docs.git"
    FRONTEND_REPO: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/frontend.git"
    BACKEND_REPO: "https://${{ secrets.GITHUB_TOKEN }}@github.com/your-org/backend.git"
```

## Self-Test Configuration

Our self-test uses environment variable substitution for maximum flexibility:

**tests/self-test-project.json:**

```json
{
  "project_name": "PRD Code Verifier Self-Test",
  "documentation_repo": "$DOCUMENTATION_REPO",
  "frontend_repo": "$FRONTEND_REPO",
  "backend_repo": "$BACKEND_REPO"
}
```

**tests/test.env:**

```bash
DOCUMENTATION_REPO=https://$GITHUB_TOKEN@github.com/gowrav-vishwakarma/prd-code-verifier.git
FRONTEND_REPO=https://$GITHUB_TOKEN@github.com/gowrav-vishwakarma/prd-code-verifier.git
BACKEND_REPO=https://$GITHUB_TOKEN@github.com/gowrav-vishwakarma/prd-code-verifier.git
GITHUB_TOKEN=your_github_token_here
```

## Benefits of Each Method

### Environment Variable Substitution

- ✅ Keeps tokens out of project files
- ✅ Easy to switch between environments
- ✅ Better security (tokens in .env files)
- ✅ Supports complex substitution patterns

### Direct Token Embedding

- ✅ Simple and straightforward
- ✅ No additional configuration needed
- ✅ Works well for public repositories
- ✅ Easy to understand and debug

### Mixed Approach

- ✅ Maximum flexibility
- ✅ Can use different methods for different repos
- ✅ Gradual migration from one method to another

## Implementation Details

The environment variable substitution is handled by `utils/env_substitution.py`:

- Supports `$VARIABLE_NAME` and `${VARIABLE_NAME}` patterns
- Recursively processes strings, dictionaries, and lists
- Falls back to original pattern if variable not found
- Used in `cr_config.py` for configuration processing
- Used in `utils/git_operations.py` for repository URLs

This ensures maximum compatibility and flexibility for all users!
