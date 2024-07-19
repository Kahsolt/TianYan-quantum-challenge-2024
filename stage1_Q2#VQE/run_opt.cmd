@REM run circuit optimize algorithms
@ECHO OFF

REM GOTO pennylane
REM GOTO pyzx
REM GOTO fuse


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
  python opt_qcir_pyzx.py -I %%I
)
ECHO.


:fuse
ECHO [Run fuse]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_vqcir.py -I %%I
)
ECHO.


:EOF
