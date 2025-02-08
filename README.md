# AI API Utility

An intelligent API interaction tool that simplifies API integration and testing through AI-powered request generation, secure credential management, and robust validation.

## Features

- 🤖 AI-Powered API Selection
  - Intelligent API recommendation based on user goals
  - Automatic request generation and parameter suggestions
  - Smart error analysis and resolution

- 🔐 Secure Credential Management
  - Local secure storage for API keys
  - Platform-specific credential handling
  - Automatic credential validation

- ✅ Advanced Request Validation
  - Pre-request parameter validation
  - URL and authentication verification
  - Pattern-based input validation
  - Comprehensive error handling

- 🔄 Robust Error Handling
  - Intelligent error analysis
  - Automatic retry with exponential backoff
  - Timeout management
  - Suggested fixes for common issues

## Installation

```bash
# Clone the repository
git clone https://github.com/gjohnhazel/ai-api-utility.git
cd ai-api-utility

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key and other configurations
```

## Usage

```bash
# Run the main application
python api_generator.py

# Follow the interactive prompts to:
# 1. Describe your API integration goal
# 2. Select the recommended API
# 3. Provide or use stored credentials
# 4. Configure request parameters
# 5. Execute and manage API requests
```

## Project Structure

```
ai-api-utility/
├── api_generator.py     # Main application logic
├── credential_manager.py # Secure credential handling
├── validator.py         # Request validation
├── .env                # Environment configuration
└── requirements.txt    # Project dependencies
```

## Development Roadmap

### Phase 1 (COMPLETED):
- Core Infrastructure & Security
  - Credential Management with secure local storage
  - Basic error handling framework
  - Retry logic with exponential backoff
  - Timeout handling

### Phase 2 (In Progress):
- Input & Validation Improvements
  1. Add input validation framework
  2. Implement "help" command system
  3. Add default value handling
  4. Add request validation (pre-request parameter validation)
  5. URL validation enhancement
  6. Authentication verification

### Phase 3:
- History & Session Management
  1. Create history storage system
  2. Add request saving/loading
  3. Implement replay functionality
  4. Add rate limit tracking
  5. Implement token refresh handling
  6. Add basic pagination support

### Phase 4:
- Documentation & Preview
  1. Add documentation fetching system
  2. Implement quick reference system
  3. Add example integration
  4. Add curl command generation

### Phase 5:
- Flutter Application Development (my goal all along was to have a mobile app)
  1. Initial Flutter project setup
  2. Core functionality migration
  3. Cross-platform UI development
  4. Local storage integration
  5. Authentication system implementation
  6. Request builder interface
  7. Response viewer development
  8. Testing and optimization

### Phase 6:
- Enhanced Flutter Application
  1. Advanced request builder
    - Multi-tab request management
    - Request templates
    - Bulk request handling
  2. Response analysis tools
    - Response formatting
    - JSON/XML viewers
    - Schema validation
  3. Collection management
    - Request organization
    - Environment variables
    - Team sharing capabilities
  4. AI-powered features
    - Request suggestions
    - Parameter optimization
    - Error resolution
    - Documentation generation
  5. Advanced testing capabilities
    - Automated testing
    - Performance monitoring
    - Mock server integration
  6. Collaboration features
    - Team workspaces
    - Request sharing
    - Comment system
    - Version control

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the AI capabilities
- The open-source community for various dependencies and inspiration 
- Claude & Cursor for writing the code 😀
- Pythonista for being able to prototype on my iPhone