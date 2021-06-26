.open db.sqlite3
--.headers ON
select u.id, u.username
from auth_user u
join football_user_clan uc on u.id = uc.user_id
where uc.clan_id=5 
