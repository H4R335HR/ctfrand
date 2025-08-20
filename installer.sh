#!/bin/bash

# This script automates the installation of the midnight-chainer systemd service.
# It should be run as the root user from the /root directory.

echo "Beginning CTF Chainer installation..."

# Check for required files
if [[ ! -f "mapping.txt" ]]; then
    echo "Error: 'mapping.txt' not found in the current directory. Please create it and run the script again."
    exit 1
fi

if [[ ! -f "chain_secrets.py" ]]; then
    echo "Error: 'chain_secrets.py' not found in the current directory. Please create it and run the script again."
    exit 1
fi

echo "Required files found. Installing dependencies..."

# --- Function to check and install dependencies ---
install_dependencies() {
    echo "Checking for required dependencies..."
    
    # Check for GnuPG
    if ! command -v gpg &> /dev/null; then
        echo "GnuPG not found. Installing..."
        apt-get update
        apt-get install -y gnupg
    else
        echo "GnuPG is already installed."
    fi

    # Check for Python3 Pip
    if ! command -v pip3 &> /dev/null; then
        echo "python3-pip not found. Installing..."
        apt-get update
        apt-get install -y python3-pip
    else
        echo "python3-pip is already installed."
    fi

    # Install Python GnuPG library
    echo "Installing python-gnupg library..."
    pip3 install python-gnupg
    echo "Dependencies installed."
}

# Run the dependency installation function
install_dependencies

echo "Dependencies installed."

# Generate GPG key for automated decryption
echo "Generating GPG key for CTF-Secrets..."
gpg --batch --gen-key <<EOF
Key-Type: 1
Key-Length: 2048
Subkey-Type: 1
Subkey-Length: 2048
Name-Real: CTF-Secrets
Name-Comment: Automated Secret Chain
Expire-Date: 0
%no-protection
%commit
EOF
echo "GPG key generated."

# Encrypt the mapping.txt file and remove the original
echo "Encrypting mapping.txt and securing the original file..."
gpg --encrypt --recipient "CTF-Secrets" --output mapping.gpg mapping.txt
shred -n 5 -z -u mapping.txt
echo "Encryption complete. 'mapping.gpg' is ready."

# Move the Python script to /root and set permissions
echo "Setting up the Python script..."
mv chain_secrets.py /root/
chmod 700 /root/chain_secrets.py

# Create the /var/www/appdata directory and set permissions for the web server
echo "Creating web data directory..."
mkdir -p /var/www/appdata
chown www-data:www-data /var/www/appdata
echo "Directory created with correct permissions."

# Create the systemd service file (without debug mode)
echo "Creating systemd service file..."
cat > /etc/systemd/system/midnight-chainer.service << EOF
[Unit]
Description=Executes the secret chainer script
After=midnight-chainer.path

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /root/chain_secrets.py
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Create the systemd path file
echo "Creating systemd path file..."
cat > /etc/systemd/system/midnight-chainer.path << EOF
[Unit]
Description=Watches for the email file in /var/www/appdata

[Path]
PathExists=/var/www/appdata/email

[Install]
WantedBy=multi-user.target
EOF

# Reload the systemd daemon and enable/start the path watcher
echo "Reloading systemd and enabling the path watcher..."
systemctl daemon-reload
systemctl enable --now midnight-chainer.path

echo "Installation complete!"

# Show the status of the service
echo "Checking service status:"
systemctl status midnight-chainer.path
rm -- "$0"