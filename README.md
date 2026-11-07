# Laboratorio práctico SGSI — UVCG (versión 0.1)

Este repositorio es un **prototipo académico** para la universidad ficticia UVCG. No representa un SGSI certificado ni una infraestructura de producción. No se han desplegado recursos Azure ni ejecutado contenedores por el solo hecho de generar este repositorio.

## Módulo 1: laboratorio local (Docker Desktop)

Requisitos: Docker Desktop con Compose, al menos 4 GB de RAM libres, terminal PowerShell.

1. Ingresar a la carpeta `local`.
2. Copiar `.env.example` a `.env` y sustituir `DB_PASSWORD` por una contraseña larga y única (no subir `.env` a repositorios).
3. Ejecutar `docker compose up -d --build`.
4. Ejecutar `python ../scripts/pruebas_locales.py`.
5. Abrir `http://127.0.0.1:8080/cursos`.
6. Para detener: `docker compose down`; para **borrar datos**, solo si se desea: `docker compose down -v`.

Arquitectura: `localhost:8080 -> Nginx (DMZ) -> API Flask (APPS) -> PostgreSQL (DATOS)`.
La API y la base no publican puertos al host. Hay redes Docker `internal` para APPS y DATOS. Es **segmentación funcional simplificada**, no equivale a un firewall NGFW ni prueba Zero Trust. HTTP se limita a loopback para laboratorio; no publicar directamente en Internet ni tratar datos reales. No hay login institucional en el prototipo, por lo que solo contiene información ficticia pública.

## Módulo 2: base Azure (Terraform)

Requisitos: suscripción Azure, Azure CLI, Terraform >=1.6 y permisos para crear recursos. **Hay costos potenciales**, aun con monitoreo desactivado; verificar precios y presupuestos antes de desplegar.

1. Ingresar a `azure`.
2. Copiar `terraform.tfvars.example` a `terraform.tfvars` y definir `subscription_id`.
3. Ejecutar `az login` y `az account set --subscription <ID>`.
4. Ejecutar `terraform init`, `terraform fmt -check`, `terraform validate` y `terraform plan -out=plan.tfplan`.
5. **Revisar el plan y costos**; solo después ejecutar `terraform apply plan.tfplan`.
6. Comprobar en Azure Portal el grupo de recursos, las cinco subredes, los NSG y sus asociaciones; tomar capturas reales.
7. Eliminar el laboratorio cuando deje de usarse con `terraform destroy` tras revisar los recursos afectados.

La base crea: grupo de recursos, VNet 10.20.0.0/16, cinco subredes, un NSG por subred, permiso TCP 443 de DMZ a APPS, permiso TCP 5432 de APPS a DATOS, y denegación del resto de tráfico entrante (incluido tráfico lateral no autorizado). **No crea máquinas virtuales, VPN, servicios de aplicación, firewall NGFW, IDS/IPS, IAM/MFA, DLP/MDM, backups ni SIEM**. Log Analytics es opcional y desactivado por defecto; activarlo no crea por sí solo integración de diagnósticos ni SIEM.

**Advertencia:** los NSG son restrictivos deliberadamente; al añadir máquinas de gestión o servicios reales habrá que ajustar reglas concretas. Los nombres de NSG, subredes y demás se deben reconciliar con el diagrama final aprobado.

## Evidencias para el docente

Registrar únicamente resultados obtenidos efectivamente: fecha, componente, comando/prueba, esperado, observado, evidencia (captura/archivo), responsable y estado. Véase `evidencias/registro.csv`.

## Seguridad del repositorio

No subir `.env`, `terraform.tfstate`, `*.tfplan`, ni secretos. Evitar claves en capturas. Cualquier despliegue es decisión del operador después de revisar permisos, costos y red. No hay evidencia de ejecución ni simulación de resultados aquí.
