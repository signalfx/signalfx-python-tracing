drop database if exists `test_db`;
create database `test_db` DEFAULT CHARACTER SET utf8mb4;

drop user if exists 'test_user';
create user 'test_user'@'%' identified by 'test_password';
grant all on test_db.* TO 'test_user'@'%';

use test_db;
drop table if exists `table_one`;
create table `table_one` (
    `string_one` varchar(64) not null,
    `string_two` varchar(64),
    `datetime_one` datetime not null,
    `datetime_two` datetime,
    primary key (`string_one`)
);

drop table if exists `table_two`;
create table `table_two` (
    `int_one` int(10) not null,
    `int_two` int(10),
    `float_one` float(11,4) not null,
    `float_two` float(11,4),
    primary key (`int_one`)
);

delimiter $$
create procedure test_procedure_one()
begin
    select * from table_one, table_two;
end$$

create procedure test_procedure_two()
begin
    select * from table_one, table_two;
end$$
delimiter ;
