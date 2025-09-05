"""Secure API key retrieval for bill2csv"""

import os
import subprocess
import sys


class APIKeyManager:
    """Manages secure retrieval of API keys from various sources"""
    
    @staticmethod
    def get_api_key_from_keychain(service: str, account: str) -> str:
        """
        Retrieve API key from macOS Keychain
        
        Args:
            service: Keychain service name
            account: Keychain account name
            
        Returns:
            API key string
            
        Raises:
            RuntimeError: If key retrieval fails
        """
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", account, "-s", service, "-w"],
                capture_output=True,
                text=True,
                check=True,
            )
            api_key = result.stdout.strip()
            if not api_key:
                raise RuntimeError(f"Empty API key retrieved from Keychain")
            return api_key
        except subprocess.CalledProcessError as e:
            if "could not be found" in e.stderr:
                raise RuntimeError(
                    f"API key not found in Keychain. "
                    f"Store it with: security add-generic-password "
                    f'-a "{account}" -s "{service}" -w "YOUR_API_KEY" -U'
                )
            else:
                raise RuntimeError(f"Failed to retrieve API key from Keychain: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "security command not found. This feature requires macOS."
            )
    
    @staticmethod
    def get_api_key_from_env(env_name: str) -> str:
        """
        Retrieve API key from environment variable
        
        Args:
            env_name: Name of environment variable
            
        Returns:
            API key string
            
        Raises:
            RuntimeError: If environment variable not set
        """
        api_key = os.environ.get(env_name)
        if not api_key:
            raise RuntimeError(
                f"API key not found in environment variable {env_name}. "
                f"Set it with: export {env_name}='your_api_key'"
            )
        return api_key
    
    @classmethod
    def get_api_key(cls, args) -> str:
        """
        Get API key using the appropriate method based on arguments
        
        Priority:
        1. macOS Keychain (if keychain args provided)
        2. Environment variable
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            API key string
            
        Raises:
            RuntimeError: If no API key can be retrieved
        """
        # Try Keychain first if credentials provided
        if args.keychain_service and args.keychain_account:
            try:
                return cls.get_api_key_from_keychain(
                    args.keychain_service, 
                    args.keychain_account
                )
            except RuntimeError as e:
                # If Keychain fails, try environment variable as fallback
                if not args.quiet:
                    print(f"Warning: {e}", file=sys.stderr)
                    print(f"Falling back to environment variable...", file=sys.stderr)
        
        # Try environment variable
        try:
            return cls.get_api_key_from_env(args.api_key_env)
        except RuntimeError as e:
            # If both methods fail, provide helpful error message
            error_msg = str(e)
            if args.keychain_service:
                error_msg = (
                    f"Failed to retrieve API key from both Keychain and environment.\n"
                    f"Either:\n"
                    f"1. Store in Keychain: security add-generic-password "
                    f'-a "{args.keychain_account}" -s "{args.keychain_service}" -w "YOUR_API_KEY" -U\n'
                    f"2. Set environment: export {args.api_key_env}='your_api_key'"
                )
            raise RuntimeError(error_msg)