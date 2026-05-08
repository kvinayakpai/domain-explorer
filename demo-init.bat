@echo off
REM Domain Explorer — Customer Accelerator demo runner.
REM
REM Defaults are picked for the most common BFSI / Snowflake / CDO demo. Edit
REM the line below if your prospect is in a different vertical.

setlocal
cd /d C:\Claude\domain-explorer

REM Clean any previous demo output so the run is a fresh 30-second show.
if exist "C:\Claude\demo-output" (
  echo Removing previous C:\Claude\demo-output ...
  rmdir /S /Q "C:\Claude\demo-output"
)

node packages\cli\bin\init.js demo-customer ^
  --vertical=bfsi ^
  --cloud=snowflake ^
  --persona=cdo ^
  --tagline="Banking, evolved." ^
  --output-dir=C:\Claude\demo-output

echo.
echo Demo clone is at C:\Claude\demo-output
echo.
endlocal
