@echo off
echo Installing Django and MySQL dependencies...

:: Install Django
pip install django

:: Ensure pip is installed and upgraded
python -m ensurepip --upgrade

:: Install MySQL client (for MySQL database support)
pip install mysqlclient

:: Install for excel library
pip install openpyxl

:: Install time manager for django
pip install pytz tzdata



echo Installation complete!
pause
