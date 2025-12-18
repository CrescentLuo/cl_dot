#!/bin/bash

# Deploy bashrc configuration script

# Install starship if needed
if ! command -v starship &> /dev/null; then
    echo "Installing starship..."
    mkdir -p ~/.local/bin
    curl -sS https://starship.rs/install.sh | sh -s -- -b ~/.local/bin
    
    # Wait for installation to complete and verify
    if command -v starship &> /dev/null; then
        echo "starship installed successfully: $(starship --version)"
    else
        echo "starship installation failed"
        exit 1
    fi
else
    echo "starship is installed: $(starship --version)"
fi


# Setup paths
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${HOME}/.config_backups"
mkdir -p "${BACKUP_DIR}"

# Setup starship theme
STARSHIP_CONFIG_DIR="${HOME}/.config"
mkdir -p "${STARSHIP_CONFIG_DIR}" && touch "${STARSHIP_CONFIG_DIR}/starship.toml"
if [ -f "${SOURCE_DIR}/gruvbox-rainbow.toml" ]; then
    echo "Deploying starship theme..."
    cp "${SOURCE_DIR}/gruvbox-rainbow.toml" "${STARSHIP_CONFIG_DIR}/starship.toml"
else
    echo "Warning: gruvbox-rainbow.toml not found"
fi



# Function to deploy config file
deploy_file() {
    local source="${SOURCE_DIR}/$1"
    local dest="${HOME}/.$1"
    
    [ -f "${dest}" ] && cp "${dest}" "${BACKUP_DIR}/$1.$(date +%Y%m%d_%H%M%S)"
    
    if [ -f "${source}" ]; then
        echo "Deploying .$1"
        cp "${source}" "${dest}"
    else
        echo "Warning: $1 not found"
        [ "$2" = "required" ] && exit 1
    fi
}

# Deploy configuration files
deploy_file "bash_profile"
deploy_file "bash_aliases"
deploy_file "bashrc" "required"

echo "Deployment complete! Run 'source ~/.bash_profile && source ~/.bashrc' to apply changes"
