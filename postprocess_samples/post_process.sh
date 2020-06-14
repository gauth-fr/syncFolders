#!/bin/bash

# When a file is copied thru SSH on th esynology the permissions set are linux permission, not Synology ACL.
# The file is also not indexed as it would be if you copied the file thru File Station for example
# This script :
#        - set Synology ACL (inherited from parents) to the file in parameter, including all the subdirectories in the filepath (because synoactltool is not recusive)
#        - start the file indexation (so it will appear, for example, in VideoStation
# $1 = file to process
# $2 = Base directory (from where the ACL should be inherited)

BASE_DIR=/volume1/video
if [ ! -z "$2" ] 
then
	if [ -d "$2" ]
	then
		BASE_DIR="$2"
	else 
		echo "$2 is not a valid directory!"
		exit 1
	fi
fi

#remove tailing / if there is one
BASE_DIR=${BASE_DIR%/}

#build a list of all subdirs in the path (from the nearest to BASE_DIR to the deepest
DIRs=""
DIR=$(dirname "$1")
while [[ $DIR != $BASE_DIR ]]
do
	DIRs="$DIR:$DIRs"
	DIR=$(dirname "$DIR")
done

# Inherit Syno ACL for each dir in the list
OLD_IFS=$IFS
IFS=':'
for i in $DIRs
do
	echo "Inherit permissions for $i"
	sudo /usr/syno/bin/synoacltool -enforce-inherit "$i" 
done 
IFS=$OLD_IFS

#Finally Inherit Syno ACL for the file
echo "Inherit permissions for $1"
sudo /usr/syno/bin/synoacltool -enforce-inherit "$1" 
echo "Force indexing $1"
synoindex -a "$1"


