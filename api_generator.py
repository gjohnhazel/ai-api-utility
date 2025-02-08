import requests
import json
from urllib.parse import urlparse
from credential_manager import get_credential_manager
from validator import RequestValidator, ValidationError
import os
import re

# Replace with your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class APIRequestGenerator:
    def __init__(self):
        self.openai_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        self.credential_manager = get_credential_manager()
        self.validator = RequestValidator()  # Add validator instance

    def get_api_signup_url(self, api_name: str) -> str:
        """Generate API signup/documentation URL."""
        # Convert API name to search-friendly format
        search_query = api_name.replace(' ', '+') + '+API+key+signup'
        return f"https://google.com/search?q={search_query}"

    def handle_credentials(self, api_info: dict) -> str:
        """Handle credential collection and storage for the API."""
        api_name = api_info['name']
        auth_method = api_info['authentication_method'].lower()
        
        # Check if API requires authentication
        if 'no' in auth_method or 'none' in auth_method:
            return ""  # Return empty string for APIs that don't require authentication
        
        # For APIs that require authentication
        print(f"\nTo use {api_name}, you need an API key.")
        
        # Show documentation if available
        if 'documentation' in api_info and api_info['documentation']:
            print(f"Documentation: {api_info['documentation']}")
            print(f"Get your API key here: {api_info['documentation']}")
        else:
            # Only use Google search as fallback if no documentation URL
            signup_url = self.get_api_signup_url(api_name)
            print(f"You can get one here: {signup_url}")
        
        # Check for existing credentials
        existing_key = self.credential_manager.get_credential(api_name, 'api_key')
        if existing_key:
            use_existing = input(f"\nFound existing API key for {api_name}. Use it? (yes/no): ").lower()
            if use_existing in ['y', 'yes']:
                return existing_key
        
        # Prompt for new API key
        while True:
            api_key = input(f"\nPlease enter your {api_name} API key: ").strip()
            if api_key:
                break
            print("API key is required to proceed.")
        
        save_key = input("Would you like to save this API key for future use? (yes/no): ").lower()
        if save_key in ['y', 'yes']:
            self.credential_manager.store_credential(api_name, 'api_key', api_key)
        
        return api_key
    
    def identify_api(self, user_goal: str) -> dict:
        """Identify the most appropriate API for the user's goal."""
        prompt = f"""
        As an API expert, analyze this user request: "{user_goal}"
        
        First, interpret the user's intent and identify any key parameters or requirements.
        Then, identify the most suitable public API that can fulfill this request.
        
        Return a JSON object with this structure:
        {{
            "name": "Name of the API",
            "why_best_choice": "Brief explanation of why this API is recommended, including how it matches the user's needs",
            "base_url": "The base URL for API requests",
            "authentication_method": "How to authenticate (e.g., API key, OAuth)",
            "credentials_needed": "What credentials are required",
            "documentation": "URL to the API documentation",
            "usage_limits": "Brief description of usage limits and pricing"
        }}
        
        Ensure the chosen API is well-documented, reliable, and appropriate for the user's needs.
        """

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=self.openai_headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an API expert. Return only valid JSON without any additional text."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            try:
                content = response.json()['choices'][0]['message']['content'].strip()
                # Remove any potential markdown code block indicators
                content = content.replace('```json', '').replace('```', '').strip()
                return json.loads(content)
            except json.JSONDecodeError as e:
                print("Debug - API Response Content:")
                print(content)
                raise Exception(f"Error parsing API identification response: {str(e)}")
        else:
            raise Exception(f"Error identifying API: {response.text}")

    def get_followup_questions(self, initial_prompt: str, api_info: dict) -> list:
        """Generate relevant followup questions based on the identified API."""
        prompt = f"""
        User request: {initial_prompt}
        Selected API: {api_info['name']}
        
        First, analyze what information we already have from the user's request.
        Then, generate 3 questions that will help gather any missing information needed to make a precise API request.
        Also provide a default value for each question in parentheses.
        
        Consider:
        - Essential parameters needed for the API endpoint
        - Any ambiguous terms that need clarification
        - Options that could help refine the results
        
        Return exactly 3 questions with their defaults, one per line, in format: "Question (default: value)"
        """

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=self.openai_headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Generate only the questions, one per line, without any additional text."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            questions = response.json()['choices'][0]['message']['content'].strip().split('\n')
            return [q.strip() for q in questions[:3]]
        else:
            raise Exception(f"Error generating questions: {response.text}")

    def handle_help_command(self, command: str = None) -> str:
        """Handle help commands and return appropriate help text"""
        return self.validator.get_help(command)

    def handle_credentials(self, api_info: dict) -> str:
        """Enhanced credential handling with validation"""
        api_name = api_info['name']
        auth_method = api_info['authentication_method'].lower()
        
        # Check if API requires authentication
        if 'no' in auth_method or 'none' in auth_method:
            return ""
        
        print(f"\nTo use {api_name}, you need an API key.")
        
        # Show documentation if available
        if 'documentation' in api_info and api_info['documentation']:
            print(f"Documentation: {api_info['documentation']}")
        else:
            signup_url = self.get_api_signup_url(api_name)
            print(f"You can get one here: {signup_url}")
        
        # Check for existing credentials
        existing_key = self.credential_manager.get_credential(api_name, 'api_key')
        if existing_key:
            use_existing = input(f"\nFound existing API key for {api_name}. Use it? (yes/no): ").lower()
            if use_existing in ['y', 'yes']:
                # Validate existing key
                try:
                    self.validator.validate_api_key(existing_key, auth_method)
                    return existing_key
                except ValidationError as e:
                    print(f"Existing API key validation failed: {str(e)}")
        
        # Prompt for new API key with validation
        while True:
            api_key = input(f"\nPlease enter your {api_name} API key: ").strip()
            try:
                self.validator.validate_api_key(api_key, auth_method)
                break
            except ValidationError as e:
                print(f"Invalid API key: {str(e)}")
                print("Please try again.")
        
        save_key = input("Would you like to save this API key for future use? (yes/no): ").lower()
        if save_key in ['y', 'yes']:
            self.credential_manager.store_credential(api_name, 'api_key', api_key)
        
        return api_key

    def prepare_api_request(self, context: dict, api_info: dict, api_key: str) -> dict:
        """Enhanced request preparation with validation"""
        base_url = api_info.get('base_url', '')
        if not base_url and 'documentation' in api_info:
            parsed_url = urlparse(api_info['documentation'])
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Create request specification
        request_spec = {
            'url': base_url,
            'method': 'GET',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            'params': {},
            'body': None
        }

        # Add API key based on authentication method
        auth_method = api_info.get('authentication_method', '').lower()
        if 'header' in auth_method:
            request_spec['headers']['Authorization'] = f'Bearer {api_key}'
        else:
            # Default to query parameter if not specified
            request_spec['params']['apikey'] = api_key

        # Add user context to parameters, using actual values instead of defaults
        if context.get('answer1') and context['answer1'] != "default":
            request_spec['params']['q'] = context['answer1']

        # Set default values
        request_spec = self.validator.set_default_values(request_spec, api_info)
        
        try:
            self.validator.validate_request(request_spec)
        except ValidationError as e:
            print(f"\nRequest validation failed: {str(e)}")
            if hasattr(e, 'details') and e.details:
                print("Details:", json.dumps(e.details, indent=2))
            raise
        
        return request_spec

    def execute_request(self, request_spec: dict) -> dict:
        """Enhanced request execution with validation and error handling"""
        try:
            self.validator.validate_request(request_spec)
            
            response = requests.request(
                method=request_spec.get('method', 'GET'),
                url=request_spec['url'],
                headers=request_spec.get('headers', {}),
                params=request_spec.get('params', {}),
                json=request_spec.get('body') if request_spec.get('body') else None,
                timeout=request_spec.get('timeout', 30)
            )
            
            if response.status_code != 200:
                error_details = self.analyze_error(response, request_spec)
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'error_analysis': error_details,
                    'original_request': request_spec
                }
            
            try:
                response_body = response.json()
            except:
                response_body = response.text

            return {
                'error': False,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_body
            }
        except ValidationError as e:
            raise Exception(f"Request validation failed: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error executing request: {str(e)}")

    def analyze_error(self, response, original_request: dict) -> dict:
        """Use AI to analyze the error and suggest fixes"""
        try:
            error_response = response.json()
        except:
            error_response = response.text

        prompt = f"""
        Analyze this API error and provide guidance on how to fix it:

        Status Code: {response.status_code}
        Error Response: {error_response}
        Original Request:
        URL: {original_request['url']}
        Method: {original_request['method']}
        Headers: {original_request['headers']}
        Parameters: {original_request['params']}
        Body: {original_request.get('body')}

        Return a JSON object with this structure:
        {{
            "error_description": "Clear description of what went wrong",
            "suggested_fixes": ["List of specific changes needed"],
            "requires_user_input": boolean,
            "user_prompts": ["Questions to gather information needed to fix the request"],
            "request_updates": {{
                "url": "string",
                "params": {{}},
                "method": "string"
            }}
        }}

        Important: When asking questions, focus on gathering information to help YOU generate a better request.
        Don't ask yes/no questions - ask for specific values needed to fix the request.
        """

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=self.openai_headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an API expert. Return only valid JSON without any additional text."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            return json.loads(content)
        else:
            raise Exception(f"Error analyzing API error: {response.text}")

    def update_request_with_user_input(self, request_spec: dict, user_responses: dict) -> dict:
        """Update request specification with user-provided information"""
        updated_spec = request_spec.copy()
        
        # Update URL if provided
        if 'url' in user_responses:
            updated_spec['url'] = user_responses['url']
        
        # Initialize params if not present
        if 'params' not in updated_spec:
            updated_spec['params'] = {}
        
        # Update parameters, maintaining existing structure
        if 'parameter_updates' in user_responses:
            for param_key, new_value in user_responses['parameter_updates'].items():
                # Find the actual parameter key in the existing spec that matches
                # the parameter we're trying to update
                matching_key = next(
                    (key for key in updated_spec['params'].keys() 
                     if key.lower() == param_key.lower()),
                    param_key  # If no match found, use the new key
                )
                updated_spec['params'][matching_key] = new_value
        
        return updated_spec

def format_api_info(api_info: dict) -> str:
    """Format the API information for display."""
    return f"""
Recommended API: {api_info.get('name')}
----------------------
{api_info.get('why_best_choice')}

Documentation: {api_info.get('documentation')}
Authentication: {api_info.get('authentication_method')}
Usage/Pricing: {api_info.get('usage_limits')}
"""

def format_request_preview(request_spec: dict) -> str:
    """Format the request specification for user preview."""
    preview = f"""
API Request Preview:
------------------
URL: {request_spec.get('url')}
Method: {request_spec.get('method')}

Headers:
{json.dumps(request_spec.get('headers', {}), indent=2)}

Query Parameters:
{json.dumps(request_spec.get('params', {}), indent=2)}

Request Body:
{json.dumps(request_spec.get('body', {}), indent=2) if request_spec.get('body') else 'None'}

Special Instructions:
{request_spec.get('instructions', 'None')}
"""
    return preview

def main():
    try:
        generator = APIRequestGenerator()
        
        print("\nWelcome to the API Request Generator!")
        print("Type 'help' for usage information or describe your goal.")
        
        while True:
            initial_input = input("\nWhat would you like to do? ").strip().lower()
            
            # Handle help commands
            if initial_input.startswith('help'):
                command = initial_input.split()[1] if len(initial_input.split()) > 1 else None
                print(generator.handle_help_command(command))
                continue
            elif initial_input in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            # Process API request
            try:
                # Identify appropriate API
                print("\nIdentifying the best API for your needs...")
                api_info = generator.identify_api(initial_input)
                print(format_api_info(api_info))
                
                # Get user confirmation
                proceed = input("\nWould you like to proceed with this API? (yes/no): ").lower()
                if proceed not in ['yes', 'y']:
                    print("Operation cancelled. Feel free to try again with a different request.")
                    continue

                # Handle API credentials with validation
                try:
                    api_key = generator.handle_credentials(api_info)
                except ValidationError as e:
                    print(f"\nCredential validation error: {str(e)}")
                    continue

                # Get followup questions
                print("\nGenerating relevant technical questions...")
                questions = generator.get_followup_questions(initial_input, api_info)
                
                # Gather context with default value handling
                context = {
                    'initial_prompt': initial_input,
                    'answer1': input(f"\n1. {questions[0]}\nYour answer (press Enter for default): ").strip() or "default",
                    'answer2': input(f"\n2. {questions[1]}\nYour answer (press Enter for default): ").strip() or "default",
                    'answer3': input(f"\n3. {questions[2]}\nYour answer (press Enter for default): ").strip() or "default"
                }
                
                # Prepare and validate API request
                print("\nGenerating and validating API request specification...")
                try:
                    request_spec = generator.prepare_api_request(context, api_info, api_key)
                except ValidationError as e:
                    print(f"\nRequest validation failed: {str(e)}")
                    if hasattr(e, 'details') and e.details:
                        print("Details:", json.dumps(e.details, indent=2))
                    continue
                
                # Show request preview and get user feedback
                while True:  # Add loop for request modifications
                    print(format_request_preview(request_spec))
                    
                    # Enhanced user choice menu
                    print("\nWhat would you like to do?")
                    print("1. Execute the request")
                    print("2. Modify the request")
                    print("3. Cancel")
                    
                    choice = input("Enter your choice (1-3): ").strip()
                    
                    if choice == "1":
                        print("\nExecuting request...")
                        while True:  # Allow for multiple retry attempts
                            try:
                                result = generator.execute_request(request_spec)
                                
                                if result.get('error'):
                                    error_analysis = result['error_analysis']
                                    print(f"\nError: {error_analysis['error_description']}")
                                    print("\nSuggested fixes:")
                                    for fix in error_analysis['suggested_fixes']:
                                        print(f"- {fix}")
                                    
                                    if error_analysis['requires_user_input']:
                                        print("\nAdditional information needed:")
                                        user_responses = {}
                                        
                                        for prompt in error_analysis['user_prompts']:
                                            response = input(f"{prompt}: ").strip()
                                            if response:
                                                # Store responses for AI to analyze
                                                user_responses[prompt] = response
                                        
                                        # Generate a new prompt with the user's responses
                                        followup_prompt = f"""
                                        Based on the original error and these user responses:
                                        {json.dumps(user_responses, indent=2)}
                                        
                                        Please provide updated request parameters that will fix the error.
                                        Return only the request_updates object with the correct URL and parameters.
                                        """
                                        
                                        # Get updated request specification from AI
                                        updated_spec = generator.get_updated_request_spec(followup_prompt)
                                        if updated_spec:
                                            request_spec.update(updated_spec)
                                        
                                        print("\nUpdated request preview:")
                                        print(format_request_preview(request_spec))
                                        retry = input("\nWould you like to retry with these updates? (yes/no): ").lower()
                                        if retry not in ['yes', 'y']:
                                            break
                                    else:
                                        # Apply AI-suggested updates automatically
                                        request_spec.update(error_analysis['request_updates'])
                                        print("\nUpdated request preview:")
                                        print(format_request_preview(request_spec))
                                        retry = input("\nWould you like to retry with these updates? (yes/no): ").lower()
                                        if retry not in ['yes', 'y']:
                                            break
                                else:
                                    print("\nAPI Response:")
                                    print(json.dumps(result, indent=2))
                                    print("\nSuccess! What adventure should we go on next?")
                                    break  # Break from retry loop
                            except Exception as e:
                                print(f"\nError executing request: {str(e)}")
                                break
                        break  # Break from outer preview loop
                    elif choice == "2":
                        print("\nWhat would you like to modify?")
                        print("1. URL")
                        print("2. Parameters")
                        print("3. Headers")
                        print("4. Method")
                        
                        mod_choice = input("Enter your choice (1-4): ").strip()
                        
                        if mod_choice == "1":
                            new_url = input("Enter new URL: ").strip()
                            request_spec['url'] = new_url
                        elif mod_choice == "2":
                            print("\nCurrent parameters:", json.dumps(request_spec.get('params', {}), indent=2))
                            print("\nEnter parameter updates in format 'key=value' (one per line)")
                            print("Leave empty to finish")
                            while True:
                                param_input = input("> ").strip()
                                if not param_input:
                                    break
                                if '=' in param_input:
                                    key, value = param_input.split('=', 1)
                                    request_spec.setdefault('params', {})
                                    request_spec['params'][key.strip()] = value.strip()
                        elif mod_choice == "3":
                            print("\nCurrent headers:", json.dumps(request_spec.get('headers', {}), indent=2))
                            print("\nEnter header updates in format 'key=value' (one per line)")
                            print("Leave empty to finish")
                            while True:
                                header_input = input("> ").strip()
                                if not header_input:
                                    break
                                if '=' in header_input:
                                    key, value = header_input.split('=', 1)
                                    request_spec.setdefault('headers', {})
                                    request_spec['headers'][key.strip()] = value.strip()
                        elif mod_choice == "4":
                            new_method = input("Enter HTTP method (GET, POST, PUT, DELETE): ").strip().upper()
                            if new_method in ['GET', 'POST', 'PUT', 'DELETE']:
                                request_spec['method'] = new_method
                            else:
                                print("Invalid method. Keeping existing method.")
                        
                        # Show updated preview
                        continue
                    elif choice == "3":
                        print("\nRequest cancelled.")
                        break
                    else:
                        print("\nInvalid choice. Please try again.")
                        continue
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("You can type 'help' for usage information or try again with a different request.")
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main()
