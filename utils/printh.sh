#!/bin/bash
ph_delimiter=" "
ph_firstline="no"
while getopts "d:hi:f" option; do
	case ${option} in 
		h ) # display help
			echo "Usage:"
			echo -e "\tprinth file\t\tprint the header the file."
			echo -e "\tprinth -h\t\tdisplay the help message."
			echo -e "\tprinth -d delimiter\tset delimiter, default delimiter is space."
			echo -e "\tprinth -f\t\tdisplay header and the first line."
			exit 0
			;;
		d )
			ph_delimiter=$OPTARG;
      		;;
		f )
			ph_firstline="yes"
			;;
	esac
done
shift $((OPTIND -1))

file=$1;shift
if [[ "$ph_firstline" == "yes" ]];
then
	firstline=`sed -n 2p $file`
	head -n1 $file | awk -F "$ph_delimiter" -v delimiter="$ph_delimiter" -v firstline="$firstline" '{OFS="\t";split(firstline,a,delimiter);for(i=1;i<=NF;i++){print i,$i,a[i]}}'
else
	head -n1 $file | awk -F "$ph_delimiter" '{OFS="\t";for(i=1;i<=NF;i++){print i,$i}}'
fi

