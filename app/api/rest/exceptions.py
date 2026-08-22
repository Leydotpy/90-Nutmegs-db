from rest_framework.exceptions import _get_error_details


class ApplicationError(Exception):
    default_message = "Application Error"

    def __init__(self, message=None):
        if not message:
            self.message = self.default_message
        self.message = message

    def __str__(self):
        return str(self.message)


class ModuleNotFoundError(Exception):
    pass


class AppNotFoundError(Exception):
    pass


class ClassNotFoundError(Exception):
    pass


class ValidationError(ApplicationError):
    def __init__(self, message):
        self.message = message


class MembershipPermissionError(ApplicationError):
    pass


class InsufficientParametersError(ApplicationError):
    default_message = "Required fields are missing"


class ObjectDoesNotExist(ApplicationError):
    default_message = "Object does not exist"


class FieldError(Exception):
    default_code = "field_error"

    def __init__(self, detail, code=None):
        if code is None:
            code = self.default_code

        self.code = code
        self.detail = _get_error_details(detail, code)
        super(FieldError, self).__init__(self.detail)
