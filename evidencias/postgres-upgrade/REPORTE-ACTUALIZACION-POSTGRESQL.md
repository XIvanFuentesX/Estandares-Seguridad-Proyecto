# Reporte de actualización PostgreSQL a imagen endurecida

Fecha: 2026-10-24. Autorización: expresa del usuario para actualizar `db` e `identity-db` con respaldos y reversión. Riesgo tratado: **R-009** (control A.8.8, A.8.20, A.8.22).

## 1. Preparación (Actividad A)

| Verificación | Resultado | Evidencia |
|---|---|---|
| Cinco servicios principales | `healthy` antes del cambio | salida de diagnóstico; `estado-aplicaciones-post-upgrade.json` |
| Volúmenes | `db` → `local_pgdata`; `identity-db` → `local_identity_data` (`/var/lib/docker/volumes/<nombre>/_data`, montados en `/var/lib/postgresql/data`) | `actualizacion-20261024-102229.json` |
| Versión | Imagen anterior y nueva: PostgreSQL **16.15**; `PG_VERSION` de los datos = 16; binario `postgres` idéntico (SHA-256 6705048937384211…) | `actualizacion-*.json` |
| Linaje de imagen | `local-postgres-hardened:16` comparte las 11 capas de `postgres:16-alpine` (sha256:f4610795…) y añade sólo la capa que elimina `gosu` | `local/postgres-hardened/Dockerfile` |
| Formato de almacenamiento | Sin cambio (mismo binario y versión mayor; no hay `pg_upgrade` ni migración) | — |
| Propiedad y permisos | Directorio de datos `drwx------ 70:70`; 0 archivos de otro propietario (1 300 y 1 803 archivos) | diagnóstico |
| Arranque sin privilegios | La imagen corre como UID 70; el entrypoint oficial sólo usa `gosu` cuando arranca como root | prueba en instancias aisladas |
| Copia del Compose | `local/rollback/compose.yaml.pre-upgrade-20261024-102045.bak` (SHA-256 75A2C99C…) | — |
| Respaldo lógico nuevo | `academic-20261024-162047.dump.enc`, `identity-20261024-162048.dump.enc`, cifrados, SHA-256 verificado | `../backup/backup-dual-20261024-102049.json` |
| Restauración de comprobación | Académica 8.22 s (3 cursos); identidad 8.947 s (5 identidades); aislada | `../recovery/restauracion-dual-20261024_102049.json` |
| Huella previa | Conteo exacto de filas de todas las tablas + MD5 del contenido de `cursos` | `huella-pre-upgrade-20261024-102047.json` |

Condición de continuidad: todos los respaldos y las restauraciones de comprobación fueron exitosos.

## 2. Actualización (Actividad B)

Script: `scripts/actualizar_postgres_endurecido.ps1`. Secuencia: validar el Compose candidato → detener API, Keycloak y schedulers → detener las bases → **copia en frío** de ambos volúmenes (`local/rollback/volumes/*.tgz` + `.sha256`) → recrear sólo `db` e `identity-db` (`--no-deps --force-recreate`, sin `-v`) → levantar dependientes → verificar.

Cambio mínimo en `local/compose.yaml` (por servicio): `image: local-postgres-hardened:16`, `build: ./postgres-hardened`, `user: "70:70"` y eliminación de `cap_add` (las capacidades no se usan con un proceso no root; la configuración resultante es idéntica a la ya validada en las instancias de restauración).

| Resultado | Valor |
|---|---|
| Bases `healthy` tras la recreación | 7.3 s |
| Interrupción hasta tener los cinco servicios `healthy` | 55.7 s |
| Usuario efectivo / `gosu` en los contenedores | UID 70 / ausente (ambas bases) |
| Integridad de datos | Huella post = huella previa: 0 diferencias (`huella-post-upgrade-20261024-102335.json`) |
| Parada y arranque | Parada previa limpia (`database system was shut down`, sin recuperación por caída); parada rápida limpia con la imagen nueva comprobada en la instancia aislada |
| HTTPS / MFA / RBAC | `pruebas_locales.py` y `pruebas_identidad.py` exitosos |
| Segmentación | `validar_segmentacion.ps1`: sólo el proxy publica; proxy↛db; db↛proxy |
| Reversión automática | No fue necesaria |

## 3. Vulnerabilidades antes y después

Ambos escaneos se hicieron con Trivy 0.76.1, la misma base de datos y severidad HIGH/CRITICAL, sobre las imágenes realmente usadas.

| Imagen | Servicios | CRITICAL | HIGH | Componente |
|---|---|---:|---:|---|
| `postgres:16-alpine` (antes) | db, identity-db | 1 | 25 | Go `stdlib` dentro de `/usr/local/bin/gosu` |
| `local-postgres-hardened:16` (después) | db, identity-db | 0 | 0 | — |
| `local-keycloak` | keycloak | 0 | 2 | `java-21-openjdk-headless` (sin corrección publicada) |
| `local-api`, `local-proxy:latest`, `local-backup-tool:latest` | api, proxy, schedulers | 0 | 0 | — |

Interpretación: los 26 hallazgos **no se corrigieron en upstream**. Desaparecen porque el componente vulnerable (`gosu`) ya no existe en los contenedores en ejecución, lo cual se verificó dentro de cada contenedor y no sólo por el cambio de etiqueta de la imagen. El resto de paquetes del SO y el binario de PostgreSQL son idénticos. Si se ejecuta la reversión, los hallazgos vuelven. Evidencia: `../security/trivy-antes-postgres-16-alpine-pre-upgrade.json`, `../security/escaneo-imagenes-en-uso-post-upgrade.json`.

## 4. Procedimiento de reversión (Actividad C)

| Elemento | Valor |
|---|---|
| Imagen anterior | `postgres:16-alpine` (sha256:f4610795587492cd…), presente localmente |
| Compose previo | `local/rollback/compose.yaml.pre-upgrade-20261024-102045.bak` |
| Copias en frío | `local/rollback/volumes/local_pgdata-20261024-102229.tgz` (SHA-256 2F82AA22…), `local_identity_data-20261024-102229.tgz` (SHA-256 6491C202…) |
| Script | `scripts/rollback_postgres.ps1 -RollbackCompose <compose previo>` (verificación) y `-Execute` (reversión) |

**Criterios de activación:** alguna base no alcanza `healthy` en 120 s; la huella posterior difiere de la previa; fallan MFA, RBAC o HTTPS atribuibles a la base; errores `FATAL`/`PANIC` o de permisos en los logs de PostgreSQL; degradación sostenida sin otra causa.

**Pasos (no destructivos):**
1. `scripts/rollback_postgres.ps1 -RollbackCompose local\rollback\compose.yaml.pre-upgrade-20261024-102045.bak` → debe informar `rollback_preparado=True`.
2. Repetir con `-Execute`: guarda el Compose actual, restaura el previo, detiene API y Keycloak, recrea sólo `db` e `identity-db` **sin borrar volúmenes**, y levanta los dependientes.
3. Verificar: `scripts/huella_datos_postgres.ps1 -Label post-rollback -CompareTo <huella previa>`, `pruebas_identidad.py`, `pruebas_locales.py`, `validar_segmentacion.ps1`.
4. Restaurar las copias en frío sobre los volúmenes **no** forma parte de la reversión automática: sobrescribe datos y requiere autorización expresa.

**Verificación ejecutada:** modo verificación `rollback_preparado=True` (Compose previo válido, imagen anterior disponible, volúmenes presentes). La imagen anterior arrancó sobre cada copia en frío en un contenedor efímero sin red, con los datos en `tmpfs` (sin crear volúmenes): 3 cursos y 5 identidades, 0 errores fatales (`rollback-prueba-imagen-anterior-20261024-1031.json`). Al ser idénticos el binario y la versión mayor, la imagen anterior también es compatible con los datos escritos después de la actualización.

## 5. Observaciones

- Las copias en frío contienen datos de identidad (incluidos los hashes de contraseñas): están excluidas de Git (`local/.gitignore`) y deben tratarse como información confidencial.
- La comprobación previa de restauración borró las dos bases temporales que ella misma había creado en la instancia aislada (`restore_*_20261024_102049`). Desde entonces, `restaurar_prueba.ps1` **conserva** las bases restauradas por defecto; borrarlas exige `-DropRestoredDatabase`.
