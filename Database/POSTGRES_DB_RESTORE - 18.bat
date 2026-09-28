@echo off


REM "Set following restore parameters to take restore"
SET pg_create_db=C:\PROGRA~1\PostgreSQL\18\bin\createdb.exe
SET pg_restore_path=C:\PROGRA~1\PostgreSQL\18\bin\pg_restore.exe

SET options= -v --no-owner
SET host_name=localhost
SET user_name=postgres
SET port_number=5434
SET db_name=HEALTH_PACS
SET target_dump_path=D:\Projects\HealthPACS\Database\
SET dump_file_name=HEALTH_PACS_202609282003.dump

REM :> Executing command restore database
REM :createdb -h localhost -p 5432 -U postgres testdb
REM :pg_dump -Fc -v --host=192.168.120.33 --username=postgres --dbname=EnergyIS -f EnergyIS.dump

REM :cd "C:\Program Files\PostgreSQL\11\bin"
%pg_create_db% -h %host_name% -p %port_number% -U %user_name% %db_name%  
pause

REM cd "C:\Progetti Software\EnergyIS\develop\EnergyIS_BK_DB"
%pg_restore_path% %options% --host=%host_name% --port=%port_number% --username=%user_name% --dbname=%db_name%  %target_dump_path%%dump_file_name%
pause

