param(
    [switch]$Install
)

$ErrorActionPreference = 'Stop'
$distro = 'Ubuntu'
$vmDir = '/root/privos-vm'
$disk = "$vmDir/privos.qcow2"
$vars = "$vmDir/OVMF_VARS_4M.fd"
$iso = '/root/privos-iso/Privos-Live.iso'

& wsl.exe -d $distro -u root -- mkdir -p $vmDir
if ($LASTEXITCODE -ne 0) { throw 'WSL Ubuntu konnte nicht gestartet werden.' }

& wsl.exe -d $distro -u root -- test -f $disk
if ($LASTEXITCODE -ne 0) {
    & wsl.exe -d $distro -u root -- qemu-img create -f qcow2 $disk 80G
    if ($LASTEXITCODE -ne 0) { throw 'Die virtuelle Festplatte konnte nicht erstellt werden.' }
}

& wsl.exe -d $distro -u root -- test -f $vars
if ($LASTEXITCODE -ne 0) {
    & wsl.exe -d $distro -u root -- cp /usr/share/OVMF/OVMF_VARS_4M.fd $vars
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

if ($Install) {
    & wsl.exe -d $distro -u root -- test -f $iso
    if ($LASTEXITCODE -ne 0) { throw "Die einmalig benötigte ISO fehlt in WSL: $iso" }
    $qemuArgs += @('-cdrom', $iso, '-boot', 'order=d')
} else {
    $qemuArgs += @('-boot', 'order=c')
}

Write-Host 'Privos-VM startet. Das QEMU-Fenster zum Beenden normal schließen.'
& wsl.exe -d $distro -u root -- qemu-system-x86_64 @qemuArgs
if ($LASTEXITCODE -ne 0) { throw "QEMU wurde mit Fehlercode $LASTEXITCODE beendet." }
