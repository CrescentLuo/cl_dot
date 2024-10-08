eval "$(starship init zsh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

[[ -f ~/.zsh/aliases.zsh ]] && source ~/.zsh/aliases.zsh

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/zluo/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/zluo/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/zluo/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/zluo/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<


LC_CTYPE=en_US.UTF-8
LC_ALL=en_US.UTF-8
