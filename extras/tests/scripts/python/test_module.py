from procsync.modules import logger as log

class TestModule:
    def with_success(self, process, action_value, *args, **kwargs):
        log.info("Execute method with_success!")
        return (None, 0,  "Success")

    def error_with_retry(self, process, action_value, *args, **kwargs):
        log.info("Retry [%s]!" % action_value[6])
        return (None, 2,  "Test retrying")
        
    def with_error(self, process, action_value, *args, **kwargs):
        log.info("Error Message!")
        return (None, 3,  "Test of error")
