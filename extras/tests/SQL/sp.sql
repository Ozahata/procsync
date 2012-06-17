DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync`.`ps_search_request`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync`.`ps_search_request`
(
    _server_name VARCHAR(45)
)
BEGIN
    -- Variables
    SET @rows_pool = 0;
    /*
    Check if have some process running, because the system can stop suddenly
        so need process again.
    This is to avoid get more one line to process if already have on line to
        be process.
    */
    SELECT COUNT(id) INTO @rows_pool 
      FROM queue
     WHERE server_name = _server_name
       AND ((process_status = 1
       AND schedule is NULL)
        OR (process_status = 2
       AND schedule < now()));
    /*
    If dont have a process running, get only one process so we need "lock" the
        row to process only by this server_name.
    */
    IF @rows_pool = 0
    THEN
       /*
       Get a row that process_status is in IDLE (0) and do not have a schedule
           or the schedule is already to be process.
       */
       UPDATE queue
          SET server_name = _server_name,
              process_status = 1,
              last_update_date = now()
        WHERE process_status = 0
          AND server_name is NULL
          AND (schedule is NULL
          OR schedule < now()) LIMIT 1;
    END IF; 

    SELECT id, action_name, from_column_value, server_name, process_status, 
           error_description, process_retry, schedule, created_date, 
           last_update_date, inserted_by
      FROM queue
     WHERE server_name = _server_name
       AND process_status < 3
       AND (schedule is NULL
        OR schedule < now())
     LIMIT 1;
END$$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync`.`ps_update_request`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync`.`ps_update_request` 
(
    _id BIGINT UNSIGNED,
    _process_status TINYINT UNSIGNED,
    _error_description varchar(255),
    _process_retry TINYINT UNSIGNED,
    _reprocess_time INT UNSIGNED
)
BEGIN
    -- Process status 0 means success. Remove from queue.
    IF _process_status = 0 
    THEN
        DELETE FROM queue
         WHERE id = _id;
    END IF;
    -- Process status 1 (Configuration error), 3 (System error). Set status 3.
    IF _process_status in (1, 3) 
    THEN
        UPDATE queue
           SET process_status = 3,
               error_description = _error_description,
               last_update_date = now()           
         WHERE id = _id;
    END IF;
    -- Process status 2 (Error inside action)
    -- Set status 2 (Reprocess) if not reach the limit, other else 3 (Error).
    IF _process_status = 2 
    THEN
        SET @server_process_status = 2, @reprocess=0;
        SELECT process_retry INTO @reprocess
          FROM queue
         WHERE id = _id;
        -- Check the reprocess
        IF @reprocess + 1 > _process_retry 
        THEN
            SET @server_process_status = 3;
        ELSE
            SET @reprocess = @reprocess + 1;
        END IF;
         
        UPDATE queue
           SET process_status = @server_process_status,
               error_description = _error_description,
               process_retry = @reprocess,
               schedule = DATE_ADD(now(), INTERVAL _reprocess_time SECOND),
               last_update_date = now()           
         WHERE id = _id;
    END IF;
END$$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync`.`ps_replicate_request`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync`.`ps_replicate_request` 
(
    _replicate_action VARCHAR(255),
    _id BIGINT UNSIGNED,
    _action_name VARCHAR(64),
    _from_column_value VARCHAR(50),
    _server_name VARCHAR(45),
    _process_status TINYINT UNSIGNED,
    _error_description VARCHAR(255),
    _process_retry TINYINT UNSIGNED,
    _schedule DATETIME,
    _created_date TIMESTAMP,
    _last_update_date TIMESTAMP,
    _inserted_by VARCHAR(255)
)
BEGIN
    INSERT INTO `queue` 
    (`action_name`, `from_column_value`, `server_name`, `process_status`, `error_description`, `process_retry`, `schedule`, `created_date`, `last_update_date`, `inserted_by`) 
    VALUES
    (_replicate_action,  _from_column_value, NULL, 0, NULL, _process_retry, _schedule, now(), now(), CONCAT('(ADD BY REPLICATED)', _inserted_by));
END$$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync_db1`.`sp_procsync_test_success`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync_db1`.`sp_procsync_test_success` 
(
    _from_column_value VARCHAR(36)
)
BEGIN
    INSERT INTO destination2 
    (`id`, `text`) 
    SELECT id, text
      FROM origin
     WHERE id = _from_column_value;
END$$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync_db1`.`sp_procsync_test_error`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync_db1`.`sp_procsync_test_error` 
(
    _from_column_value VARCHAR(36)
)
BEGIN
    INSERT INTO destination2 
    (`id`, `text`) 
    SELECT id, text
      FROM origin
     WHERE wrong_field = _from_column_value;
END$$

DELIMITER ;

DELIMITER $$

DROP PROCEDURE IF EXISTS `procsync_db1`.`sp_procsync_test_error_duplicate`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `procsync_db1`.`sp_procsync_test_error_duplicate` 
(
    _from_column_value VARCHAR(36)
)
BEGIN
    INSERT INTO destination2 
    (`id`, `text`) 
    VALUES
    (_from_column_value, 'CAN\'T INSERT');
END$$

DELIMITER ;
