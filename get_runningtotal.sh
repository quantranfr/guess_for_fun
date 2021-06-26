rm tmp*
sqlite3 < clan_users.sql > tmp_users
while read -r line
do
	user_id=`echo $line | awk -F '|' '{print $1}'`
	username=`echo $line | awk -F '|' '{print $2}'`
	sed "s/ParamToBeReplaced/$user_id/" clan_progression.sql > tmp
	sqlite3 < tmp | cut -d "|" -f 3 > tmp2
	sed "1s/^/$username\n/" tmp2 > tmp_each_$username
done < tmp_users
paste -d , tmp_each* > clan_progression.csv
rm tmp*
