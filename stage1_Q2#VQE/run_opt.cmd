@REM run circuit optimize algorithms
@ECHO OFF

REM GOTO pennylane
GOTO pyzx


:cqlib
ECHO [Run cqlib]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_cqlib.py -I %%I
)
ECHO.


:pennylane
ECHO [Run pennylane]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pennylane.py -I %%I
)
ECHO.


:pyzx
ECHO [Run pyzx]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pyzx.py -I %%I --save
)
ECHO.


:EOF
