# Dot Files

CL_DOT provides dot files and my freaquently used scripts.

ToDo list:
- [ ] ls color settings

## Dependencies 
1. Nerd Font [FiraCode Nerd Font](https://www.nerdfonts.com/font-downloads)
2. Starship [github](https://github.com/starship/starship)

## utils

1. **printf.sh** script to print header infomation of a file.
2. **shepherd.sh** script to control parelle execution of jobs.

## Niagara

1. **sbinit** script for sbatch job submission script header generation

## tmux configure



## bash configure


## OSS utils 

```bash
ossutil ls oss_path -e endpoint -i accessKeyID -k accessKeySecret
ossutil cp -rfu oss_path local_dir  -e endpoint -i accessKeyID -k accessKeySecret
```

## Addons

1. **opencode-addon-mesh** internal addon utility binary.
2. **opencode-addon-lattice** internal addon utility binary.

Notes:

1. These binaries are intended for internal addon workflows.
2. Implementation details are not documented in this README.
