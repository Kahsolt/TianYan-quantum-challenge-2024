@REM run circuit optimize algorithms
@ECHO OFF

REM GOTO reduce
REM GOTO pyzx
GOTO fuse


:reduce
ECHO [Run reduce]
FOR /L %%I IN (0,1,9) DO (
  ECHO sample-%%I
  python opt_qcir_reduce.py -I %%I
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
python verify_solut.py
ECHO.


:EOF
