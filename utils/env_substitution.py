"""
Environment variable substitution utilities for CR mode.
Handles $XYZ pattern replacement with environment variables.
"""

import os
import re
from typing import Any, Dict, Union


class EnvSubstitution:
    """Handles environment variable substitution in configuration values."""
    
    # Pattern to match $VARIABLE_NAME or ${VARIABLE_NAME}
    ENV_PATTERN = re.compile(r'\$(\w+|\{[^}]+\})')
    
    @classmethod
    def substitute(cls, value: Any) -> Any:
        """
        Substitute environment variables in a value.
        
        Args:
            value: The value to process (string, dict, list, etc.)
            
        Returns:
            The value with environment variables substituted
        """
        if isinstance(value, str):
            return cls._substitute_string(value)
        elif isinstance(value, dict):
            return {k: cls.substitute(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [cls.substitute(item) for item in value]
        else:
            return value
    
    @classmethod
    def _substitute_string(cls, text: str) -> str:
        """
        Substitute environment variables in a string.
        
        Args:
            text: The string to process
            
        Returns:
            The string with environment variables substituted
        """
        def replace_env_var(match):
            var_name = match.group(1)
            # Remove braces if present
            if var_name.startswith('{') and var_name.endswith('}'):
                var_name = var_name[1:-1]
            
            # Get environment variable value
            env_value = os.getenv(var_name)
            if env_value is None:
                # If not found, keep the original pattern
                return match.group(0)
            return env_value
        
        return cls.ENV_PATTERN.sub(replace_env_var, text)
    
    @classmethod
    def substitute_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute environment variables in a configuration dictionary.
        
        Args:
            config: The configuration dictionary to process
            
        Returns:
            The configuration with environment variables substituted
        """
        return cls.substitute(config)
    
    @classmethod
    def get_missing_vars(cls, text: str) -> list:
        """
        Get list of environment variables referenced but not set.
        
        Args:
            text: The string to analyze
            
        Returns:
            List of missing environment variable names
        """
        matches = cls.ENV_PATTERN.findall(text)
        missing = []
        
        for match in matches:
            var_name = match
            if var_name.startswith('{') and var_name.endswith('}'):
                var_name = var_name[1:-1]
            
            if os.getenv(var_name) is None:
                missing.append(var_name)
        
        return missing
