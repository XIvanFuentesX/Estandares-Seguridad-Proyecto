# Procedimiento de investigación de alertas — laboratorio UVCG

## Alcance

Aplica a alertas del SIEM ligero y Suricata offline. No presupone capacidades IPS, EDR/XDR, captura en vivo ni atribución de una identidad real.

## Flujo

1. **Registrar:** asignar identificador, fecha, regla, severidad y analista. No copiar tokens, cookies o contraseñas.
2. **Validar:** consultar los eventos relacionados por origen, categoría y ventana temporal; confirmar que la regla coincide con evidencia y descartar pruebas autorizadas.
3. **Clasificar:** determinar si afecta autenticación, autorización, aplicación, base de datos, disponibilidad o red.
4. **Contener:** si existe riesgo activo, bloquear la cuenta o ruta mediante el propietario autorizado. No ejecutar acciones automáticas desde este SIEM demostrativo.
5. **Preservar:** copiar reportes saneados, hashes y marcas de tiempo; mantener los originales con acceso restringido.
6. **Erradicar/recuperar:** corregir configuración o credenciales mediante cambio aprobado, restaurar servicios y validar integridad.
7. **Cerrar:** documentar causa, impacto, controles, tiempos, evidencia y acción preventiva; actualizar riesgo y tratamiento.

## Consultas reproducibles

```powershell
python scripts/siem_ligero.py search --category authentication --outcome denied
python scripts/siem_ligero.py search --category authorization --outcome denied
python scripts/siem_ligero.py search --source suricata
python scripts/siem_ligero.py search --category database_authentication
python scripts/siem_ligero.py search --category backup --outcome failure
python scripts/siem_ligero.py alerts
```

La guía por firma IDS está en `evidencias/ids/REPORTE-IDS.md` (sección 7).

## Escalamiento académico propuesto

- Alta/crítica: responsable de Seguridad, propietario del servicio y Continuidad.
- Media: custodio técnico y Seguridad.
- Baja: registrar, revisar tendencia y cerrar si corresponde a prueba autorizada.

Los cargos y tiempos son supuestos académicos pendientes de aprobación institucional.
