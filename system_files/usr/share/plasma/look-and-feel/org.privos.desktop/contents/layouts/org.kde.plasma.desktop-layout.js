// Privos-Standardlayout: Plasma-Standardleiste, aufgeräumt und mit Privos-Startmenü
loadTemplate("org.kde.plasma.desktop.defaultPanel")

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = "org.kde.image";
    desktopsArray[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktopsArray[j].writeConfig("Image", "file:///usr/share/wallpapers/Privos/");
}

panels().forEach(function (panel) {
    // Startmenü mit Privos-Logo
    panel.widgets("org.kde.plasma.kickoff").forEach(function (widget) {
        widget.currentConfigGroup = ["General"];
        widget.writeConfig("icon", "privos-logo");
    });
    // Virtuelle-Desktops-Umschalter ausblenden – weniger Ablenkung
    panel.widgets("org.kde.plasma.pager").forEach(function (widget) {
        widget.remove();
    });
});
