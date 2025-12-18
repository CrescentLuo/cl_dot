# Path management
export PATH="$HOME/.local/bin:$PATH"

# Set starship init and config
eval "$(starship init bash)"

# Load aliases

[[ -f ~/.bash_aliases ]] && source ~/.bash_aliases

LC_CTYPE=en_US.UTF-8
LC_ALL=en_US.UTF-8