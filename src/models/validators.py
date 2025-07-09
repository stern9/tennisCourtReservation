# ABOUTME: Custom validators for tennis booking system data validation
# ABOUTME: Validates dates, times, courts, and credentials with clear error messages

import re
from datetime import datetime
from typing import Any, List
from pydantic import validator


class ValidationError(Exception):
    """Custom validation error with detailed messages"""
    pass


class DateValidator:
    """Validates date formats and ranges"""
    
    @staticmethod
    def validate_date_format(value: str) -> str:
        """Validate YYYY-MM-DD format"""
        if not isinstance(value, str):
            raise ValidationError("Date must be a string")
        
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, value):
            raise ValidationError("Date must be in YYYY-MM-DD format")
        
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Invalid date value")
        
        return value
    
    @staticmethod
    def validate_future_date(value: str) -> str:
        """Validate that date is in the future"""
        DateValidator.validate_date_format(value)
        
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        if date_obj.date() <= datetime.now().date():
            raise ValidationError("Date must be in the future")
        
        return value


class TimeValidator:
    """Validates time slot formats"""
    
    @staticmethod
    def validate_time_slot(value: str) -> str:
        """Validate time slot format: 'De HH:MM AM/PM a HH:MM AM/PM'"""
        if not isinstance(value, str):
            raise ValidationError("Time slot must be a string")
        
        pattern = r'^De \d{2}:\d{2} (AM|PM) a \d{2}:\d{2} (AM|PM)$'
        if not re.match(pattern, value):
            raise ValidationError("Time slot must be in format 'De HH:MM AM/PM a HH:MM AM/PM'")
        
        # Extract start and end times
        parts = value.split(' a ')
        if len(parts) != 2:
            raise ValidationError("Invalid time slot format")
        
        start_time = parts[0].replace('De ', '')
        end_time = parts[1]
        
        # Validate time format
        try:
            start_dt = datetime.strptime(start_time, '%I:%M %p')
            end_dt = datetime.strptime(end_time, '%I:%M %p')
        except ValueError:
            raise ValidationError("Invalid time format in time slot")
        
        # Validate end time is after start time
        if end_dt <= start_dt:
            raise ValidationError("End time must be after start time")
        
        return value


class CourtValidator:
    """Validates court IDs and availability"""
    
    VALID_COURTS = [1, 2]
    
    @staticmethod
    def validate_court_id(value: int) -> int:
        """Validate court ID is in allowed list"""
        if not isinstance(value, int):
            raise ValidationError("Court ID must be an integer")
        
        if value not in CourtValidator.VALID_COURTS:
            raise ValidationError(f"Court ID must be one of: {CourtValidator.VALID_COURTS}")
        
        return value
    
    @staticmethod
    def validate_court_list(value: List[int]) -> List[int]:
        """Validate list of court IDs"""
        if not isinstance(value, list):
            raise ValidationError("Court list must be a list")
        
        if not value:
            raise ValidationError("Court list cannot be empty")
        
        validated_courts = []
        for court in value:
            validated_courts.append(CourtValidator.validate_court_id(court))
        
        return validated_courts


class CredentialValidator:
    """Validates usernames and passwords"""
    
    @staticmethod
    def validate_username(value: str) -> str:
        """Validate username format and length"""
        if not isinstance(value, str):
            raise ValidationError("Username must be a string")
        
        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(value) > 50:
            raise ValidationError("Username cannot be longer than 50 characters")
        
        # Allow alphanumeric and common special characters
        pattern = r'^[a-zA-Z0-9._-]+$'
        if not re.match(pattern, value):
            raise ValidationError("Username can only contain letters, numbers, dots, underscores, and hyphens")
        
        return value
    
    @staticmethod
    def validate_password(value: str) -> str:
        """Validate password strength"""
        if not isinstance(value, str):
            raise ValidationError("Password must be a string")
        
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if len(value) > 128:
            raise ValidationError("Password cannot be longer than 128 characters")
        
        # Check for at least one uppercase, lowercase, and digit
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', value):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', value):
            raise ValidationError("Password must contain at least one digit")
        
        return value


class EmailValidator:
    """Validates email addresses"""
    
    @staticmethod
    def validate_email(value: str) -> str:
        """Validate email format"""
        if not isinstance(value, str):
            raise ValidationError("Email must be a string")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValidationError("Invalid email format")
        
        if len(value) > 254:
            raise ValidationError("Email cannot be longer than 254 characters")
        
        return value


# Pydantic validators for use in models
def validate_date_format(cls, v):
    """Pydantic validator for date format"""
    try:
        return DateValidator.validate_date_format(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_future_date(cls, v):
    """Pydantic validator for future date"""
    try:
        return DateValidator.validate_future_date(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_time_slot(cls, v):
    """Pydantic validator for time slot"""
    try:
        return TimeValidator.validate_time_slot(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_court_id(cls, v):
    """Pydantic validator for court ID"""
    try:
        return CourtValidator.validate_court_id(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_court_list(cls, v):
    """Pydantic validator for court list"""
    try:
        return CourtValidator.validate_court_list(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_username(cls, v):
    """Pydantic validator for username"""
    try:
        return CredentialValidator.validate_username(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_password(cls, v):
    """Pydantic validator for password"""
    try:
        return CredentialValidator.validate_password(v)
    except ValidationError as e:
        raise ValueError(str(e))


def validate_email(cls, v):
    """Pydantic validator for email"""
    try:
        return EmailValidator.validate_email(v)
    except ValidationError as e:
        raise ValueError(str(e))