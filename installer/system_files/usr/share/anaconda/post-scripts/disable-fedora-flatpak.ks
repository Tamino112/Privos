%post --erroronfail --log=/tmp/privos-disable-fedora-flatpak.log
systemctl disable flatpak-add-fedora-repos.service || :
%end
