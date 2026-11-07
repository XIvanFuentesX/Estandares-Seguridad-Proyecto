param(
    [Parameter(Mandatory = $true)][string]$Label,
    [string]$CompareTo
)

# Huella no destructiva (sólo SELECT) de ambas bases: conteo exacto por tabla y hash del contenido académico.
# Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$evidencePath = Join-Path $root "evidencias\postgres-upgrade"
New-Item -ItemType Directory -Force -Path $evidencePath | Out-Null
$envValues = @{}
Get-Content (Join-Path $localPath ".env") | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { $envValues[$matches[1]] = $matches[2] }
}
$countSql = @"
SELECT table_schema || '.' || table_name || '=' ||
  (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I.%I', table_schema, table_name), false, true, '')))[1]::text
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema') AND table_type = 'BASE TABLE'
ORDER BY 1
"@
$targets = [ordered]@{
    academic = @{ Service = "db"; User = $envValues["DB_USER"]; Db = $envValues["DB_NAME"] }
    identity = @{ Service = "identity-db"; User = $envValues["KC_DB_USER"]; Db = $envValues["KC_DB_NAME"] }
}
# Tablas de identidad que no deben variar por un reinicio (las de sesiones/eventos sí pueden).
$identityKeyTables = @("public.user_entity", "public.credential", "public.user_role_mapping", "public.keycloak_role",
    "public.realm", "public.client", "public.user_group_membership", "public.required_action_provider")

$result = [ordered]@{ label = $Label; timestamp = (Get-Date).ToString("o"); databases = [ordered]@{} }
Push-Location $localPath
try {
    foreach ($name in $targets.Keys) {
        $t = $targets[$name]
        $rows = docker compose -f compose.yaml exec -T $t.Service psql -U $t.User -d $t.Db -Atc $countSql
        if ($LASTEXITCODE -ne 0) { throw "No se pudo leer la huella de $name." }
        $counts = [ordered]@{}
        foreach ($line in $rows) { $k, $v = $line -split '=', 2; $counts[$k] = [int]$v }
        $version = docker compose -f compose.yaml exec -T $t.Service psql -U $t.User -d $t.Db -Atc "SHOW server_version"
        $entry = [ordered]@{ server_version = "$version".Trim(); tables = $counts.Count; total_rows = ($counts.Values | Measure-Object -Sum).Sum; counts = $counts }
        if ($name -eq "academic") {
            $hash = docker compose -f compose.yaml exec -T $t.Service psql -U $t.User -d $t.Db -Atc "SELECT md5(string_agg(c::text, '|' ORDER BY c::text)) FROM cursos c"
            $entry.cursos_content_md5 = "$hash".Trim()
        }
        $result.databases[$name] = $entry
    }
} finally { Pop-Location }

if ($CompareTo) {
    $before = Get-Content $CompareTo -Raw -Encoding UTF8 | ConvertFrom-Json
    $differences = [System.Collections.Generic.List[string]]::new()
    $academicBefore = $before.databases.academic
    foreach ($p in $academicBefore.counts.PSObject.Properties) {
        if ($result.databases.academic.counts[$p.Name] -ne $p.Value) { $differences.Add("academic:$($p.Name) $($p.Value)->$($result.databases.academic.counts[$p.Name])") }
    }
    if ($academicBefore.cursos_content_md5 -ne $result.databases.academic.cursos_content_md5) { $differences.Add("academic:cursos_content_md5") }
    foreach ($table in $identityKeyTables) {
        $old = $before.databases.identity.counts.$table
        if ($old -ne $result.databases.identity.counts[$table]) { $differences.Add("identity:$table $old->$($result.databases.identity.counts[$table])") }
    }
    $informational = @()
    foreach ($p in $before.databases.identity.counts.PSObject.Properties) {
        if ($p.Name -notin $identityKeyTables -and $result.databases.identity.counts[$p.Name] -ne $p.Value) {
            $informational += "$($p.Name) $($p.Value)->$($result.databases.identity.counts[$p.Name])"
        }
    }
    $result.comparison = [ordered]@{
        compared_to = Split-Path $CompareTo -Leaf
        integrity_preserved = ($differences.Count -eq 0)
        differences = $differences
        identity_volatile_tables_changed = $informational
    }
}
$file = Join-Path $evidencePath ("huella-{0}-{1}.json" -f $Label, (Get-Date -Format "yyyyMMdd-HHmmss"))
$result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $file
Write-Output ("OK: label=$Label academic_rows=" + $result.databases.academic.total_rows + " identity_rows=" + $result.databases.identity.total_rows + " evidencia=$file")
if ($result.comparison -and -not $result.comparison.integrity_preserved) {
    throw "Integridad NO preservada: $($result.comparison.differences -join '; ')"
}
