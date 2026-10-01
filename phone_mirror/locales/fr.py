"""French translation. Keys are the English strings passed to `_()`."""

CATALOG = {
    # General
    "Phone Mirror": "Miroir Téléphone",
    "{app} — Settings": "{app} — Réglages",
    "{app} — Webcam": "{app} — Webcam",
    "The phone": "Le téléphone",
    "Retry": "Réessayer",
    "Cancel": "Annuler",
    "Open settings": "Ouvrir les réglages",
    " and ": " et ",

    # Connection
    "Connecting to the phone…": "Connexion au téléphone…",
    "A phone is plugged in over USB but hasn't authorized this computer.\n\n"
    "Accept “Allow USB debugging” on the phone's screen, then click Retry.":
        "Un téléphone est branché en USB mais n'a pas autorisé ce PC.\n\n"
        "Accepte « Autoriser le débogage USB » sur l'écran du téléphone, puis clique sur "
        "Réessayer.",
    "{name} can't be reached.\n\n"
    "Plug it in over USB and click Retry: mirroring will go through the cable, and Wi-Fi "
    "will be set up again for next time (useful after the phone restarted).\n\n"
    "Otherwise, check that it is on the same Wi-Fi network.":
        "{name} est injoignable.\n\n"
        "Branche-le en USB puis clique sur Réessayer : le miroir passera par le câble, et le "
        "Wi-Fi sera réactivé pour la prochaine fois (utile si le téléphone a redémarré).\n\n"
        "Sinon, vérifie qu'il est bien sur le même réseau Wi-Fi.",
    "Phone IP…": "IP du téléphone…",
    "Phone IP address (Settings → Wi-Fi on the phone):":
        "Adresse IP du téléphone (Paramètres → Wi-Fi sur le téléphone) :",
    "If the error mentions an encoder or a codec, try H.264 or a lower resolution in the "
    "settings.":
        "Si l'erreur parle d'encodeur ou de codec, essaie H.264 ou une résolution plus basse "
        "dans les réglages.",

    # Mirror
    "USB cable detected — switching to USB…": "Câble USB détecté — passage en USB…",
    "New settings — restarting the mirror…": "Nouveaux réglages — redémarrage du miroir…",
    "The mirror could not start.": "Le miroir n'a pas pu démarrer.",
    "Connection lost — reconnecting…": "Connexion perdue — reconnexion…",
    "Connection lost — reconnecting to the phone…":
        "Connexion perdue — reconnexion au téléphone…",
    "The connection to the phone was lost. Reconnect?":
        "La connexion au téléphone a été perdue. Reconnecter ?",

    # Webcam
    "Phone camera": "Caméra du téléphone",
    "No virtual webcam is available.\n\n"
    "One-time setup: install v4l2loopback (on Arch: v4l2loopback-dkms — some kernels, such "
    "as CachyOS's, already include it), then paste these commands in a terminal (your "
    "password will be asked). They create the “Phone Camera” webcam at every boot, plus a "
    "second one for OBS's virtual camera.":
        "Aucune webcam virtuelle n'est disponible.\n\n"
        "Mise en place unique : installe v4l2loopback (sur Arch : v4l2loopback-dkms — "
        "certains noyaux, comme celui de CachyOS, l'incluent déjà), puis colle ces commandes "
        "dans un terminal (mot de passe demandé). Elles créent la webcam « Phone Camera » à "
        "chaque démarrage, plus une seconde pour la caméra virtuelle d'OBS.",
    "Copy the commands": "Copier les commandes",
    "Pick “{name}” as the camera in Discord or your browser.\n"
    "In OBS, use a “Video Capture Device (V4L2)” source, not “PipeWire Camera”: PipeWire "
    "doesn't see this virtual webcam.":
        "Choisis « {name} » comme caméra dans Discord ou ton navigateur.\n"
        "Dans OBS : source « Périphérique de capture vidéo (V4L2) », pas « Caméra PipeWire » "
        "(PipeWire ne voit pas cette webcam virtuelle).",
    "Stop": "Arrêter",
    "Switch to the back camera": "Passer à la caméra arrière",
    "Switch to the front camera": "Passer à la caméra avant",
    "● Webcam on: {camera}, {res} at {fps} fps → {dev}":
        "● Webcam active : {camera}, {res} à {fps} i/s → {dev}",
    "front camera": "caméra avant",
    "back camera": "caméra arrière",
    "The webcam could not start.": "La webcam n'a pas pu démarrer.",
    "The phone is using its camera (face unlock?) — unlock it… retry {n}/5":
        "Caméra occupée par le téléphone (déverrouillage facial ?) — déverrouille-le… "
        "nouvel essai {n}/5",
    "The preview window was closed: the webcam is off.":
        "La fenêtre d'aperçu a été fermée : la webcam est coupée.",
    "The preview and the webcam are one and the same. To stop the webcam, use the “Stop” "
    "button of this window instead.":
        "L'aperçu et la webcam ne font qu'un. Pour arrêter la webcam, utilise plutôt le "
        "bouton « Arrêter » de cette fenêtre-ci.",
    "Restart": "Relancer",
    "Restart without preview": "Relancer sans aperçu",
    "Stop the webcam": "Arrêter la webcam",

    # Settings — tabs and buttons
    "Phones": "Téléphones",
    "Mirror": "Miroir",
    "Webcam": "Webcam",
    "Start mirror": "Lancer le miroir",
    "Start webcam": "Lancer la webcam",
    "A running mirror or webcam restarts with the new settings.":
        "Un miroir ou une webcam en cours redémarre avec les nouveaux réglages.",
    "✔ Saved.": "✔ Enregistré.",
    "to the running mirror": "au miroir en cours",
    "to the running webcam": "à la webcam en cours",
    "✔ Saved — applied {where} (restarting in a few seconds).":
        "✔ Enregistré — appliqué {where} (redémarrage en quelques secondes).",
    "Already running: settings applied (restarting in a few seconds).":
        "Déjà lancé : réglages appliqués (redémarrage en quelques secondes).",
    "✔ Mirror started.": "✔ Miroir lancé.",
    "✔ Webcam started.": "✔ Webcam lancée.",
    "Keep this window open to adjust: each save applies right away (short restart).":
        "Garde cette fenêtre ouverte pour ajuster : chaque enregistrement s'applique aussitôt "
        "(court redémarrage).",

    # Settings — phones
    "Phone": "Téléphone",
    "Automatic (first phone found)": "Automatique (premier téléphone trouvé)",
    "no Wi-Fi yet": "pas encore de Wi-Fi",
    "Detect phones": "Détecter les téléphones",
    "Finds the phones plugged in over USB (or already connected over Wi-Fi) and prepares "
    "their Wi-Fi connection.":
        "Trouve les téléphones branchés en USB (ou déjà connectés en Wi-Fi) et prépare leur "
        "connexion Wi-Fi.",
    "Add by IP…": "Ajouter par IP…",
    "Rename…": "Renommer…",
    "Forget": "Oublier",
    "Name of this phone:": "Nom de ce téléphone :",
    "Looking for phones…": "Recherche des téléphones…",
    "✔ Found: {names}": "✔ Trouvé : {names}",
    "✘ No phone found. Plug one in over USB, with USB debugging enabled, and accept the "
    "prompt on it.":
        "✘ Aucun téléphone trouvé. Branche-en un en USB, avec le débogage USB activé, et "
        "accepte la demande qui s'affiche dessus.",
    "✘ No answer from {ip}:{port}. Wireless adb must be on: plug the phone in once and "
    "click “Detect phones”.":
        "✘ Pas de réponse de {ip}:{port}. L'adb sans fil doit être actif : branche le "
        "téléphone une fois et clique sur « Détecter les téléphones ».",
    "⚠ A plugged-in phone hasn't authorized this computer yet: unlock it and accept “Allow "
    "USB debugging?” on its screen, then click “Detect phones” again. No prompt? Unplug and "
    "plug it back in, or use “Revoke USB debugging authorizations” in its Developer options.":
        "⚠ Un téléphone branché n'a pas encore autorisé ce PC : déverrouille-le et accepte "
        "« Autoriser le débogage USB ? » sur son écran, puis clique à nouveau sur « Détecter "
        "les téléphones ». Pas de demande ? Débranche-le et rebranche-le, ou utilise "
        "« Révoquer les autorisations de débogage USB » dans ses Options pour les "
        "développeurs.",
    "✔ Added: {name}": "✔ Ajouté : {name}",
    "Test the connection": "Tester la connexion",
    "✔ {name}: connected over Wi-Fi ({ip})": "✔ {name} : connecté en Wi-Fi ({ip})",
    "✔ {name}: connected over USB — Wi-Fi ready for later ({ip})":
        "✔ {name} : connecté en USB — Wi-Fi prêt pour plus tard ({ip})",
    "✔ {name}: connected over USB — the phone's Wi-Fi is off":
        "✔ {name} : connecté en USB — Wi-Fi du téléphone coupé",
    "✘ Plugged in over USB but not authorized: accept the prompt on the phone.":
        "✘ Branché en USB mais non autorisé : accepte la demande sur le téléphone.",
    "✘ Unreachable. Plug the phone in over USB.":
        "✘ Injoignable. Branche le téléphone en USB.",
    "A new phone: enable USB debugging (Developer options), plug it in and click “Detect "
    "phones”. After a phone restart, plug it in once: Wi-Fi is set up again automatically.":
        "Nouveau téléphone : active le débogage USB (Options pour les développeurs), "
        "branche-le et clique sur « Détecter les téléphones ». Après un redémarrage du "
        "téléphone, branche-le une fois : le Wi-Fi se réactive tout seul.",
    "Reconnect automatically if Wi-Fi drops": "Reconnexion automatique si le Wi-Fi coupe",
    "Application menu": "Menu des applications",
    "Clicking the icon": "Clic sur l'icône",
    "Open these settings": "Ouvrir ces réglages",
    "Start mirroring right away": "Lancer le miroir directement",
    "Right-clicking the icon always offers: Mirror now, Webcam and Settings.":
        "Le clic droit sur l'icône donne toujours : Miroir direct, Webcam et Réglages.",

    # Settings — mirror
    "Preset": "Préréglage",
    "Custom": "Personnalisé",
    "Smooth (busy Wi-Fi)": "Fluide (Wi-Fi chargé)",
    "Balanced": "Équilibré",
    "Best quality": "Qualité max",
    "Max resolution": "Résolution max",
    "Native": "Native",
    "Max frame rate": "Images/s max",
    "Unlimited": "Illimité",
    "Video bitrate": "Débit vidéo",
    "Codec": "Codec",
    "H.265 — better picture at the same bitrate": "H.265 — meilleure image à débit égal",
    "H.264 — most compatible": "H.264 — le plus compatible",
    "Anti-stutter buffer": "Tampon anti-saccades",
    "None (lowest latency)": "Aucun (latence minimale)",
    "Delays the picture slightly to absorb Wi-Fi hiccups.":
        "Retarde légèrement l'image pour absorber les à-coups du Wi-Fi.",
    "Turn the phone screen off": "Éteindre l'écran du téléphone",
    "Keep the phone awake (even on battery)": "Garder le téléphone éveillé (même sur batterie)",
    "Forward the sound": "Transférer le son",
    "Fullscreen": "Plein écran",
    "Always on top": "Toujours au premier plan",
    "Stutters? Over Wi-Fi it's nearly always the bitrate: try “Smooth”, or add a 30–50 ms "
    "buffer — or plug the cable in. Tip: drop a file on the window to send it to Downloads, "
    "or an APK to install it.":
        "Saccades ? En Wi-Fi, c'est presque toujours le débit : essaie « Fluide », ajoute un "
        "tampon de 30 à 50 ms, ou branche le câble. Astuce : glisse un fichier sur la fenêtre "
        "pour l'envoyer dans Téléchargements, ou un APK pour l'installer.",

    # Settings — webcam
    "Camera": "Caméra",
    "Front (selfie)": "Avant (selfie)",
    "Back": "Arrière",
    "Resolution": "Résolution",
    "Frame rate": "Images/s",
    "Show a preview on the computer": "Afficher un aperçu sur le PC",
    "Virtual webcam ready: “{name}” ({dev})": "Webcam virtuelle prête : « {name} » ({dev})",
    "No virtual webcam yet — a one-time setup is needed.":
        "Webcam virtuelle absente — une mise en place unique est nécessaire.",
    "How to set it up…": "Comment l'installer…",
}
