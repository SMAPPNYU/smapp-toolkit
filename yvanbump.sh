#!/bin/bash
# c* https://github.com/aaren/notedown/blob/master/release
# c* https://www.gnu.org/software/sed/manual/html_node/The-_0022s_0022-Command.html#The-_0022s_0022-Command

# create a helper function to join arrays
function join { local IFS="$1"; shift; echo "$*"; }

#get setup.py version
dirpath=`pwd -P`
currentversion=`python $dirpath/setup.py -V`
echo "old version: $currentversion"

# split the current version into 3 #s
# add one to the last number to bump it
IFS='.' read -a myarray <<< "$currentversion"
((myarray[2]=${myarray[2]}+1))

#join array elements back together
newversion=`join '.' "${myarray[@]}"`
echo "new version: $newversion"

#do an in place replace (should be portable linux <-> unix
sed -i -e "s/version=.*,/version='$newversion',/" setup.py

# get rid of old abckup file made by sed
rm 'setup.py-e'

#commit new files.
git commit -am "yvanbump :)"

# push to current branch
git push
