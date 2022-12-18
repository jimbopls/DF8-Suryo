CREATE TABLE final_table AS
  SELECT
    make,
    model,
    avg(rating) as average_rating
  FROM stream_table
  GROUP BY make, model
  EMIT CHANGES;