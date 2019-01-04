drop schema if exists test_schema cascade;
create schema test_schema;
set schema 'test_schema';

drop table if exists table_one;
create table table_one (
    string_one varchar(64) primary key,
    string_two varchar(64),
    timestamp_one timestamp not null,
    timestamp_two timestamp
);

drop table if exists table_two;
create table table_two (
    int_one integer primary key,
    int_two integer,
    float_one decimal(11,4) not null,
    float_two decimal(11,4)
);

create type "test_type" as (
    string_one varchar(64),
    string_two varchar(64),
    timestamp_one timestamp,
    timestamp_two timestamp,
    int_one integer,
    int_two integer,
    float_one decimal(11,4),
    float_two decimal(11,4)
);

create or replace function test_function_one() returns test_type
    as 'select * from table_one, table_two;'
    language sql;

create or replace function test_function_two() returns test_type
    as 'select * from table_one, table_two;'
    language sql;


drop role if exists test_user;
create role test_user with login password 'test_password';

grant all privileges on database test_db TO test_user;
grant all privileges on schema test_schema TO test_user;
grant all privileges on all tables in schema test_schema TO test_user;
grant all privileges on all sequences in schema test_schema TO test_user;
