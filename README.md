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

1. **opencode-addon-mesh** generates a single protected addon artifact from tracked files in a Git repository.
2. **opencode-addon-lattice** materializes files from a protected addon artifact.

Examples:

```bash
# create bundle under cl_dot/addons
opencode-addon-mesh --source /path/to/git/repo --name sample.mesh

# restore bundle to a target directory
opencode-addon-lattice --bundle /home/ubuntu/cl_dot/addons/sample.mesh --dest /tmp/sample_restore
```

Notes:

1. `--source` must point to a valid Git repository.
2. The mesh command includes tracked files only (`git ls-files`).
3. Password is required for both create and restore operations.
