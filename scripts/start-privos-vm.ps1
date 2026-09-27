param(
    [Alias('Install')]
    [switch]$Live,
    [string]$IsoPath,
    [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'
$vmDir = '/root/privos-vm'
$disk = "$vmDir/privos.qcow2"
$vars = "$vmDir/OVMF_VARS_4M.fd"
$iso = '/root/privos-iso/Privos-Live.iso'

& wsl.exe -d $Distro -u root -- test -x /usr/bin/qemu-system-x86_64
if ($LASTEXITCODE -ne 0) {
    throw "QEMU fehlt in WSL '$Distro'. In Ubuntu installieren: sudo apt update; sudo apt install -y qemu-system-x86 qemu-utils ovmf"
}
& wsl.exe -d $Distro -u root -- test -e /dev/kvm
if ($LASTEXITCODE -ne 0) {
    throw "KVM fehlt in WSL '$Distro'. Virtualisierung im BIOS und WSL 2 prüfen."
}
$runningVm = & wsl.exe -d $Distro -u root -- ps -C qemu-system-x86 -o args=
if ($runningVm | Where-Object { $_ -match 'qemu-system-x86_64 -name Privos' }) {
    Write-Host 'Die Privos-VM läuft bereits. Das vorhandene QEMU-Fenster öffnen oder die VM zuerst schließen.'
    return
}

& wsl.exe -d $Distro -u root -- mkdir -p $vmDir
if ($LASTEXITCODE -ne 0) { throw "WSL '$Distro' konnte nicht gestartet werden." }

& wsl.exe -d $Distro -u root -- test -f $disk
if ($LASTEXITCODE -ne 0) {
    & wsl.exe -d $Distro -u root -- qemu-img create -f qcow2 $disk 80G
    if ($LASTEXITCODE -ne 0) { throw 'Die virtuelle Festplatte konnte nicht erstellt werden.' }
}

& wsl.exe -d $Distro -u root -- test -f $vars
if ($LASTEXITCODE -ne 0) {
    & wsl.exe -d $Distro -u root -- cp /usr/share/OVMF/OVMF_VARS_4M.fd $vars
    if ($LASTEXITCODE -ne 0) { throw 'Die UEFI-Einstellungen konnten nicht erstellt werden.' }
}

$qemuArgs = @(
    '-name', 'Privos',
    '-machine', 'q35,accel=kvm',
    '-cpu', 'host',
    '-smp', '4',
    '-m', '8192',
    '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
    '-drive', "if=pflash,format=raw,file=$vars",
    '-drive', "file=$disk,if=virtio,format=qcow2",
    '-device', 'virtio-vga',
    '-display', 'gtk,gl=off',
    '-device', 'qemu-xhci',
    '-device', 'usb-tablet',
    '-netdev', 'user,id=net0',
    '-device', 'virtio-net-pci,netdev=net0'
)

if ($Live) {
    & wsl.exe -d $Distro -u root -- test -f $iso
    $isoMissing = $LASTEXITCODE -ne 0
    if ($IsoPath -or $isoMissing) {
        if (-not $IsoPath) {
            $outputDir = Join-Path $PSScriptRoot '..\output'
            $foundIso = Get-ChildItem -LiteralPath $outputDir -Filter '*.iso' -File -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($foundIso) { $IsoPath = $foundIso.FullName }
        }
        if (-not $IsoPath) {
            throw 'Keine ISO gefunden. Eine fertige Privos-ISO aus GitHub Actions herunterladen oder vom ersten PC kopieren und mit -IsoPath angeben.'
        }
        $windowsIso = (Resolve-Path -LiteralPath $IsoPath).Path.Replace('\', '/')
        $linuxIso = (& wsl.exe -d $Distro -u root -- wslpath -u -a $windowsIso | Select-Object -First 1).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $linuxIso) { throw 'Der ISO-Pfad konnte nicht nach WSL übertragen werden.' }
        & wsl.exe -d $Distro -u root -- mkdir -p /root/privos-iso
        if ($LASTEXITCODE -ne 0) { throw 'Das ISO-Verzeichnis konnte nicht erstellt werden.' }
        Write-Host 'Kopiere die ISO einmalig nach WSL. Das kann einige Minuten dauern.'
        & wsl.exe -d $Distro -u root -- cp -f -- $linuxIso $iso
        if ($LASTEXITCODE -ne 0) { throw 'Die ISO konnte nicht nach WSL kopiert werden.' }
    }
    $qemuArgs += @('-cdrom', $iso, '-boot', 'order=d')
} else {
    $qemuArgs += @('-boot', 'order=c')
}

Write-Host 'Privos-VM startet. Das QEMU-Fenster zum Beenden normal schließen.'
& wsl.exe -d $Distro -u root -- qemu-system-x86_64 @qemuArgs
if ($LASTEXITCODE -ne 0) { throw "QEMU wurde mit Fehlercode $LASTEXITCODE beendet." }
