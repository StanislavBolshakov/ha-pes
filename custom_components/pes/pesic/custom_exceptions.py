class MissingArgumentError(ValueError):
    def __init__(self, msg: str = None):
        self.msg = msg


class UnsupportedArgumentError(ValueError):
    def __init__(self, msg: str = None):
        self.msg = msg


class UnsupportedMeterType(ValueError):
    def __init__(self, msg: str = None):
        self.msg = msg

class TokenError(Exception):
    def __init__(self, msg: str = None):
        self.msg = msg