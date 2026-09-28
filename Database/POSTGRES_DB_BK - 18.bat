@echo off


REM "Set following backup parameters to take backup"
SET PGPASSWORD=postgres
SET db_name=HEALTH_PACS
SET file_format=c
SET host_name=localhost
SET port_number=5434
SET user_name=postgres
SET pg_dump_path=C:\PROGRA~1\PostgreSQL\18\bin\pg_dump.exe
SET target_backup_path=E:\Progetti\Python\HealthPACS\Database\
SET other_pg_dump_flags=--blobs --verbose -c 

REM Fetch Current System Date and set month,day and year variables
   for /f "tokens=1-4 delims=/ " %%i in ("%date%") do (
     set day=%%i
     set month=%%j
     set year=%%k
   )

for /f "tokens=1-3 delims=: " %%i in ("%time%") do (
	set hour=%%i
	set min=%%j
	set sec=%%k
)


REM Creating string for backup file name
for /f "delims=" %%i in ('dir "%target_backup_path%" /b/a-d ^| find /v /c "::"') do set count=%%i
set /a count=%count%+1 
set datestr=%year%%month%%day%%hour%%min%

REM Backup File name
set BACKUP_FILE=%db_name%_%datestr%.dump

REM :> Executing command to backup database
%pg_dump_path% -h %host_name% --port=%port_number% -U %user_name% --format=%file_format%  %other_pg_dump_flags% -f "%target_backup_path%%BACKUP_FILE%"  %db_name%
pause
