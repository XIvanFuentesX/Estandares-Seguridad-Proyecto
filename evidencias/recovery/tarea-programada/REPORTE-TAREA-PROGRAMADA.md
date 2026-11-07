# Reporte de la tarea programada de recuperación periódica

Fecha: 2026-10-24. Autorización: expresa del usuario para registrar esta tarea en el Programador de tareas de Windows. Riesgos tratados: R-005, R-006, R-007, R-019 (controles A.8.13, A.5.30).

## 1. Definición registrada

| Atributo | Valor |
|---|---|
| Nombre | `SGSI-UVCG-Prueba-Recuperacion` |
| Disparador | Semanal, domingos a las 10:00 (hora local de Windows); próxima ejecución 2026-10-25 10:00 |
| Cuenta | Usuario actual, `LogonType Interactive` (sólo con sesión iniciada); **no se almacenan credenciales** |
| Nivel | `RunLevel Limited` (sin elevación; Windows no la solicitó) |
| Instancias | `MultipleInstances IgnoreNew` + mutex `Local\SGSI-UVCG-Prueba-Recuperacion` en el script |
| Tiempo límite | 30 minutos |
| Ejecución perdida | `StartWhenAvailable`: si el equipo estaba apagado, se ejecuta al estar disponible |
| Acción | `powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File scripts\tarea_recuperacion_programada.ps1` (la política de ejecución sólo cambia para ese proceso) |
| Definición exportada | `definicion-tarea.xml` |

## 2. Comportamiento del script

- Comprueba Docker con `docker info` (límite de 45 s). Si no responde, registra `no_verificable` y añade `target=recovery-test result=failure reason=docker_unavailable` a la bitácora de backups (alerta SIEM-BACKUP-001).
- Ejecuta `prueba_recuperacion_periodica.ps1`: verifica los schedulers y el SHA-256, y restaura ambas bases **sólo** en `restore-db` e `identity-restore-db` (red `recovery` interna). Nunca usa los servicios `db` ni `identity-db` como destino y no borra bases, volúmenes ni respaldos (las bases restauradas se conservan).
- Registra la fecha, la hora de inicio y fin, la duración, el resultado (`exitoso`/`fallido`/`omitido`/`no_verificable`), el detalle y la evidencia en `ejecuciones.csv` y en `ejecucion-<fecha>.json`.
- No imprime secretos: los scripts de Docker leen `local/.env`, pero sólo registran nombres de archivo, hashes y conteos.

## 3. Pruebas realizadas

| Prueba | Resultado | Duración |
|---|---|---|
| Ejecución manual del script | exitoso (restauración dual, dentro del RTO, 2 brechas de RPO informadas) | 19.2 s |
| Dos ejecuciones simultáneas | A: exitoso; B: `omitido` por el mutex | 18.8 s / 0 s |
| Docker no disponible (simulado con `DOCKER_HOST` inválido sólo en ese proceso) | `no_verificable`, alerta registrada; Docker real intacto | 0.2 s |
| Ejecución desde el Programador de tareas (`Start-ScheduledTask`) | `LastTaskResult = 0`, exitoso | 20.1 s |

## 4. Limitaciones

- Docker Desktop corre en la sesión del usuario: la tarea **sólo funciona con la sesión iniciada** y Docker Desktop abierto. Sin sesión no se ejecuta; con sesión pero sin motor, registra `no_verificable`.
- Cada ejecución conserva 2 bases restauradas en los volúmenes aislados (unos pocos MB por semana, con datos de identidad). Su limpieza requiere autorización expresa (`-DropRestoredDatabase`).
- Revertir el registro: `Unregister-ScheduledTask -TaskName SGSI-UVCG-Prueba-Recuperacion` (no afecta datos).
