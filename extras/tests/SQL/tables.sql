SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

CREATE DATABASE `procsync_db1` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `procsync_db1`;

CREATE TABLE IF NOT EXISTS `origin` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `text` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `destination2` (
  `id` bigint(20) unsigned NOT NULL,
  `text` varchar(255) NOT NULL,
  `added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE DATABASE `procsync_db2` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `procsync_db2`;

CREATE TABLE IF NOT EXISTS `destination1` (
  `id` bigint(20) unsigned NOT NULL,
  `text` varchar(255) NOT NULL,
  `added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE DATABASE `procsync` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `procsync`;

CREATE TABLE IF NOT EXISTS `queue` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `action_name` varchar(64) NOT NULL,
  `from_column_value` varchar(50) NOT NULL,
  `server_name` varchar(45) DEFAULT NULL,
  `process_status` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `error_description` varchar(255) DEFAULT NULL,
  `process_retry` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `schedule` datetime DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_update_date` timestamp NULL DEFAULT NULL,
  `inserted_by` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Sync` (`server_name`, `process_status`,`schedule`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

