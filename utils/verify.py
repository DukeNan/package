import hashlib
import json
import os
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from constants import FLAG, PROJECT_DIR, SECURE_KEY, PackageFilenameEnum
from utils.log_base import logger

__all__ = ["PackageBuilder"]


class AESFileCryptoWithSalt:
    def __init__(self, password: str, iterations: int = 100000):
        try:
            if not password:
                raise ValueError("password is empty")
            if iterations <= 0:
                raise ValueError("iterations must be greater than 0")

            self.password = password.encode("utf-8")
            self.iterations = iterations
            self.backend = default_backend()
        except UnicodeEncodeError as e:
            raise ValueError(f"password encoding failed: {e}")
        except Exception as e:
            raise RuntimeError(f"initialize AES encryption failed: {e}")

    def _derive_key(self, salt: bytes) -> bytes:
        try:
            if not salt or len(salt) != 16:
                raise ValueError("salt must be 16 bytes")

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # AES-256
                salt=salt,
                iterations=self.iterations,
                backend=self.backend,
            )
            return kdf.derive(self.password)
        except Exception as e:
            raise RuntimeError(f"key derivation failed: {e}")

    def encrypt_file(self, input_path: str, output_path: str):
        try:
            if not input_path or not output_path:
                raise ValueError("input and output path is empty")

            if not os.path.exists(input_path):
                raise FileNotFoundError(f"input file not found: {input_path}")

            salt = os.urandom(16)
            key = self._derive_key(salt)
            iv = os.urandom(16)

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(128).padder()

            with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
                # 文件前写入：salt + iv
                f_out.write(salt)
                f_out.write(iv)

                while True:
                    chunk = f_in.read(1024)
                    if not chunk:
                        break
                    padded = padder.update(chunk)
                    encrypted = encryptor.update(padded)
                    f_out.write(encrypted)

                f_out.write(encryptor.update(padder.finalize()) + encryptor.finalize())
        except FileNotFoundError:
            raise
        except PermissionError as e:
            raise PermissionError(f"file permission error: {e}")
        except OSError as e:
            raise OSError(f"file operation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"file encryption failed: {e}")
        logger.info(f"File encrypted successfully: {output_path}")

    def decrypt_file(self, input_path: str):
        try:
            if not input_path:
                raise ValueError("input path is empty")

            if not os.path.exists(input_path):
                raise FileNotFoundError(f"input file not found: {input_path}")

            with open(input_path, "rb") as f_in:
                salt = f_in.read(16)
                iv = f_in.read(16)

                if len(salt) != 16 or len(iv) != 16:
                    raise ValueError(
                        "file format error: salt or iv length is incorrect"
                    )

                key = self._derive_key(salt)

                cipher = Cipher(
                    algorithms.AES(key), modes.CBC(iv), backend=self.backend
                )
                decryptor = cipher.decryptor()
                unpadder = padding.PKCS7(128).unpadder()

                decrypted_data = b""
                while True:
                    chunk = f_in.read(1024)
                    if not chunk:
                        break
                    decrypted = decryptor.update(chunk)
                    decrypted_data += unpadder.update(decrypted)

                decrypted_data += unpadder.update(decryptor.finalize())
                decrypted_data += unpadder.finalize()
        except Exception:
            raise ValueError(f"file has been modified, decryption failed.")
        logger.info(f"File decrypted successfully: {input_path}")
        return decrypted_data.decode("utf-8")


class PackageBuilder:
    PACKAGE_FILES = [
        PackageFilenameEnum.VERIFY.value,
        PackageFilenameEnum.PACKAGE.value,
        PackageFilenameEnum.VERSION.value,
        PackageFilenameEnum.README.value,
    ]

    def __init__(self, package_name: str = None, config_path=None):
        self.package_path = self._init_package_path()
        self.package_checksum = ""
        self.config = self._parse_config(config_path)
        self.package_name = self._init_package_name(package_name)

    def _init_package_name(self, package_name: str = None):
        if not package_name:
            package_name = self.config.get("package_name")

        if not package_name.endswith(".tar.gz"):
            package_name = f"{package_name}.tar.gz"

        return package_name

    def _init_package_path(self):
        package_path = PROJECT_DIR.joinpath(PackageFilenameEnum.PACKAGE.value)
        if not package_path.exists():
            raise FileNotFoundError(f"Package file not found: {package_path}")
        return package_path

    def _parse_config(self, config_path):
        if not config_path:
            config_path = PROJECT_DIR.joinpath(PackageFilenameEnum.VERSION.value)
        with open(config_path, "r") as f:
            return json.load(f)

    def _get_checksum(self):
        if not self.package_path.exists() or not self.package_path.is_file():
            raise FileNotFoundError(f"Package file not found: {self.package_path}")
        return hashlib.sha256(self.package_path.read_bytes()).hexdigest()

    def encrypt_verify_file(self):
        """
        加密 verify.info 文件，并生成verify文件
        """
        checksum = self.package_checksum or self._get_checksum()
        verify_info_file_path = PROJECT_DIR.joinpath(
            PackageFilenameEnum.VERIFY_INFO.value
        )
        verify_info_file_path.write_text(f"{FLAG}_{checksum}")

        aes_crypto = AESFileCryptoWithSalt(f"{SECURE_KEY}_{checksum}")
        verify_file_path = PROJECT_DIR.joinpath(PackageFilenameEnum.VERIFY.value)
        aes_crypto.encrypt_file(verify_info_file_path, verify_file_path)
        return verify_file_path

    def decrypt_verify_file(self):
        """
        解密 verify 文件，并生成 verify.info 文件
        """
        encrypted_verify_file_path = PROJECT_DIR.joinpath(
            PackageFilenameEnum.VERIFY.value
        )
        if (
            not encrypted_verify_file_path.exists()
            or not encrypted_verify_file_path.is_file()
        ):
            raise FileNotFoundError(
                f"Encrypted verify file not found: {encrypted_verify_file_path}"
            )
        checksum = self._get_checksum()
        aes_crypto = AESFileCryptoWithSalt(f"{SECURE_KEY}_{checksum}")
        decrypted_data = aes_crypto.decrypt_file(encrypted_verify_file_path)
        if decrypted_data != f"{FLAG}_{checksum}":
            raise ValueError(f"file has been modified, decryption failed.")
        return decrypted_data
