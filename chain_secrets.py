#!/usr/bin/env python3

import os
import sys
import hashlib
import re
import base64
import gnupg
from pwd import getpwnam
from subprocess import run, CalledProcessError

# --- Logging setup ---
class Logger:
    def __init__(self, log_file, debug_mode):
        self.log_file = log_file
        self.debug_mode = debug_mode
        if self.debug_mode:
            with open(self.log_file, 'a') as f:
                f.write(f"\n--- Script run at {datetime.now()} ---\n")

    def log(self, message):
        if self.debug_mode:
            with open(self.log_file, 'a') as f:
                f.write(f"{message}\n")

# Define a secure cleanup function
def secure_remove(path):
    try:
        if os.path.isfile(path):
            run(['shred', '-n', '5', '-z', '-u', path], check=True, stdout=sys.stderr, stderr=sys.stderr)
        elif os.path.isdir(path):
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path):
                    run(['shred', '-n', '5', '-z', '-u', file_path], check=True, stdout=sys.stderr, stderr=sys.stderr)
            os.rmdir(path)
    except Exception as e:
        print(f"Error during secure removal of {path}: {e}", file=sys.stderr)

def main():
    # File paths
    EMAIL_PATH = '/var/www/appdata/email'
    MAPPING_GPG_PATH = '/root/mapping.gpg'
    self_path = os.path.abspath(sys.argv[0])

    # Initialize logger based on DEBUG_MODE environment variable
    debug_mode = os.environ.get('DEBUG_MODE') == 'true'
    logger = Logger('/tmp/chainer.log', debug_mode)
    
    # Ensure this script self-destructs
    def cleanup():
        secure_remove(self_path)

    success = True # Initialize success flag
    try:
        # Check for the email file
        if not os.path.exists(EMAIL_PATH):
            logger.log("Email file not found. Exiting.")
            success = False
            return

        with open(EMAIL_PATH, 'r') as f:
            email = f.read().strip()
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                logger.log("Invalid email format. Exiting.")
                success = False
                return
        
        # Get original file ownership to restore later
        original_uid = os.stat(EMAIL_PATH).st_uid
        original_gid = os.stat(EMAIL_PATH).st_gid

        # Initialize gnupg and decrypt the mapping file
        try:
            gpg = gnupg.GPG(gnupghome='/root/.gnupg')
            with open(MAPPING_GPG_PATH, 'rb') as f:
                decrypted_data = gpg.decrypt_file(f, always_trust=True)
            if not decrypted_data.ok:
                raise Exception(f"Decryption failed: {decrypted_data.status}")
            mapping_content = decrypted_data.data.decode('utf-8')
        except Exception as e:
            logger.log(f"Failed to decrypt mapping file: {e}")
            success = False
            return

        current_hash = hashlib.sha512(email.encode('utf-8')).hexdigest()
        logger.log(f"Starting secret chaining with email: {email}")

        # Process the mapping file
        for i, line in enumerate(mapping_content.strip().split('\n')):
            parts = line.split('|')
            if len(parts) < 3:
                continue

            filepath, old_secret, secret_type = parts[0], parts[1], parts[2]
            password_user = parts[3] if len(parts) > 3 else None
            
            suffix = current_hash[-4:]
            logger.log(f"Processing step {i+1}: {filepath} with suffix '{suffix}'")

            # --- Secret transformation logic from chainer.py ---
            new_secret_plaintext = ''
            if secret_type == 'plain text':
                new_secret = old_secret + suffix
                new_secret_plaintext = new_secret
            elif secret_type == 'flag':
                m = re.match(r'flag\{(.+)\}', old_secret)
                if m:
                    flag_content = m.group(1)
                    new_secret = f'flag{{{flag_content}_{suffix}}}'
                    new_secret_plaintext = f'{flag_content}_{suffix}'
                else:
                    logger.log(f"Warning: Invalid flag format for {old_secret}. Skipping.")
                    continue
            elif secret_type == 'base64':
                try:
                    old_secret_plaintext = base64.b64decode(old_secret).decode('utf-8')
                    new_secret_plaintext = old_secret_plaintext + suffix
                    new_secret = base64.b64encode(new_secret_plaintext.encode('utf-8')).decode('utf-8')
                except Exception as e:
                    logger.log(f"Warning: Failed to decode base64 secret {old_secret}. Skipping.")
                    continue
            else:
                logger.log(f"Warning: Unknown secret type '{secret_type}'. Skipping.")
                continue

            # --- File modification and password update logic ---
            try:
                with open(filepath, 'r') as f:
                    filedata = f.read()

                # Check if the original secret exists
                if old_secret not in filedata:
                    logger.log(f"Original secret '{old_secret}' not found in '{filepath}'. Chain broken.")
                    success = False
                    break # Critical: Stop the chain
                
                # Replace the old secret with the new one
                filedata = filedata.replace(old_secret, new_secret, 1)

                with open(filepath, 'w') as f:
                    f.write(filedata)
                
                logger.log(f"Successfully replaced '{old_secret}' with '{new_secret}' in '{filepath}'.")

                if password_user:
                    logger.log(f"Changing password for user '{password_user}'.")
                    run(['chpasswd'], input=f'{password_user}:{new_secret_plaintext}\n', check=True, text=True)

                # Advance the chain with the new secret's plaintext
                current_hash = hashlib.sha512(new_secret_plaintext.encode('utf-8')).hexdigest()

            except Exception as e:
                logger.log(f"Error processing {filepath}: {e}")
                success = False
                break
        
    except Exception as e:
        logger.log(f"An unexpected error occurred: {e}")
        success = False
    finally:
        # Write success/failure to the email file based on the final status
        status = 'success' if success else 'failed'
        try:
            with open(EMAIL_PATH, 'w') as f:
                f.write(status)
            os.chown(EMAIL_PATH, original_uid, original_gid)
            logger.log(f"Final status '{status}' written to email file. Ownership restored.")
        except Exception as e:
            logger.log(f"Failed to write final status to email file: {e}")
        
        # Crucial final cleanup
        secure_remove(MAPPING_GPG_PATH)
        cleanup()

if __name__ == "__main__":
    from datetime import datetime
    main()