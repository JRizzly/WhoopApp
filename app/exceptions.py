# Copyright (c) 2014 Data Bakery LLC. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, this list of
# conditions and the following disclaimer.
# 
#     2. Redistributions in binary form must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other materials provided with
# the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY DATA BAKERY LLC ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DATA BAKERY LLC OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
l = logging.getLogger(__name__)

from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import Forbidden

class AppError(HTTPException):
    code = 400

    def to_json(self):
        return { 
            "description": self.description,
            "error_code": self.error_code
        }

class ConsistencyError(AppError):
    error_code = "CONSISTENCY"
    description = "Consistency error"


class DatabaseValueError(AppError):
    error_code = "DATABASE_VALUE"
    description = "Invalid database value"


class TimeoutError(AppError):
    error_code = "TIMEOUT"
    description = "Timeout"


class BackendError(AppError):
    code = 500
    error_code = "BACKEND_ERROR"
    description = "Backend error"


class ValidationError(AppError):
    error_code = "VALIDATION_ERROR"
    description = "Validation error"


class InternalError(AppError):
    error_code = "INTERNAL_ERROR"
    description = "Internal error"
    

class ForbiddenError(AppError):
    code = 403
    error_code = "FORBIDDEN"
    description = "Permission denied"


class NotFoundError(AppError):
    code = 404
    error_code = "NOT_FOUND"
    description = "Not found"


class AccountDisabled(AppError):
    code = 403
    error_code = "ACCOUNT_DISABLED"
    description = "Account disabled"

class AJAXTokenInvalidError(AppError):
    error_code = "AJAX_TOKEN_INVALID"
    description = "AJAX token invalid"

