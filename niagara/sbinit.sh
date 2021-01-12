#!/bin/bash 

# Parse options to the `sbinit`
while getopts ":h" option; do
	case ${option} in
		h) #display help
			echo "Usage:"
			echo "	sbinit -h							Display help message"
			echo "	sbinit array						Generate sbatch array job script"
			exit 0
			;;
		\? ) 
			echo "Invalid option -$OPTARG" 1>&2
			exit 1
			;;
	esac
done
shift $((OPTIND -1))

sbatch_header (){
	# get parameters
	nodes=${1:-1}
	time=${2:-4}
	time=$(($time * 3600))
	time=`date -u -r $time +%T`
	job_name=${3:-"sbatch_job"}
	echo "#!/bin/bash"
	echo "#SBATCH --nodes=${nodes}"
	echo "#SBATCH --time=${time}"
	echo "#SBATCH --job-name ${job_name}"
}

usage_array (){
	echo "Usage:"
	echo "	sbinit array [-j JOBNAME] [-l LENGTH] [-n NODES] [-t TIME]"
	echo "Description:"
	echo "	-j, JOBNAME,	name of the sbatch job."
	echo "	-l, LENGTH,	length of job array."
	echo "	-n, NODES,	nodes required for each job."
	echo "	-t, TIME,	time limit for each job."
}


job_name=""
array_len=1
nodes=""
job_time=""

subcommend=$1; shift # Remove 'sbinit' from the argument list
case "$subcommend" in
	# Parse options to the 'array' sub commend
	array)
		while getopts ":hj:l:n:t:" option; do
			case ${option} in
				h )
					usage_array
					exit 0
					;;
				j ) # job names
					job_name=$OPTARG
					;;
				l ) # number of jobs in the array
					array_len=$OPTARG
					;;
				n ) # number of nodes required
					nodes=$OPTARG
					;;
				t ) # time limit for the job
					job_time=$OPTARG
					;;
				\? )
					echo "Invalid Option:  -$OPTARG" 1>&2
					exit 1
					;;
				: )
					echo "Invalid Option: -$OPTARG requires an argument" 1>&2
					exit 1
					;;
			esac
		done
		shift $((OPTIND -1))
		sbatch_header $nodes $job_time $job_name
		echo "#SBATCH --array=1-${array_len}%20"
		;;
	sbatch)
		sbatch_header
		;;
esac

