from datetime import date
today = date.today()
year_int = int(today.year)


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': year_int,
    }
