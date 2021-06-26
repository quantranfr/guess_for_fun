.open db.sqlite3
--.headers ON
WITH scores AS (
SELECT
  match_id
  , user_id
  , s1, s2, ps1, ps2
  , pts8*8 + pts5*5 + pts4*4 + pts3*3 AS match_score
FROM (
  select
    match_id
    , user_id
    , s1, s2, ps1, ps2
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND s1!=ps1 AND s2!=ps2 AND s1-s2!=ps1-ps2 AS pts3
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND ((s1=ps1 AND s2!=ps2) OR (s2=ps2 AND s1!=ps1)) AS pts4
    , s1-s2=ps1-ps2 AND s1!=ps1 AS pts5
    , s1=ps1 AND s2=ps2 AS pts8
  FROM (
    select
      m.id AS match_ID
      , m.main_score_1 AS s1
      , m.main_score_2 AS s2
      , p.user_id AS user_id
      , p.main_score_1 AS ps1
      , p.main_score_2 AS ps2 
    from football_match m
    join football_prediction p on m.id = p.match_id
    where p.user_id in (select user_id from football_user_clan where clan_id=5)
    order by start_time, m.id
  )
)
)

--SELECT * from scores
SELECT m.id, s.match_score
  , sum(s.match_score) OVER (ORDER BY m.start_time, m.id) AS runningtotal
FROM (SELECT id, start_time FROM football_match ORDER BY start_time) m
LEFT JOIN (SELECT * FROM scores WHERE user_id=ParamToBeReplaced) s on m.id = s.match_id
--LEFT JOIN (SELECT * FROM scores WHERE user_id=34) s on m.id = s.match_id
