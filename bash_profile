
#Load shell dotfiles:
for file in ~/.{bashrc,exports,bash_aliases}; do
    [   -r "$file" ] && [ -r "$file" ] && source "$file"
done;
unset file;

# Autocorrect typos in path names when using `cd`
shopt -s cdspell;
