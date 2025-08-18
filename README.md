# Work-Life Balance Tool Setup Instructions

This guide walks you through setting up the work-life balance tool (`wallaby`) for analyzing calendar events and meeting themes.

## Prerequisites

- Python 3.12 or higher
- Git
- Access to Google Calendar and Google Drive APIs
- (Optional) Gemini API access for theme analysis

## Step 1: Set Up Python Virtual Environment

### Using venv (built-in Python)

```bash
# Navigate to your desired directory
cd /path/to/your/projects

# Clone the repository
git clone <repository-url>
cd work-life-balance

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Linux/macOS
# OR
venv\Scripts\activate     # On Windows
```

## Step 2: Install Poetry

Poetry is used for dependency management in this project.

### Install Poetry

```bash
# Using pip (if you prefer)
pip install poetry
```

## Step 3: Install Project Dependencies

```bash
# Ensure you're in the project directory and virtual environment is activated
cd work-life-balance

# Install all dependencies using poetry
poetry install

# This installs both production and development dependencies
# For production-only: poetry install --no-dev
```

## Step 4: Configuration

The application requires several environment variables and API credentials.

### 4.1 Google API Credentials

1. **Enable Google APIs**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Google Calendar API
     - Google Drive API

2. **Create OAuth 2.0 Credentials**:
   - Go to "Credentials" in the Google Cloud Console
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file (it will be named something like `client_secret_*.json`)
   - Save this file securely (e.g., `~/.config/wallaby/credentials.json`)

### 4.2 Gemini API Key (Optional)

For theme analysis functionality:

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Keep this key secure for the next step

### 4.3 Environment Variables

Create a `.env` file in your project directory or set environment variables:

```bash
# Required for basic functionality
export EMAIL="your-email@example.com"
export GOOGLE_CREDS_PATH="/path/to/your/credentials.json"

# Optional for theme analysis
export GEMINI_API_KEY="your-gemini-api-key-here"
```

#### Setting up .env file (recommended)

```bash
# Create .env file in project root
cat > .env << EOF
EMAIL=your-email@example.com
GOOGLE_CREDS_PATH=/home/yourusername/.config/wallaby/credentials.json
GEMINI_API_KEY=your-gemini-api-key-here
EOF

# Load environment variables
source .env
```

#### Configuration Details

- **EMAIL**: Your primary email address used in calendar events
- **GOOGLE_CREDS_PATH**: Absolute path to your Google OAuth credentials JSON file
- **GEMINI_API_KEY**: Your Gemini API key for AI-powered theme analysis

## Step 5: Verify Installation

### Test basic functionality

```bash
# Activate your virtual environment if not already active
source venv/bin/activate

# Test the installation
poetry run wlb --help

# List available calendars (this will trigger OAuth flow on first run)
poetry run wlb list-calendars

# List recent events
poetry run wlb list-events --months 1
```

### First-time OAuth Flow

When you run a command for the first time:

1. Your browser will open automatically
2. Sign in to your Google account
3. Grant permissions for Calendar and Drive access
4. The tool will save a token file (e.g., `credentials.json.token.json`)
5. Subsequent runs will use the saved token

## Step 6: Usage Examples

### Basic Commands

```bash
# List all calendars
poetry run wlb list-calendars

# Export events from last 3 months to CSV
poetry run wlb list-events --months 3 --output my-meetings.csv

# Download meeting notes for last 30 days
poetry run wlb download-notes --days 30 --output-dir ./notes

# Analyze themes in meeting notes (requires Gemini API)
poetry run wlb analyze-themes --input-dir ./notes --output themes-report.txt
```

### Development Commands

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Install development dependencies
poetry install
```

## Troubleshooting

### Common Issues

1. **"Missing environment variable $EMAIL"**
   - Ensure EMAIL environment variable is set
   - Check your .env file or export command

2. **"Missing credentials: /path/to/credentials.json"**
   - Verify GOOGLE_CREDS_PATH points to correct file
   - Ensure the credentials file exists and is readable

3. **"Missing environment variable $GEMINI_API_KEY"**
   - Only required for theme analysis
   - Get API key from [Google AI Studio](https://aistudio.google.com/)

4. **OAuth issues**
   - Delete the `.token.json` file to reset authentication
   - Ensure your Google Cloud project has the correct APIs enabled
   - Check that your OAuth consent screen is configured

5. **Poetry not found**
   - Ensure Poetry is in your PATH
   - Try restarting your terminal after installation

### Getting Help

- Check the application help: `poetry run wlb --help`
- Run with verbose output to see detailed error messages
- Ensure all environment variables are properly set

## Security Notes

- Keep your `credentials.json` file secure and never commit it to version control
- Store your Gemini API key securely
- The token files contain sensitive authentication data - keep them private
- Consider using a dedicated Google Cloud project for this application

## Project Structure

- `wallaby/` - Main application code
- `wallaby/cli/` - Command-line interface modules
- `tests/` - Test suite
- `pyproject.toml` - Poetry configuration and dependencies
- `.env` - Environment variables (create this file)
