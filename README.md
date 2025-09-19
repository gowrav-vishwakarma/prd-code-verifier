# PRD Code Verifier

A comprehensive web application that verifies code implementations against documentation using AI. This tool helps ensure that your code matches your project requirements and documentation specifications.

## 🚀 Features

### Core Functionality

- **Project Management**: Create, save, and load verification projects as JSON files
- **Multi-AI Provider Support**: Works with OpenAI, Google Gemini, Ollama, and LM Studio
- **Flexible Verification**: Configure multiple verification sections with different documentation and code files
- **Flexible Prompt Management**: Choose to use global, override, or append prompts and instructions per verification
- **Report Generation**: Generate detailed markdown reports for each verification
- **Hierarchical Organization**: Reports are organized in ProjectName/AIProvider/Model folder structure
- **Multi-Provider Comparison**: Easy comparison of results across different AI providers and models
- **Debug Mode**: Save complete prompts sent to AI when DEBUG is enabled

### Web Interface

- **Modern UI**: Clean, responsive web interface built with Bootstrap
- **File Path Management**: Textarea-based file path input for absolute paths
- **Verification Selection**: Checkbox-based selection system for running specific verifications
- **Selection Management**: Select All/Deselect All buttons for easy bulk selection
- **Real-time Configuration**: Dynamic AI provider configuration with environment defaults
- **Batch Processing**: Run all verifications or selected ones with visual feedback
- **Download Reports**: Direct download of generated reports
- **Real-time Markdown Preview**: Live markdown rendering during AI streaming with toggle between raw text and preview modes
- **Configurable Streaming**: Environment variable to enable/disable streaming for performance optimization

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

# Streaming Configuration
ENABLE_STREAMING=True  # Set to False to disable real-time streaming (faster for small responses)
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

**LM Studio Streaming Setup:**

1. **Start the Inference Server**:

   - Open LM Studio
   - Navigate to the "Server" tab
   - Click "Start Server"
   - Ensure the server is running on `http://localhost:1234`

2. **Verify Model Compatibility**:

   - Not all models support streaming
   - Test with models known to support streaming (e.g., Mistral, Llama 2)
   - Check model documentation for streaming support

3. **System Requirements**:

   - **macOS**: Apple Silicon (M1/M2/M3/M4), macOS 13.4+, 16GB+ RAM
   - **Windows**: CPU with AVX2 support, 16GB+ RAM, GPU with 4GB+ VRAM
   - **Linux**: Ubuntu 20.04+, x64 architecture, 16GB+ RAM

4. **Troubleshooting Streaming Issues**:

   - Ensure LM Studio is updated to the latest version
   - Check that the inference server is running
   - Verify the model supports streaming
   - Check LM Studio logs for error messages
   - Try different models if streaming fails
   - The application will automatically fallback to non-streaming if streaming fails

5. **Configuration**:
   ```env
   DEFAULT_AI_PROVIDER=lm_studio
   LM_STUDIO_BASE_URL=http://localhost:1234/v1
   LM_STUDIO_MODEL=your-model-name
   ```

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

The application uses a **root path + relative path** system for maximum portability:

1. **Set root paths** in the project configuration:

   - Documentation Root Path: Base directory for all documentation files
   - Frontend Project Path: Base directory for all frontend code files
   - Backend Project Path: Base directory for all backend code files

2. **Enter relative file paths** in the verification sections:

   - One file path per line in each textarea
   - Paths are relative to their respective root directories
   - Click "File Path Help" for guidance on getting relative paths

3. **Supported file types**:
   - Documentation: `.md`, `.txt`, `.pdf`
   - Frontend: `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.html`, `.css`, `.scss`
   - Backend: `.py`, `.java`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.php`, `.rb`

**Example setup:**

- Documentation Root Path: `/home/user/project/docs`
- Frontend Project Path: `/home/user/project/frontend`
- Backend Project Path: `/home/user/project/backend`

**Example relative paths:**

```
docs/README.md
docs/api-spec.md
src/components/Button.jsx
api/routes/users.py
```

### 3. Prompt Management

The application provides flexible prompt management with three modes for both system prompts and instructions:

#### **System Prompt Modes:**

- **Use Global**: Uses only the global system prompt (default)
- **Override**: Uses only the local verification system prompt
- **Append**: Combines global + local system prompts (global first, then local)

#### **Instructions Modes:**

- **Use Global**: Uses only the global instructions (default)
- **Override**: Uses only the local verification instructions
- **Append**: Combines global + local instructions (global first, then local)

#### **How It Works:**

1. **Global Prompts**: Set once in the project configuration
2. **Local Prompts**: Set per verification section
3. **Mode Selection**: Choose how to combine them using radio buttons
4. **Smart Combination**: When appending, prompts are separated by double newlines for clarity

#### **Example Scenarios:**

- **Use Global**: Standard verification using project-wide prompts
- **Override**: Special verification requiring completely different prompts
- **Append**: Add verification-specific context to global prompts

### 4. Running Verifications

1. **Save your project** first (optional but recommended)
2. **Select verifications to run**:
   - Check the boxes next to verification sections you want to run
   - Use "Select All" to check all verifications
   - Use "Deselect All" to uncheck all verifications
   - The counter shows "X of Y selected"
3. **Run verifications**:
   - Click "Run All Verifications" to process all sections
   - Click "Run Selected" to run only checked verifications
4. **Monitor progress** with the loading indicator and real-time streaming
5. **View AI responses** in real-time with markdown preview
6. **Download reports** from the results section

### 5. Verification Selection Features

The application provides flexible verification selection:

- **Individual Selection**: Check/uncheck specific verification sections
- **Bulk Selection**: Use "Select All" or "Deselect All" buttons
- **Visual Feedback**: Real-time counter showing "X of Y selected"
- **Smart Defaults**: When loading a project, all verifications are selected by default
- **Validation**: System prevents running without selecting any verifications
- **Error Handling**: Clear notifications for selection issues

### 6. Real-time Markdown Preview

The application features a powerful real-time markdown preview system for viewing AI responses:

#### **Features:**

- **Dual View Modes**: Toggle between raw text and rendered markdown preview
- **Auto-Detection**: Automatically switches to preview mode when markdown content is detected
- **Real-time Rendering**: Updates markdown preview as AI streams content
- **Manual Control**: Override auto-detection with manual toggle buttons
- **Responsive Design**: Optimized for both desktop and mobile viewing

#### **How to Use:**

1. **Start a verification** - The streaming area appears automatically
2. **View modes**:
   - **Raw**: Shows the original markdown text (default)
   - **Preview**: Shows rendered markdown with proper formatting
3. **Auto-switching**: The system automatically switches to preview mode when it detects markdown formatting
4. **Manual override**: Use the toggle buttons to switch between modes at any time
5. **Real-time updates**: Both views update in real-time as the AI streams content

#### **Markdown Features Supported:**

- Headers (H1-H6)
- Bold and italic text
- Code blocks and inline code
- Lists (ordered and unordered)
- Blockquotes
- Tables
- Links
- Horizontal rules

#### **Benefits:**

- **Better Readability**: See formatted content instead of raw markdown
- **Real-time Feedback**: Monitor AI responses as they're generated
- **Flexible Viewing**: Choose the view that works best for your needs
- **Professional Output**: Preview how the final report will look

### 7. Understanding Reports

Each verification generates:

- **`{verification_name}_report.md`**: AI analysis of code vs documentation
- **`{verification_name}_prompt.md`**: Complete prompt sent to AI (only when DEBUG=True)

Reports are organized in a hierarchical folder structure for easy comparison:

```
output/
└── My Project/
    ├── openai/
    │   └── gpt-3.5-turbo/
    │       ├── API Verification_report.md
    │       ├── API Verification_prompt.md
    │       ├── Database Schema_report.md
    │       └── Database Schema_prompt.md
    ├── gemini/
    │   └── gemini-pro/
    │       ├── API Verification_report.md
    │       └── API Verification_prompt.md
    └── ollama/
        └── llama2/
            ├── API Verification_report.md
            └── API Verification_prompt.md
```

This structure allows you to:

- **Compare results** across different AI providers
- **Test different models** from the same provider
- **Organize reports** by project, provider, and model
- **Easily identify** which AI configuration generated each report

**Download URLs:**

- Reports are downloaded using the hierarchical path: `/api/reports/{project_name}/{provider_name}/{model_name}/{filename}`
- The system automatically constructs the correct download URL based on the AI provider and model used
- Legacy download URLs are still supported for backward compatibility

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
- `GET /api/reports/{project_name}/{provider_name}/{model_name}/{filename}` - Download verification report (hierarchical path)
- `GET /api/reports/{project_name}/{filename}` - Download verification report (legacy endpoint for backward compatibility)

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

### Performance Optimization

#### Streaming Configuration

The application supports configurable streaming for optimal performance:

- **`ENABLE_STREAMING=True`** (default): Shows real-time streaming with markdown preview
  - Best for: Large responses, interactive monitoring, markdown content
  - Features: Live updates, markdown preview, toggle between raw/preview modes
- **`ENABLE_STREAMING=False`**: Uses faster non-streaming mode
  - Best for: Small responses, batch processing, performance-critical scenarios
  - Features: Simple progress indicator, faster processing, reduced UI complexity

#### When to Disable Streaming

Consider setting `ENABLE_STREAMING=False` when:

- Processing many small verifications
- Running batch operations
- Using slower AI providers
- Prioritizing speed over real-time feedback
- Working with non-markdown responses

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
