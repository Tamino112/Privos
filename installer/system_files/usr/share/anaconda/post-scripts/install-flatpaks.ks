%post --erroronfail --nochroot --log=/tmp/privos-install-flatpaks.log
# Die im Live-System vorinstallierten Flatpaks direkt ins neue System kopieren (kein Download nötig)
deployment="$(ostree rev-parse --repo=/mnt/sysimage/ostree/repo ostree/0/1/0)"
target="/mnt/sysimage/ostree/deploy/default/deploy/$deployment.0/var/lib/"
mkdir -p "$target"
rsync -aAXUHKP --open-noatime /var/lib/flatpak "$target"
sync "$target"
%end
