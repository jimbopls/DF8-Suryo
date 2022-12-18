CREATE TABLE driver_profiles (
  driver_id integer PRIMARY KEY,
  make text,
  model text,
  year integer,
  license_plate text,
  rating float
);

INSERT INTO driver_profiles (driver_id, make, model, year, license_plate, rating) VALUES
  (0, 'Toyota', 'Prius',   2019, 'KAFKA-1', 5.00),
  (1, 'Kia',    'Sorento', 2017, 'STREAMS', 4.89),
  (2, 'Tesla',  'Model S', 2019, 'CNFLNT',  4.92),
  (3, 'Toyota', 'Camry',   2018, 'ILVKSQL', 4.85);