@REM run circuit optimize algorithms
@ECHO OFF

REM GOTO pennylane
REM GOTO pennylane-v
REM GOTO pyzx-v
GOTO pyzx-v-opt


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
  python opt_qcir_pennylane.py -I %%I --render
)
ECHO.

:pennylane-v
ECHO [Run pennylane-v]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pennylane.py -I %%I
)
ECHO.


:pyzx
ECHO [Run pyzx]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pyzx.py -I %%I --render
)
ECHO.

:pyzx-v
ECHO [Run pyzx-v]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pyzx.py -I %%I --save
)
ECHO.

:pyzx-v-opt
ECHO [Run pyzx-v-opt]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_pyzx.py -I %%I --save -M opt
)
ECHO.


:EOF
