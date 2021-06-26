.headers ON
WITH scores AS (
SELECT
  match_id
  , user_id
  , s1, s2, ps1, ps2
  , (pts8*8 + pts5*5 + pts4*4 + pts3*3)*coef_phase AS match_score
FROM (
  select
    match_id
    , CASE phase
        WHEN 'group' THEN 1
        ELSE 2
      END coef_phase
    , user_id
    , s1, s2, ps1, ps2
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND s1!=ps1 AND s2!=ps2 AND s1-s2!=ps1-ps2 AS pts3
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND ((s1=ps1 AND s2!=ps2) OR (s2=ps2 AND s1!=ps1)) AS pts4
    , s1-s2=ps1-ps2 AND s1!=ps1 AS pts5
    , s1=ps1 AND s2=ps2 AS pts8
  FROM (
    select
      m.id AS match_id
      , m.phase
      , m.main_score_1 AS s1
      , m.main_score_2 AS s2
      , p.user_id AS user_id
      , p.main_score_1 AS ps1
      , p.main_score_2 AS ps2
    from football_match m
    join football_prediction p on m.id = p.match_id
    where p.user_id in (select user_id from football_user_clan where clan_id=:clan_id)
    order by start_time, m.id
  )
)
)

SELECT m.id, s.match_score
  , sum(s.match_score) OVER (ORDER BY m.start_time, m.id) AS running_total
FROM (SELECT id, start_time FROM football_match ORDER BY start_time) m --get complete list of matches
LEFT JOIN (SELECT * FROM scores WHERE user_id=:user_id) s on m.id = s.match_id
