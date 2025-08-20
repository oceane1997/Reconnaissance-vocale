# Reconnaissance vocale — Streamlit
Appli de reconnaissance vocale à partir de fichiers audio (WAV/FLAC) avec SpeechRecognition, déployable sur Streamlit Cloud.

##  Fonctionnalités
Choix d’API : Google Web Speech (en ligne) ou Sphinx (hors-ligne, local seulement).

Erreurs lisibles : messages clairs + option “détails techniques”.

Export : bouton pour télécharger la transcription en .txt.

Langue : sélection du code BCP-47 (ex. fr-FR, en-US).

Pause / Reprendre : cumulez plusieurs transcriptions (segments) et exportez le document cumulé.

##  Utilisation
Choisissez API et langue.

Importez un WAV/FLAC puis Transcrire.

Option : “Télécharger la transcription (.txt)”.

Pour pause/reprendre : après chaque transcription réussie, cliquez “➕ Ajouter ce résultat au document”, puis téléchargez le document cumulé.

##  Notes
Google nécessite Internet ; Sphinx (hors-ligne) demande pocketsphinx (plutôt en local, pas sur Cloud).

Messages d’erreur utiles : audio inaudible, format non supporté, service indisponible, etc.

Formats recommandés : WAV ou FLAC (supportés nativement).
