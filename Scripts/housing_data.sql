CREATE TABLE IF NOT EXISTS public.housing_raw_data
(
    id integer NOT NULL DEFAULT nextval('housing_raw_data_id_seq'::regclass),
    housing_data jsonb,
    CONSTRAINT housing_raw_data_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS housing_data_clean AS
SELECT
    housing_data->>'id'                                AS id,
    (housing_data->>'area')::int                        AS area,
    (housing_data->>'beds')::int                         AS beds,
    (housing_data->>'baths')::numeric                    AS baths,
    (housing_data->>'price')::numeric                    AS price,
    housing_data->>'status'                             AS status,
    housing_data->>'homeType'                           AS home_type,
    (housing_data->>'latitude')::numeric                 AS latitude,
    (housing_data->>'longitude')::numeric                AS longitude,
    (housing_data->>'zestimate')::numeric                AS zestimate,
    housing_data->>'addressRaw'                         AS address_raw,
    housing_data->>'brokerName'                         AS broker_name,
    housing_data->>'brokerNameRaw'                      AS broker_name_raw,
    (housing_data->>'daysOnZillow')::int                 AS days_on_zillow,
    housing_data->>'lotAreaUnits'                       AS lot_area_units,
    (housing_data->>'lotAreaValue')::numeric             AS lot_area_value,
    (housing_data->>'rentZestimate')::numeric            AS rent_zestimate,
    -- nested: address
    housing_data#>>'{address,city}'                     AS city,
    housing_data#>>'{address,state}'                    AS state,
    housing_data#>>'{address,street}'                   AS street,
    housing_data#>>'{address,zipcode}'                  AS zipcode,
	(housing_data->>'beds')::int+ (housing_data->>'baths')::numeric					AS Room_Count
FROM housing_raw_data;