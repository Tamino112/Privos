%post --erroronfail --log=/tmp/privos-restore-selinux-labels.log
setenforce 0 || true
restorecon -R /etc/selinux
restorecon -R /var/lib/flatpak
%end
