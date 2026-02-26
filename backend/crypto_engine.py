"""
Crypto Engine Module - AES Encryption/Decryption using Quantum-Generated Keys
Provides real cryptographic operations for the Quantum Key Generator
"""

import os
import base64
import hashlib
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class CryptoEngine:
    """AES encryption engine using quantum-generated keys"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def _prepare_key(self, quantum_key: str, key_size: int = 256) -> bytes:
        """
        Prepare a quantum key for AES encryption.
        
        Args:
            quantum_key: Hex string key from quantum generator
            key_size: 128 or 256 bits
            
        Returns:
            bytes: Properly sized key bytes
        """
        # If quantum_key is hex, convert to bytes
        if all(c in '0123456789abcdefABCDEF' for c in quantum_key):
            key_bytes = bytes.fromhex(quantum_key)
        else:
            # If it's binary string, convert to hex first then bytes
            key_bytes = int(quantum_key, 2).to_bytes((len(quantum_key) + 7) // 8, byteorder='big')
        
        # Ensure key is correct length (16 bytes for AES-128, 32 bytes for AES-256)
        required_bytes = key_size // 8
        
        if len(key_bytes) >= required_bytes:
            return key_bytes[:required_bytes]
        else:
            # Extend key using SHA-256 if too short
            extended = hashlib.sha256(key_bytes).digest()
            return extended[:required_bytes]
    
    def _pad_message(self, message: bytes) -> bytes:
        """PKCS7 padding for AES block size"""
        block_size = 16
        padding_length = block_size - (len(message) % block_size)
        padding = bytes([padding_length] * padding_length)
        return message + padding
    
    def _unpad_message(self, padded_message: bytes) -> bytes:
        """Remove PKCS7 padding"""
        padding_length = padded_message[-1]
        if padding_length > 16 or padding_length == 0:
            raise ValueError("Invalid padding")
        # Verify padding is correct
        for i in range(padding_length):
            if padded_message[-(i+1)] != padding_length:
                raise ValueError("Invalid padding bytes")
        return padded_message[:-padding_length]
    
    def encrypt_text(self, plaintext: str, quantum_key: str, key_size: int = 256) -> dict:
        """
        Encrypt text using AES with a quantum-generated key.
        
        Args:
            plaintext: Text to encrypt
            quantum_key: Hex string key from quantum generator
            key_size: 128 or 256 bits (default: 256)
            
        Returns:
            dict: {ciphertext, iv, key_used, encryption_time_ms, algorithm}
        """
        start_time = time.time()
        
        # Prepare the key
        key_bytes = self._prepare_key(quantum_key, key_size)
        
        # Generate random IV (16 bytes for AES)
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Pad and encrypt
        padded_plaintext = self._pad_message(plaintext.encode('utf-8'))
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        
        encryption_time = (time.time() - start_time) * 1000
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'key_used': quantum_key[:16] + '...' if len(quantum_key) > 16 else quantum_key,
            'key_hash': hashlib.sha256(key_bytes).hexdigest()[:16],
            'algorithm': f'AES-{key_size}-CBC',
            'encryption_time_ms': round(encryption_time, 3),
            'plaintext_length': len(plaintext),
            'ciphertext_length': len(ciphertext)
        }
    
    def decrypt_text(self, ciphertext_b64: str, quantum_key: str, iv_b64: str, key_size: int = 256) -> dict:
        """
        Decrypt text using AES with a quantum-generated key.
        
        Args:
            ciphertext_b64: Base64 encoded ciphertext
            quantum_key: Hex string key from quantum generator
            iv_b64: Base64 encoded initialization vector
            key_size: 128 or 256 bits (default: 256)
            
        Returns:
            dict: {plaintext, decryption_time_ms, success}
        """
        start_time = time.time()
        
        try:
            # Prepare the key
            key_bytes = self._prepare_key(quantum_key, key_size)
            
            # Decode ciphertext and IV
            ciphertext = base64.b64decode(ciphertext_b64)
            iv = base64.b64decode(iv_b64)
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            
            # Decrypt and unpad
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = self._unpad_message(padded_plaintext)
            
            decryption_time = (time.time() - start_time) * 1000
            
            return {
                'plaintext': plaintext.decode('utf-8'),
                'decryption_time_ms': round(decryption_time, 3),
                'success': True
            }
            
        except Exception as e:
            return {
                'plaintext': None,
                'error': str(e),
                'decryption_time_ms': round((time.time() - start_time) * 1000, 3),
                'success': False
            }
    
    def encrypt_file(self, file_data: bytes, quantum_key: str, key_size: int = 256) -> dict:
        """
        Encrypt file data using AES with a quantum-generated key.
        
        Args:
            file_data: Raw file bytes
            quantum_key: Hex string key from quantum generator
            key_size: 128 or 256 bits
            
        Returns:
            dict: {encrypted_data, iv, metadata}
        """
        start_time = time.time()
        
        # Prepare the key
        key_bytes = self._prepare_key(quantum_key, key_size)
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Pad and encrypt
        padded_data = self._pad_message(file_data)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        encryption_time = (time.time() - start_time) * 1000
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'original_size': len(file_data),
            'encrypted_size': len(encrypted_data),
            'algorithm': f'AES-{key_size}-CBC',
            'encryption_time_ms': round(encryption_time, 3),
            'key_hash': hashlib.sha256(key_bytes).hexdigest()[:16]
        }
    
    def decrypt_file(self, encrypted_data_b64: str, quantum_key: str, iv_b64: str, key_size: int = 256) -> dict:
        """
        Decrypt file data using AES with a quantum-generated key.
        
        Args:
            encrypted_data_b64: Base64 encoded encrypted file
            quantum_key: Hex string key from quantum generator
            iv_b64: Base64 encoded IV
            key_size: 128 or 256 bits
            
        Returns:
            dict: {decrypted_data, metadata}
        """
        start_time = time.time()
        
        try:
            # Prepare the key
            key_bytes = self._prepare_key(quantum_key, key_size)
            
            # Decode
            encrypted_data = base64.b64decode(encrypted_data_b64)
            iv = base64.b64decode(iv_b64)
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            
            # Decrypt and unpad
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            decrypted_data = self._unpad_message(padded_data)
            
            decryption_time = (time.time() - start_time) * 1000
            
            return {
                'decrypted_data': base64.b64encode(decrypted_data).decode('utf-8'),
                'decrypted_size': len(decrypted_data),
                'decryption_time_ms': round(decryption_time, 3),
                'success': True
            }
            
        except Exception as e:
            return {
                'decrypted_data': None,
                'error': str(e),
                'success': False
            }


# Example usage for testing
if __name__ == "__main__":
    engine = CryptoEngine()
    
    # Test with a sample quantum key (256-bit hex)
    test_key = "A1B2C3D4E5F6789012345678901234567890ABCDEF1234567890ABCDEF123456"
    test_message = "Hello, Quantum World! This is a secret message."
    
    print("=== AES Encryption Test ===")
    encrypted = engine.encrypt_text(test_message, test_key)
    print(f"Original: {test_message}")
    print(f"Ciphertext: {encrypted['ciphertext'][:50]}...")
    print(f"IV: {encrypted['iv']}")
    print(f"Algorithm: {encrypted['algorithm']}")
    print(f"Time: {encrypted['encryption_time_ms']}ms")
    
    print("\n=== AES Decryption Test ===")
    decrypted = engine.decrypt_text(encrypted['ciphertext'], test_key, encrypted['iv'])
    print(f"Decrypted: {decrypted['plaintext']}")
    print(f"Success: {decrypted['success']}")
    print(f"Time: {decrypted['decryption_time_ms']}ms")
