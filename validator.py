# validator.py

from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse
import re
import json
from dotenv import load_dotenv
import os

# Add near the top of your file, after imports
load_dotenv()  # This loads the variables from .env into os.environ

api_key = os.getenv('OPENAI_API_KEY')

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.details = details or {}

class RequestValidator:
    """Handles validation of API requests and parameters"""
    
    def __init__(self):
        self.help_commands = {
            "help": self._general_help,
            "auth": self._auth_help,
            "params": self._params_help,
            "examples": self._examples_help,
            "validation": self._validation_help
        }
        
        # Common parameter patterns
        self.patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "api_key": r'^[A-Za-z0-9_\-]{20,}$',
            "url": r'^https?:\/\/.+',
        }
    
    def get_help(self, command: Optional[str] = None) -> str:
        """Get help information for a specific command or general help"""
        if not command:
            return self._general_help()
        
        help_func = self.help_commands.get(command.lower())
        if help_func:
            return help_func()
        return f"Unknown help command: '{command}'. Try 'help' for available commands."
    
    def _general_help(self) -> str:
        return """
Available Commands:
- help: Show this general help message
- auth: Get help with authentication
- params: Learn about parameter validation
- examples: See example API requests
- validation: Understanding validation rules

Use 'help <command>' for more specific information.
"""

    def _auth_help(self) -> str:
        return """
Authentication Help:
- API keys should be kept secure and never shared
- Most APIs require keys in headers or query parameters
- Keys should be at least 20 characters
- Store keys securely using credential_manager
"""

    def _params_help(self) -> str:
        return """
Parameter Validation:
- Required parameters must not be empty
- Dates should be in YYYY-MM-DD format
- Email addresses must be properly formatted
- URLs must include http:// or https://
"""

    def _examples_help(self) -> str:
        return """
Example Requests:
1. Weather API:
   - Required: location, units
   - Optional: forecast_days, details

2. Search API:
   - Required: query
   - Optional: limit, offset, sort
"""

    def _validation_help(self) -> str:
        return """
Validation Rules:
- URLs must be properly formatted and accessible
- API keys must meet minimum length requirements
- Date formats must match API specifications
- Numeric ranges must be within allowed limits
"""

    def validate_request(self, request_spec: Dict[str, Any]) -> None:
        """
        Validate the complete request specification
        Raises ValidationError if validation fails
        """
        # Validate basic structure
        required_fields = ['url', 'method']
        missing_fields = [field for field in required_fields if field not in request_spec]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate URL
        self.validate_url(request_spec['url'])
        
        # Validate HTTP method
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if request_spec['method'].upper() not in valid_methods:
            raise ValidationError(f"Invalid HTTP method: {request_spec['method']}")
        
        # Validate headers
        if 'headers' in request_spec:
            self.validate_headers(request_spec['headers'])
        
        # Validate parameters
        if 'params' in request_spec:
            self.validate_parameters(request_spec['params'])
        
        # Validate body for appropriate methods
        if request_spec['method'].upper() in ['POST', 'PUT', 'PATCH']:
            if 'body' not in request_spec:
                raise ValidationError("Request body required for POST/PUT/PATCH methods")
            self.validate_body(request_spec['body'])

    def validate_url(self, url: str) -> None:
        """Validate URL format and structure"""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError(f"Invalid URL format: {url}")
            if result.scheme not in ['http', 'https']:
                raise ValidationError(f"URL must use HTTP(S) protocol: {url}")
        except Exception as e:
            raise ValidationError(f"URL validation failed: {str(e)}")

    def validate_headers(self, headers: Dict[str, str]) -> None:
        """Validate request headers"""
        for key, value in headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError(f"Invalid header type for {key}: {value}")
            if not key or not value:
                raise ValidationError(f"Empty header key or value: {key}: {value}")

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate request parameters"""
        for key, value in params.items():
            if value is None:
                raise ValidationError(f"Parameter '{key}' cannot be None")
            
            # Validate based on parameter name patterns
            if 'email' in key.lower():
                self.validate_pattern(value, self.patterns['email'], f"Invalid email format: {value}")
            elif 'date' in key.lower():
                self.validate_pattern(value, self.patterns['date'], f"Invalid date format: {value}")
            elif 'api_key' in key.lower():
                self.validate_pattern(value, self.patterns['api_key'], f"Invalid API key format: {value}")
            elif 'url' in key.lower():
                self.validate_pattern(value, self.patterns['url'], f"Invalid URL format: {value}")

    def validate_body(self, body: Union[Dict, List, str]) -> None:
        """Validate request body"""
        if isinstance(body, (dict, list)):
            try:
                # Verify JSON serializable
                json.dumps(body)
            except Exception as e:
                raise ValidationError(f"Invalid JSON body: {str(e)}")
        elif isinstance(body, str):
            try:
                # Verify valid JSON string
                json.loads(body)
            except Exception as e:
                raise ValidationError(f"Invalid JSON string in body: {str(e)}")
        else:
            raise ValidationError(f"Unsupported body type: {type(body)}")

    def validate_pattern(self, value: str, pattern: str, error_message: str) -> None:
        """Validate string against regex pattern"""
        if not isinstance(value, str) or not re.match(pattern, value):
            raise ValidationError(error_message)

    def validate_api_key(self, api_key: str, auth_method: str) -> None:
        """Validate API key format based on authentication method"""
        if not api_key and auth_method.lower() not in ['none', 'no auth']:
            raise ValidationError("API key required for authentication")
        
        if api_key:
            if len(api_key) < 20:
                raise ValidationError("API key too short (minimum 20 characters)")
            if not re.match(r'^[A-Za-z0-9_\-]+$', api_key):
                raise ValidationError("API key contains invalid characters")

    def set_default_values(self, request_spec: Dict[str, Any], api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values for optional parameters"""
        defaults = request_spec.copy()
        
        # Default headers
        defaults.setdefault('headers', {})
        defaults['headers'].setdefault('Content-Type', 'application/json')
        defaults['headers'].setdefault('Accept', 'application/json')
        
        # Default query parameters
        defaults.setdefault('params', {})
        
        # Default method
        defaults.setdefault('method', 'GET')
        
        # Default timeout
        defaults.setdefault('timeout', 30)
        
        return defaults