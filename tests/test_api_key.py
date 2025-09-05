"""Unit tests for API key management"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from bill2csv.api_key import APIKeyManager


class TestAPIKeyManager:
    """Test API key retrieval methods"""
    
    def test_get_api_key_from_env_success(self):
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key_123"}):
            key = APIKeyManager.get_api_key_from_env("TEST_API_KEY")
            assert key == "test_key_123"
    
    def test_get_api_key_from_env_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="API key not found in environment"):
                APIKeyManager.get_api_key_from_env("MISSING_KEY")
    
    def test_get_api_key_from_env_empty(self):
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            with pytest.raises(RuntimeError, match="API key not found in environment"):
                APIKeyManager.get_api_key_from_env("EMPTY_KEY")
    
    @patch("subprocess.run")
    def test_get_api_key_from_keychain_success(self, mock_run):
        mock_run.return_value = Mock(
            stdout="keychain_key_123\n",
            stderr="",
            returncode=0
        )
        
        key = APIKeyManager.get_api_key_from_keychain("test-service", "test-account")
        assert key == "keychain_key_123"
        
        mock_run.assert_called_once_with(
            ["security", "find-generic-password", "-a", "test-account", "-s", "test-service", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
    
    @patch("subprocess.run")
    def test_get_api_key_from_keychain_not_found(self, mock_run):
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(
            1, 
            ["security"], 
            stderr="The specified item could not be found in the keychain"
        )
        
        with pytest.raises(RuntimeError, match="API key not found in Keychain"):
            APIKeyManager.get_api_key_from_keychain("test-service", "test-account")
    
    @patch("subprocess.run")
    def test_get_api_key_from_keychain_empty(self, mock_run):
        mock_run.return_value = Mock(
            stdout="",
            stderr="",
            returncode=0
        )
        
        with pytest.raises(RuntimeError, match="Empty API key retrieved"):
            APIKeyManager.get_api_key_from_keychain("test-service", "test-account")
    
    def test_get_api_key_env_fallback(self):
        args = Mock(
            keychain_service=None,
            keychain_account=None,
            api_key_env="TEST_KEY",
            quiet=False
        )
        
        with patch.dict(os.environ, {"TEST_KEY": "env_key_123"}):
            key = APIKeyManager.get_api_key(args)
            assert key == "env_key_123"
    
    @patch("subprocess.run")
    def test_get_api_key_keychain_then_env_fallback(self, mock_run):
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, ["security"], stderr="not found")
        
        args = Mock(
            keychain_service="test-service",
            keychain_account="test-account",
            api_key_env="FALLBACK_KEY",
            quiet=False
        )
        
        with patch.dict(os.environ, {"FALLBACK_KEY": "fallback_key_123"}):
            key = APIKeyManager.get_api_key(args)
            assert key == "fallback_key_123"
    
    def test_get_api_key_both_methods_fail(self):
        args = Mock(
            keychain_service=None,
            keychain_account=None,
            api_key_env="MISSING_KEY",
            quiet=False
        )
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="API key not found"):
                APIKeyManager.get_api_key(args)