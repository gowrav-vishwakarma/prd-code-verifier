# PRD Code Verifier

A web application that verifies code against documentation using AI. This tool helps ensure that your implementation matches your project requirements and documentation.

## Features

- **Project Management**: Create, save, and load verification projects
- **Multiple AI Providers**: Support for OpenAI, Google Gemini, Ollama, and LM Studio
- **Flexible Verification**: Configure multiple verification sections with different documentation and code files
- **Custom Prompts**: Override global system prompts and instructions per verification
- **Report Generation**: Generate detailed markdown reports for each verification
- **Web Interface**: Easy-to-use web interface for managing verifications

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

1. Install UV if you haven't already:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository and install dependencies:

   ```bash
   git clone <repository-url>
   cd prd-code-verifier
   uv sync
   ```

3. Copy the environment configuration:

   ```bash
   cp env.example .env
   ```

4. Edit `.env` file with your AI provider credentials:

   ```bash
   # For OpenAI
   DEFAULT_AI_PROVIDER=openai
   OPENAI_API_KEY=your_api_key_here

   # For Google Gemini
   # DEFAULT_AI_PROVIDER=gemini
   # GEMINI_API_KEY=your_api_key_here

   # For Ollama (local)
   # DEFAULT_AI_PROVIDER=ollama
   # OLLAMA_BASE_URL=http://localhost:11434

   # For LM Studio (local)
   # DEFAULT_AI_PROVIDER=lm_studio
   # LM_STUDIO_BASE_URL=http://localhost:1234/v1
   ```

## Usage

1. Start the application:

   ```bash
   uv run main.py
   ```

2. Open your browser to `http://localhost:8000`

3. Create a new project:

   - Enter project name and output folder
   - Configure global system prompt and instructions
   - Add verification sections with documentation and code files
   - Save the project

4. Run verifications:
   - Configure AI provider settings
   - Click "Run All Verifications" or "Run Selected"
   - Download generated reports

## Project Structure

```
prd-code-verifier/
├── main.py                 # Application entry point
├── web_app.py             # FastAPI web application
├── models.py              # Pydantic models
├── ai_providers.py        # AI provider implementations
├── verification_engine.py # Core verification logic
├── config.py              # Configuration management
├── templates/             # HTML templates
│   └── index.html
├── static/                # Static files (CSS, JS)
├── projects/              # Saved project files
└── reports/               # Generated verification reports
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/providers` - List available AI providers
- `POST /api/projects/save` - Save project configuration
- `GET /api/projects` - List saved projects
- `POST /api/projects/load` - Load project from file
- `POST /api/verification/run` - Run verification process
- `GET /api/reports/{filename}` - Download verification report

## Configuration

The application supports multiple AI providers:

### OpenAI

- Requires API key
- Default model: gpt-3.5-turbo
- Base URL: https://api.openai.com/v1

### Google Gemini

- Requires API key
- Default model: gemini-pro
- Base URL: https://generativelanguage.googleapis.com

### Ollama (Local)

- No API key required
- Default model: llama2
- Base URL: http://localhost:11434

### LM Studio (Local)

- No API key required
- Default model: local-model
- Base URL: http://localhost:1234/v1

## Development

1. Install development dependencies:

   ```bash
   uv sync --dev
   ```

2. Run tests:

   ```bash
   uv run pytest
   ```

3. Format code:

   ```bash
   uv run black .
   uv run isort .
   ```

4. Lint code:
   ```bash
   uv run flake8
   ```

## License

This project is licensed under the MIT License.
