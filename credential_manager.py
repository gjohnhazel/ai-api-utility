import json
import base64
#import keychain  # Pythonista's keychain module
from typing import Optional, Dict
import os
import platform
from pathlib import Path

def get_credential_manager():
    """Factory function to return appropriate credential manager based on platform"""
    if platform.system() == 'iOS':
        return PythonistaCredentialManager()
    return DesktopCredentialManager()

class BaseCredentialManager:
    """Base class defining the credential manager interface"""
    def get_credential(self, service: str, account: str) -> str:
        raise NotImplementedError
        
    def store_credential(self, service: str, account: str, credential: str) -> None:
        raise NotImplementedError

class PythonistaCredentialManager(BaseCredentialManager):
    """Credential manager for Pythonista on iOS"""
    def __init__(self):
        self.keychain = keychain
        
    def get_credential(self, service: str, account: str) -> str:
        return self.keychain.get_password(service, account)
        
    def store_credential(self, service: str, account: str, credential: str) -> None:
        self.keychain.set_password(service, account, credential)

class DesktopCredentialManager(BaseCredentialManager):
    """Credential manager for desktop environments"""
    def __init__(self):
        self.credentials_file = Path.home() / '.ai_api_credentials.json'
        self._ensure_credentials_file()
        
    def _ensure_credentials_file(self):
        """Create credentials file if it doesn't exist"""
        if not self.credentials_file.exists():
            self.credentials_file.write_text('{}')
        # Ensure file permissions are restricted
        self.credentials_file.chmod(0o600)
        
    def _read_credentials(self) -> dict:
        """Read credentials from file"""
        try:
            return json.loads(self.credentials_file.read_text())
        except json.JSONDecodeError:
            return {}
            
    def _write_credentials(self, credentials: dict):
        """Write credentials to file"""
        self.credentials_file.write_text(json.dumps(credentials, indent=2))
        
    def get_credential(self, service: str, account: str) -> str:
        """Get credential from file"""
        credentials = self._read_credentials()
        service_creds = credentials.get(service, {})
        return service_creds.get(account)
        
    def store_credential(self, service: str, account: str, credential: str) -> None:
        """Store credential in file"""
        credentials = self._read_credentials()
        if service not in credentials:
            credentials[service] = {}
        credentials[service][account] = credential
        self._write_credentials(credentials)

class CredentialManager:
    """Handles secure storage and retrieval of API credentials."""
    
    def __init__(self):
        self.service_name = 'APIRequestGenerator'
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Initialize storage if it doesn't exist."""
        try:
            keychain.get_password(self.service_name, 'credentials')
        except KeyError:
            # Initialize empty credential store
            keychain.set_password(self.service_name, 'credentials', 
                                self._encrypt_data(json.dumps({})))
    
    def _encrypt_data(self, data: str) -> str:
        """Basic encryption for storing data."""
        # Convert string to bytes
        data_bytes = data.encode('utf-8')
        # Use base64 to make the data storable
        return base64.b64encode(data_bytes).decode('utf-8')
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt stored data."""
        try:
            # Decode base64 data
            decrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error decrypting data: {str(e)}")
    
    def _get_credential_store(self) -> Dict:
        """Retrieve and decrypt the credential store."""
        try:
            encrypted_data = keychain.get_password(self.service_name, 'credentials')
            if encrypted_data:
                decrypted_data = self._decrypt_data(encrypted_data)
                return json.loads(decrypted_data)
            return {}
        except Exception as e:
            print(f"Error accessing credential store: {str(e)}")
            return {}
    
    def _save_credential_store(self, store: Dict):
        """Encrypt and save the credential store."""
        try:
            encrypted_data = self._encrypt_data(json.dumps(store))
            keychain.set_password(self.service_name, 'credentials', encrypted_data)
        except Exception as e:
            raise ValueError(f"Error saving credentials: {str(e)}")
    
    def store_credential(self, api_name: str, credential_type: str, 
                        credential_value: str) -> bool:
        """
        Store a credential for a specific API.
        
        Args:
            api_name: Name of the API (e.g., 'OpenWeatherMap')
            credential_type: Type of credential (e.g., 'api_key', 'oauth_token')
            credential_value: The actual credential value
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            store = self._get_credential_store()
            
            # Create API entry if it doesn't exist
            if api_name not in store:
                store[api_name] = {}
            
            # Store the credential
            store[api_name][credential_type] = credential_value
            
            self._save_credential_store(store)
            return True
        except Exception as e:
            print(f"Error storing credential: {str(e)}")
            return False
    
    def get_credential(self, api_name: str, credential_type: str) -> Optional[str]:
        """
        Retrieve a credential for a specific API.
        
        Args:
            api_name: Name of the API
            credential_type: Type of credential to retrieve
            
        Returns:
            Optional[str]: The credential value if found, None otherwise
        """
        try:
            store = self._get_credential_store()
            return store.get(api_name, {}).get(credential_type)
        except Exception as e:
            print(f"Error retrieving credential: {str(e)}")
            return None
    
    def list_apis(self) -> list:
        """List all APIs with stored credentials."""
        try:
            store = self._get_credential_store()
            return list(store.keys())
        except Exception:
            return []
    
    def delete_credential(self, api_name: str, credential_type: str) -> bool:
        """
        Delete a specific credential.
        
        Args:
            api_name: Name of the API
            credential_type: Type of credential to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            store = self._get_credential_store()
            if api_name in store and credential_type in store[api_name]:
                del store[api_name][credential_type]
                if not store[api_name]:  # Remove API entry if no credentials left
                    del store[api_name]
                self._save_credential_store(store)
                return True
            return False
        except Exception as e:
            print(f"Error deleting credential: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all stored credentials."""
        try:
            self._save_credential_store({})
            return True
        except Exception as e:
            print(f"Error clearing credentials: {str(e)}")
            return False

if __name__ == "__main__":
    # Test code
    cm = CredentialManager()
    
    # Test storing a credential
    cm.store_credential("TestAPI", "api_key", "test123")
    
    # Test retrieving the credential
    retrieved = cm.get_credential("TestAPI", "api_key")
    print(f"Retrieved credential: {retrieved}")
    
    # List all APIs
    apis = cm.list_apis()
    print(f"Stored APIs: {apis}")
