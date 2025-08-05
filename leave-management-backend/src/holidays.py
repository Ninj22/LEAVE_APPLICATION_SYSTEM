from datetime import date, timedelta
from dateutil.easter import easter

def get_kenyan_public_holidays(year):
    holidays = [
        date(year, 1, 1),  # New Year's Day
        date(year, 5, 1),  # Labour Day
        date(year, 6, 1),  # Madaraka Day
        date(year, 10, 20), # Mashujaa Day
        date(year, 12, 12), # Jamhuri Day
        date(year, 12, 25), # Christmas Day
        date(year, 12, 26), # Boxing Day
    ]

    # Calculate Easter holidays
    e = easter(year)
    holidays.append(e - timedelta(days=2)) # Good Friday
    holidays.append(e + timedelta(days=1)) # Easter Monday

    # Handle holidays falling on a weekend (observed on next Monday)
    # This is a common practice but might need to be confirmed for Kenya
    # For simplicity, we'll add this logic for now.
    # A more robust solution might involve checking official gazettes.
    adjusted_holidays = []
    for h in holidays:
        if h.weekday() == 5: # Saturday
            adjusted_holidays.append(h + timedelta(days=2))
        elif h.weekday() == 6: # Sunday
            adjusted_holidays.append(h + timedelta(days=1))
        else:
            adjusted_holidays.append(h)

    return sorted(list(set(adjusted_holidays))) # Remove duplicates and sort