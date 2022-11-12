.headers ON
SELECT
  (pts8*8 + pts5*5 + pts4*4 + pts3*3)*coef_phase AS score
FROM (
  select
    CASE phase
      WHEN 'group' THEN 1
      ELSE 2
    END coef_phase
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND s1!=ps1 AND s2!=ps2 AND s1-s2!=ps1-ps2 AS pts3
    , ((s1>s2 AND ps1>ps2) OR (s1<s2 AND ps1<ps2)) AND ((s1=ps1 AND s2!=ps2) OR (s2=ps2 AND s1!=ps1)) AS pts4
    , s1-s2=ps1-ps2 AND s1!=ps1 AS pts5
    , s1=ps1 AND s2=ps2 AS pts8
  FROM (
    select
      m.id AS match_id
      , start_time
      , phase
      , m.main_score_1 AS s1
      , m.main_score_2 AS s2
      , p.main_score_1 AS ps1
      , p.main_score_2 AS ps2
    from football_match m
    join football_championship c on m.championship_id = c.id
    left join (
      select * from football_prediction where user_id=user_id_param
    ) p on m.id = p.match_id
    where c.name = 'World Cup 2022'
    order by start_time, m.id
  )
);
