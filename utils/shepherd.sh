#!/bin/bash

function usage(){
	echo -e "Usage:"
	echo -e "\tshepherd -s SCRIPTS -n JOBNAME [-m MAXJOB]"
	echo -e "Description:"
	echo -e "\t-s, SCRIPTS,\tTarget scripts to monitor."
	echo -e "\t-n, JOBNAME,\tJom name for log file."
	echo -e "\t-m, MAXJOB,\tMax jobs"
}

while getopts ":hs:n:m:" opt; do
	case "$opt" in
		h)
			usage
			exit 0
			;;
		s)
			script=$OPTARG
			;;
		n)
			job_name=$OPTARG
			;;
		m)
			max_job=$OPTARG
			;;
		\?)
			echo "Invalid Option: -$OPTARG" 1>&2
			exit 1
			;;
	esac
done
shift $((OPTIND -1))
job_name=${job_name:-"shepherd_job"}


if [ -e ${job_name}.log ];then
    rm ${job_name}.log
fi
echo `date` "Run job list $job_name" >> ${job_name}.log
sleep 1

task_len=`wc -l $script | awk '{print $1}'`

max_jobs=${max_job:-4}
FIFO_FILE="./$$.fifo"
mkfifo $FIFO_FILE
exec 6<>$FIFO_FILE
rm -f $FIFO_FILE

for((i=1; i<=${max_jobs}; i++));do
    echo
done >&6


for((i=1; i<=${task_len}; i++));do
	read -u6
	{
		{
			cmd=`sed -n ${i}p $script`
			eval $cmd
			echo `date` "starting job ${i}">> ${job_name}.log 
		} && {
			echo `date` "finish job ${i}" >> ${job_name}.log
			sleep 1 
		} || {
            echo job ${i} error >> ${job_name}.log
        }
        echo >&6
    }& 
done

# wati for all jobs to complete
wait
exec 6>&-
