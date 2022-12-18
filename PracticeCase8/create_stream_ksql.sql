CREATE STREAM stream_table (
    driver_id INTEGER,
    make STRING,
    model STRING,
    year INTEGER,
    license_plate STRING,
    rating DOUBLE
)
WITH (kafka_topic='jdbc_driver_profiles', value_format='json', partitions=1, key='driver_id');