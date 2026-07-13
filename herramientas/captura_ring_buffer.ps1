# Captura con ring buffer (sección 3.5): 10 archivos de ~5 MB cada uno.
# Ejecutar en PowerShell como administrador, con Wireshark (y Npcap) instalado.
#   .\captura_ring_buffer.ps1 -Carnet 21XXXX
# Detener la captura con Ctrl+C cuando ya existan los 10 archivos.
param(
    [Parameter(Mandatory = $true)][string]$Carnet,
    [string]$Interfaz = "Wi-Fi"
)

$dumpcap = "C:\Program Files\Wireshark\dumpcap.exe"
$salida = Join-Path $PSScriptRoot "..\capturas_ring_buffer"
New-Item -ItemType Directory -Force $salida | Out-Null

# Lista de interfaces disponibles (tomar captura de pantalla de esto también)
& $dumpcap -D

# -b filesize está en kB: 5000 kB = 5 MB. -b files:10 conserva solo los últimos 10 archivos.
& $dumpcap -i $Interfaz -b filesize:5000 -b files:10 -w (Join-Path $salida "lab1_$Carnet.pcapng")
