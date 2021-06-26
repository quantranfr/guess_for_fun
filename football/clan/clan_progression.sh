#!/bin/bash
DB=$1
if [ -z "$DB" ]
then
      echo "No DB provided. Abort."
      exit 1
fi
SCRIPT_PATH=$(dirname ${BASH_SOURCE[0]})
cd $SCRIPT_PATH
sqlite3 $DB "select id from football_clan" | # get clans
  while read -r clan_id
  do # for each clan
    rm tmp* 2&>/dev/null
    sqlite3 $DB """select u.id, u.username
                   from auth_user u
                   join football_user_clan uc on u.id = uc.user_id
                   where uc.clan_id=$clan_id""" | # get users of clan x
      while read -r line
      do
        user_id=`echo $line | awk -F '|' '{print $1}'`
      	username=`echo $line | awk -F '|' '{print $2}'`
        sqlite3 $DB ".param init" ".param set :user_id $user_id" ".param set :clan_id $clan_id" ".read clan_progression.sql" | # 3 columns: match_id, match_score, running_total
          cut -d "|" -f 3 | # get the running_total column
          sed -e "s/running_total/$username/" > tmp_$username
      done
    paste -d , tmp_* > clan_progression_$clan_id.csv
    rm tmp* 2&>/dev/null
  done
exit 0
