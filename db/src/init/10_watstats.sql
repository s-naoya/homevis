CREATE TABLE wattstats(
    datetime timestamp PRIMARY KEY,
    dow text NOT NULL,
    watt_usage double precision,
    watt_sold double precision
);
