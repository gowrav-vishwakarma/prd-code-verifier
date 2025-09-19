# PRD Code Verifier

A comprehensive web application that verifies code implementations against documentation using AI. This tool helps ensure that your code matches your project requirements and documentation specifications.

## 🚀 Features

### Core Functionality

- **Project Management**: Create, save, and load verification projects as JSON files
- **Multi-AI Provider Support**: Works with OpenAI, Google Gemini, Ollama, and LM Studio
- **Flexible Verification**: Configure multiple verification sections with different documentation and code files
- **Custom Prompts**: Override global system prompts and instructions per verification
- **Report Generation**: Generate detailed markdown reports for each verification
- **Project-Specific Organization**: Reports are organized in project-specific folders
- **Debug Mode**: Save complete prompts sent to AI when DEBUG is enabled

### Web Interface

- **Modern UI**: Clean, responsive web interface built with Bootstrap
- **File Path Management**: Textarea-based file path input for absolute paths
- **Verification Selection**: Checkbox-based selection system for running specific verifications
- **Selection Management**: Select All/Deselect All buttons for easy bulk selection
- **Real-time Configuration**: Dynamic AI provider configuration with environment defaults
- **Batch Processing**: Run all verifications or selected ones with visual feedback
- **Download Reports**: Direct download of generated reports

## 📋 Requirements

- Python 3.9+
- [UV](https://github.com/astral-sh/uv) package manager
- One of the supported AI providers (see Configuration section)

## 🛠️ Installation

1. **Install UV** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup**:

   ```bash
   git clone <repository-url>
   cd prd-code-verifier
   uv sync
   ```

3. **Configure environment**:

   ```bash
   cp env.example .env
   # Edit .env with your AI provider credentials
   ```

4. **Start the application**:

   ```bash
   # Easy way
   ./start.sh

   # Or manually
   uv run main.py
   ```

5. **Access the web interface**:
   Open your browser to `http://localhost:8000`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# AI Provider Configuration
DEFAULT_AI_PROVIDER=lm_studio  # openai, gemini, ollama, lm_studio

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro

# Ollama Configuration (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# LM Studio Configuration (Local)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=qwen/qwen3-30b-a3b-2507

# Application Configuration
DEBUG=True  # Set to False to disable prompt saving
HOST=0.0.0.0
PORT=8000
```

### AI Provider Setup

#### OpenAI

- Get API key from [OpenAI Platform](https://platform.openai.com/)
- Set `DEFAULT_AI_PROVIDER=openai`
- Add your API key to `OPENAI_API_KEY`

#### Google Gemini

- Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Set `DEFAULT_AI_PROVIDER=gemini`
- Add your API key to `GEMINI_API_KEY`

#### Ollama (Local)

- Install [Ollama](https://ollama.ai/)
- Pull a model: `ollama pull llama2`
- Set `DEFAULT_AI_PROVIDER=ollama`
- No API key required

#### LM Studio (Local)

- Install [LM Studio](https://lmstudio.ai/)
- Load a model and start the local server
- Set `DEFAULT_AI_PROVIDER=lm_studio`
- No API key required

## 📖 Usage Guide

### 1. Creating a Project

1. **Open the web interface** at `http://localhost:8000`
2. **Configure project settings**:

   - Project Name: Choose a descriptive name
   - Output Folder: Where reports will be saved
   - Global System Prompt: Default prompt for all verifications
   - Global Instructions: Default instructions for all verifications

3. **Add verification sections**:

   - Click "Add Section" to create verification sections
   - Each section can have:
     - Documentation files (markdown, text, PDF)
     - Frontend code files (JS, TS, Vue, React, etc.)
     - Backend code files (Python, Java, C++, etc.)
     - Custom system prompts and instructions (optional)

4. **Configure AI settings**:
   - Select AI provider
   - Set model and parameters
   - The interface will auto-populate from your `.env` file

### 2. File Path Management

The application uses textarea-based file path input:

1. **Enter absolute file paths** directly in the textareas
2. **One file path per line** in each textarea
3. **Click the help button (?) ** for guidance on getting file paths
4. **Supported file types**:
   - Documentation: `.md`, `.txt`, `.pdf`
   - Frontend: `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.html`, `.css`, `.scss`
   - Backend: `.py`, `.java`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.php`, `.rb`

Example file paths:

```
/home/user/project/docs/README.md
/home/user/project/src/components/Button.jsx
/home/user/project/api/routes/users.py
```

### 3. Running Verifications

1. **Save your project** first (optional but recommended)
2. **Select verifications to run**:
   - Check the boxes next to verification sections you want to run
   - Use "Select All" to check all verifications
   - Use "Deselect All" to uncheck all verifications
   - The counter shows "X of Y selected"
3. **Run verifications**:
   - Click "Run All Verifications" to process all sections
   - Click "Run Selected" to run only checked verifications
4. **Monitor progress** with the loading indicator
5. **Download reports** from the results section

### 4. Verification Selection Features

The application provides flexible verification selection:

- **Individual Selection**: Check/uncheck specific verification sections
- **Bulk Selection**: Use "Select All" or "Deselect All" buttons
- **Visual Feedback**: Real-time counter showing "X of Y selected"
- **Smart Defaults**: When loading a project, all verifications are selected by default
- **Validation**: System prevents running without selecting any verifications
- **Error Handling**: Clear notifications for selection issues

### 5. Understanding Reports

Each verification generates:

- **`{verification_name}_report.md`**: AI analysis of code vs documentation
- **`{verification_name}_prompt.md`**: Complete prompt sent to AI (only when DEBUG=True)

Reports are organized in project-specific folders:

```
output/
└── My Project/
    ├── API Verification_report.md
    ├── API Verification_prompt.md
    ├── Database Schema_report.md
    └── Database Schema_prompt.md
```

## 🏗️ Project Structure

```
prd-code-verifier/
├── main.py                 # Application entry point
├── web_app.py             # FastAPI web application
├── models.py              # Pydantic data models
├── ai_providers.py        # AI provider implementations
├── verification_engine.py # Core verification logic
├── config.py              # Configuration management
├── templates/
│   └── index.html         # Web interface
├── static/                # Static files (CSS, JS)
├── projects/              # Saved project files
├── output/                # Generated reports
├── env.example            # Environment configuration template
├── example_project.json   # Example project file
├── start.sh               # Startup script
└── README.md              # This file
```

## 🔌 API Endpoints

### Web Interface

- `GET /` - Main application page

### Configuration

- `GET /api/providers` - List available AI providers
- `GET /api/config/default-ai` - Get default AI configuration

### Project Management

- `POST /api/projects/save` - Save project configuration
- `GET /api/projects` - List saved projects
- `POST /api/projects/load` - Load project from file

### Verification

- `POST /api/verification/run` - Run verification process
- `GET /api/reports/{project_name}/{filename}` - Download verification report

## 🔧 Development

### Setup Development Environment

```bash
uv sync --dev
```

### Run Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

### Linting

```bash
uv run flake8
```

### Project Dependencies

The project uses these main dependencies:

- **FastAPI**: Web framework
- **Pydantic**: Data validation and settings
- **Uvicorn**: ASGI server
- **aiofiles**: Async file operations
- **OpenAI**: OpenAI API client
- **google-generativeai**: Google Gemini API client
- **ollama**: Ollama client
- **python-dotenv**: Environment variable management

## 📝 Example Project

See `example_project.json` for a sample project configuration:

```json
{
  "project_name": "Example PRD Verification",
  "output_folder": "./reports",
  "global_system_prompt": "You are an expert software engineer...",
  "global_instructions": "Please provide a detailed analysis...",
  "verification_sections": [
    {
      "name": "API Endpoints Verification",
      "documentation_files": [],
      "frontend_code_files": [],
      "backend_code_files": [],
      "override_global_system_prompt": false,
      "override_global_instructions": false
    }
  ]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"Error saving project"**

   - Ensure all required fields are filled
   - Check that verification sections have names

2. **"Report not found"**

   - Verify the project name in the download URL
   - Check that the verification completed successfully

3. **"AI API error"**

   - Verify your API key is correct
   - Check that the AI service is running (for local providers)
   - Ensure you have sufficient API credits

4. **File paths not working**

   - Use absolute paths (starting with `/`)
   - Ensure files exist and are readable
   - Check file permissions

5. **"Please select at least one verification to run"**

   - Check the boxes next to verification sections you want to run
   - Use "Select All" to quickly select all verifications
   - Ensure verification sections have names before running

6. **"Please ensure selected verifications have names"**
   - Make sure all selected verification sections have names filled in
   - The verification name field is required for each section

### Debug Mode

Set `DEBUG=True` in your `.env` file to:

- Save complete prompts sent to AI
- Enable detailed error logging
- Help troubleshoot verification issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the example project
3. Check your environment configuration
4. Open an issue on GitHub

---

**Happy Verifying!** 🎉
