class PCRAPIException(Exception):
    def __init__(self, message, status, result_code):
        super().__init__(message)
        self.message = message
        self.status = status
        self.result_code = result_code
