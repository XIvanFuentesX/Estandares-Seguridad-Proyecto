param(
    [string]$EnvPath = (Join-Path $PSScriptRoot "..\local\.env")
)

$ErrorActionPreference = "Stop"

function New-RandomBytes([int]$Count) {
    $bytes = New-Object byte[] $Count
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return $bytes
}

function New-Password {
    $value = [Convert]::ToBase64String((New-RandomBytes 24)).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    return "Aa1!$value"
}

function ConvertTo-Base32([byte[]]$Bytes) {
    $alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    $result = New-Object System.Text.StringBuilder
    $buffer = 0
    $bitsLeft = 0
    foreach ($byte in $Bytes) {
        $buffer = ($buffer -shl 8) -bor $byte
        $bitsLeft += 8
        while ($bitsLeft -ge 5) {
            $bitsLeft -= 5
            [void]$result.Append($alphabet[($buffer -shr $bitsLeft) -band 31])
        }
    }
    if ($bitsLeft -gt 0) {
        [void]$result.Append($alphabet[($buffer -shl (5 - $bitsLeft)) -band 31])
    }
    return $result.ToString()
}

$required = [ordered]@{
    DB_USER = "sgsi_demo"
    DB_NAME = "universidad_demo"
    DB_PASSWORD = { New-Password }
    KC_DB_NAME = "keycloak"
    KC_DB_USER = "keycloak"
    KC_DB_PASSWORD = { New-Password }
    KC_ADMIN_USER = "kcadmin"
    KC_ADMIN_PASSWORD = { New-Password }
    BACKUP_ENCRYPTION_PASSWORD = { New-Password }
    UVCG_ADMIN_PASSWORD = { New-Password }
    UVCG_ADMIN_TOTP = { ConvertTo-Base32 (New-RandomBytes 20) }
    UVCG_DOCENTE_PASSWORD = { New-Password }
    UVCG_DOCENTE_TOTP = { ConvertTo-Base32 (New-RandomBytes 20) }
    UVCG_ESTUDIANTE_PASSWORD = { New-Password }
    UVCG_ESTUDIANTE_TOTP = { ConvertTo-Base32 (New-RandomBytes 20) }
    UVCG_ADMINISTRATIVO_PASSWORD = { New-Password }
    UVCG_ADMINISTRATIVO_TOTP = { ConvertTo-Base32 (New-RandomBytes 20) }
}

$lines = [System.Collections.Generic.List[string]]::new()
if (Test-Path $EnvPath) {
    foreach ($line in Get-Content $EnvPath) { $lines.Add($line) }
}
$existing = @{}
foreach ($line in $lines) {
    if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=') { $existing[$matches[1]] = $true }
}

foreach ($entry in $required.GetEnumerator()) {
    if (-not $existing.ContainsKey($entry.Key)) {
        $value = if ($entry.Value -is [scriptblock]) { & $entry.Value } else { $entry.Value }
        $lines.Add("$($entry.Key)=$value")
    }
}

[System.IO.File]::WriteAllLines((Resolve-Path (Split-Path $EnvPath -Parent)).Path + "\.env", $lines, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Secretos locales presentes: valores no mostrados."
