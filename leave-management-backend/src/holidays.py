from datetime import date, timedelta
from dateutil.easter import easter
import calendar

def get_kenyan_public_holidays(year):
    """
    Get list of Kenyan public holidays for a given year
    Returns a set of date objects
    """
    holidays = set()
    
    # Fixed holidays
    holidays.add(date(year, 1, 1))   # New Year's Day
    holidays.add(date(year, 5, 1))   # Labour Day
    holidays.add(date(year, 6, 1))   # Madaraka Day
    holidays.add(date(year, 10, 10)) # Huduma Day (formerly Moi Day)
    holidays.add(date(year, 10, 20)) # Mashujaa Day (Heroes' Day)
    holidays.add(date(year, 12, 12)) # Jamhuri Day
    holidays.add(date(year, 12, 25)) # Christmas Day
    holidays.add(date(year, 12, 26)) # Boxing Day
    
    # Variable holidays (approximations - in practice these would be determined by religious authorities)
    # Good Friday (Friday before Easter Sunday)
    easter_date = get_easter_date(year)
    good_friday = easter_date - timedelta(days=2)
    holidays.add(good_friday)
    
    # Easter Monday (Monday after Easter Sunday)
    easter_monday = easter_date + timedelta(days=1)
    holidays.add(easter_monday)
    
    # Eid ul-Fitr and Eid ul-Adha (Islamic holidays - dates vary each year)
    # These would need to be looked up from Islamic calendar
    # For now, we'll add placeholder dates (these should be updated annually)
    
    return holidays

def get_easter_date(year):
    """
    Calculate Easter date for a given year using the algorithm
    """
    # Algorithm to calculate Easter date
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    n = (h + l - 7 * m + 114) // 31
    p = (h + l - 7 * m + 114) % 31
    
    return date(year, n, p + 1)

def is_public_holiday(check_date):
    """
    Check if a given date is a public holiday in Kenya
    """
    holidays = get_kenyan_public_holidays(check_date.year)
    return check_date in holidays

def get_next_working_day(start_date, exclude_weekends=True):
    """
    Get the next working day after the given date
    """
    next_day = start_date + timedelta(days=1)
    holidays = get_kenyan_public_holidays(next_day.year)
    
    while True:
        # Check if it's a weekend (if we're excluding weekends)
        if exclude_weekends and next_day.weekday() >= 5:  # Saturday or Sunday
            next_day += timedelta(days=1)
            continue
            
        # Check if it's a public holiday
        if next_day in holidays:
            next_day += timedelta(days=1)
            continue
            
        # It's a working day
        return next_day