$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (& wsl.exe -d Ubuntu-22.04 -- wslpath -a $repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve repository path in WSL.' }
& wsl.exe -d Ubuntu-22.04 -- bash "$linuxRepo/scripts/run-walk.sh"
if ($LASTEXITCODE -ne 0) { throw "Kimodo generation failed: $LASTEXITCODE" }
