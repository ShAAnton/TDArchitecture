from datetime import date, timedelta
from model import *
import pytest

today = date.today()
tomorrow = today + timedelta(days=1)
later = today + timedelta(days=10)
