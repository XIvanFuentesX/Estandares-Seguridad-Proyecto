param(
    [string]$TlsDirectory = (Join-Path $PSScriptRoot "..\local\tls")
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path $TlsDirectory).Path
$cert = Join-Path $resolved "uvcg-lab.crt"
$key = Join-Path $resolved "uvcg-lab.key"

if ((Test-Path $cert) -and (Test-Path $key)) {
    Write-Output "Certificado de laboratorio existente; no se reemplazó."
    exit 0
}

$volume = $resolved.Replace('\', '/')
docker run --rm --mount "type=bind,source=$volume,target=/certs" alpine/openssl req `
    -x509 -nodes -newkey rsa:3072 -sha256 -days 365 `
    -keyout /certs/uvcg-lab.key -out /certs/uvcg-lab.crt `
    -subj "/CN=localhost/O=UVCG Laboratorio/OU=SGSI" `
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" `
    -addext "basicConstraints=critical,CA:FALSE" `
    -addext "keyUsage=critical,digitalSignature,keyEncipherment" `
    -addext "extendedKeyUsage=serverAuth" | Out-Null

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $cert) -or -not (Test-Path $key)) {
    throw "No se pudo generar el certificado TLS de laboratorio."
}
Write-Output "Certificado autofirmado de laboratorio generado; la clave privada no se mostró."
