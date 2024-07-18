@REM run circuit optimize algorithms
@ECHO OFF

REM GOTO pennylane-v
GOTO pyzx-v

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

:pennylane-v
ECHO [Run pennylane-v]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_vqcir_pennylane.py -I %%I
)
ECHO.

REM GOTO EOF

:pyzx-v
ECHO [Run pyzx-v]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_vqcir_pyzx.py -I %%I --save
)
ECHO.

:EOF
