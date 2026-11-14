param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$nodeExecutable = (Get-Command node -ErrorAction Stop).Source
Push-Location -LiteralPath $projectRoot
try {
    & $nodeExecutable scripts/preparar_render.mjs
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar la aplicación.' }
    $healthUrl = 'http://127.0.0.1:8996/__health'
    $health = $null
    try { $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2 } catch {}
    if ($health -and ($health.app -ne 'globo-detalle' -or [IO.Path]::GetFullPath($health.root).TrimEnd('\') -ne (Join-Path $projectRoot 'public'))) {
        throw 'El puerto 8996 está ocupado por otra aplicación.'
    }
    if (-not $health) {
        $logs = Join-Path $projectRoot 'reports\globo-detalle'
        New-Item -ItemType Directory -Path $logs -Force | Out-Null
        $serverProcess = Start-Process -FilePath $nodeExecutable -ArgumentList 'scripts/servir-local.mjs' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'server.log') -RedirectStandardError (Join-Path $logs 'server-error.log')
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Milliseconds 200
            if ($serverProcess.HasExited) { throw 'El servidor no pudo arrancar. Revisa reports/globo-detalle/server-error.log.' }
            try { $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 1; break } catch {}
        }
    }
    if (-not $health -or $health.app -ne 'globo-detalle') { throw 'El servidor local no respondió.' }
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8996/' -WindowStyle Hidden }
    Write-Output 'Aplicación disponible en http://127.0.0.1:8996/'
} finally { Pop-Location }
