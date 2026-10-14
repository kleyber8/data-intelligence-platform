{{ config(materialized='table', tags=['gold', 'marts']) }}

WITH port_reference AS (
    SELECT * FROM (VALUES
        ('USLAX', 'Port of Los Angeles',   'US',  33.7405, -118.2775),
        ('USNYC', 'Port of New York',      'US',  40.6892,  -74.0445),
        ('NLRTM', 'Port of Rotterdam',     'NL',  51.9500,    4.1333),
        ('SGSIN', 'Port of Singapore',     'SG',   1.2644,  103.8409),
        ('CNSHA', 'Port of Shanghai',      'CN',  31.2304,  121.4737),
        ('AEJEA', 'Jebel Ali Port',        'AE',  25.0122,   55.0622),
        ('DEHAM', 'Port of Hamburg',       'DE',  53.5459,    9.9683),
        ('BEANR', 'Port of Antwerp',       'BE',  51.2603,    4.4025),
        ('KRPUS', 'Port of Busan',         'KR',  35.1028,  129.0403),
        ('JPTYO', 'Port of Tokyo',         'JP',  35.6528,  139.8394),
        ('BRSSZ', 'Port of Santos',        'BR', -23.9535,  -46.3317),
        ('ZADUR', 'Port of Durban',        'ZA', -29.8700,   31.0300),
        ('AUSYD', 'Port of Sydney',        'AU', -33.8700,  151.2100),
        ('MYPKG', 'Port Klang',            'MY',   3.0000,  101.4000),
        ('INNSA', 'Jawaharlal Nehru Port', 'IN',  18.9500,   72.9500)
    ) AS t(port_id, port_name, country_code, latitude, longitude)
),

expanded AS (
    SELECT
        port_id,
        port_name,
        country_code,
        latitude,
        longitude,
        latitude  - 0.3 AS bbox_min_lat,
        longitude - 0.3 AS bbox_min_lon,
        latitude  + 0.3 AS bbox_max_lat,
        longitude + 0.3 AS bbox_max_lon,
        NOW() AS created_at
    FROM port_reference
)

SELECT * FROM expanded
