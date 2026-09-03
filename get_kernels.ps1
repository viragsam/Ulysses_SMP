# Downloads the NAIF SPICE kernels listed in smp.tm into .\kernels\
# Usage (PowerShell, from the project root):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\get_kernels.ps1
$ErrorActionPreference = "Stop"

$B = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels"
$files = @(
    @{ dir = "lsk"; url = "$B/lsk/naif0012.tls" },
    @{ dir = "spk"; url = "$B/spk/planets/de440s.bsp" },
    @{ dir = "pck"; url = "$B/pck/pck00011.tpc" },
    @{ dir = "pck"; url = "$B/pck/moon_pa_de440_200625.bpc" },
    @{ dir = "fk";  url = "$B/fk/satellites/moon_de440_250416.tf" }
)

foreach ($f in $files) {
    $dir  = Join-Path "kernels" $f.dir
    $name = Split-Path $f.url -Leaf
    $dest = Join-Path $dir $name
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    if (Test-Path $dest) {
        Write-Host "exists   $dest"
    } else {
        Write-Host "download $name"
        Invoke-WebRequest -Uri $f.url -OutFile $dest
    }
}

Write-Host "Kernels downloaded to .\kernels\"
