import streamlit as st
import speech_recognition as sr
import tempfile
from pathlib import Path
from datetime import datetime

# État pour mémoriser la dernière transcription
if "last_transcript" not in st.session_state:
    st.session_state["last_transcript"] = None


# Document cumulé (segments ajoutés au fil des transcriptions)
if "segments" not in st.session_state:
    st.session_state["segments"] = []  # liste de chaînes (chaque élément = une transcription)


# ---------- Config de page ----------
st.set_page_config(page_title="Reconnaissance vocale", page_icon="🎤")

st.title("🎤 Application de reconnaissance vocale")
st.caption("Étapes — Choix de l’API & de la langue, transcription d’un fichier audio (WAV/FLAC).")

# ---------- Aide / instructions ----------
with st.expander("📝 Instructions (ouvrir)"):
    st.markdown("""
    1. Choisissez l’**API** ci-dessous (Google par défaut).  
    2. Sélectionnez la **langue** (ex. Français `fr-FR`, Anglais `en-US`).  
    3. Importez un fichier **WAV** ou **FLAC** puis cliquez sur **Transcrire**.
    """)

# ---------- Choix de l’API ----------
API_CHOICES = {
    "Google Web Speech API (en ligne)": "google",
    "Sphinx (hors-ligne — nécessite `pocketsphinx`)": "sphinx",  # optionnelle
}
api_label = st.selectbox("API de reconnaissance", list(API_CHOICES.keys()))
api_choice = API_CHOICES[api_label]

# ---------- Choix de la langue ----------
LANG_MAP = {
    "Français (fr-FR)": "fr-FR",
    "Anglais (en-US)": "en-US",
    "Espagnol (es-ES)": "es-ES",
    "Arabe (ar-SA)": "ar-SA",
    "Wolof (wo-SN)*": "wo-SN",  # *les modèles peuvent être limités selon l'API
}
lang_label = st.selectbox("Langue parlée", list(LANG_MAP.keys()), index=0)
language_code = LANG_MAP[lang_label]

# ---------- Import de l'audio (fichier) ----------
audio_file = st.file_uploader("Fichier audio (WAV/FLAC)", type=["wav", "flac"])
if audio_file:
    st.audio(audio_file, format="audio/wav")


# Option: afficher les détails techniques en cas d'erreur
show_debug = st.checkbox("Afficher les détails techniques en cas d'erreur", value=False)



# ---------- Fonction de transcription (Étape 1 : Google + Sphinx basique) ----------
def transcribe_speech_from_file(uploaded_file, api: str, language: str):
    """
    Transcrit un fichier audio (WAV/FLAC) avec l'API choisie.
    Renvoie (message_utilisateur, debug_details) où:
      - message_utilisateur: texte final à afficher (succès ou message explicite)
      - debug_details: chaîne avec détails techniques (ou None)
    """
    recognizer = sr.Recognizer()

    # écrire le fichier uploadé dans un fichier temporaire
    suffix = "." + uploaded_file.name.split(".")[-1].lower()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = Path(tmp.name)
    except Exception as e:
        return ("❗️ Impossible de créer un fichier temporaire pour l'audio.", f"{type(e).__name__}: {e}")

    try:
        with sr.AudioFile(str(tmp_path)) as source:
            # astuce: normaliser un peu le signal
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.record(source)

        if api == "google":
            try:
                text = recognizer.recognize_google(audio, language=language)
                return (text, None)
            except sr.UnknownValueError as e:
                return ("❗️ L’API Google n’a pas compris l’audio. "
                        "Conseils: parlez plus fort, réduisez le bruit, vérifiez la langue choisie.",
                        f"{type(e).__name__}")
            except sr.RequestError as e:
                return ("❗️ Erreur de service Google (réseau/quota/clé). "
                        "Vérifiez votre connexion Internet, réessayez plus tard.",
                        f"{type(e).__name__}: {e}")

        elif api == "sphinx":
            try:
                # nécessite pocketsphinx installé pour fonctionner
                text = recognizer.recognize_sphinx(audio, language=language)
                return (text, None)
            except sr.UnknownValueError as e:
                return ("❗️ Sphinx n’a pas compris l’audio (souvent sensible à la qualité/anglais).",
                        f"{type(e).__name__}")
            except sr.RequestError as e:
                return ("❗️ Sphinx indisponible: il faut installer `pocketsphinx` localement "
                        "(ou choisissez Google Web Speech API).",
                        f"{type(e).__name__}: {e}")

        else:
            return ("❗️ API non reconnue.", f"api={api}")

    except FileNotFoundError as e:
        return ("❗️ Fichier introuvable. Re-uploadez l’audio.", f"{type(e).__name__}: {e}")
    except ValueError as e:
        return ("❗️ Format audio non supporté. Utilisez un fichier WAV ou FLAC.", f"{type(e).__name__}: {e}")
    except Exception as e:
        # garde-fou générique
        return ("❗️ Erreur inattendue lors de la transcription.", f"{type(e).__name__}: {e}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

# ---------- Bouton Transcrire ----------
col1, col2 = st.columns([1,1])
with col1:
    transcribe_btn = st.button("🗣️ Transcrire")

with col2:
    st.write("")  # espacement


if transcribe_btn:
    if audio_file is None:
        st.warning("Veuillez d’abord sélectionner un fichier audio WAV/FLAC.")
    else:
        with st.spinner("Transcription en cours..."):
            message, debug = transcribe_speech_from_file(audio_file, api_choice, language_code)

        st.markdown("**Transcription / Message :**")
        if message.startswith("❗️"):
            st.error(message)
            st.session_state["last_transcript"] = None  # on ne propose pas de téléchargement en cas d’erreur
        else:
            st.success("Transcription réussie.")
            st.write(message)
            st.session_state["last_transcript"] = message  # mémoriser pour télécharger

        if show_debug and debug:
            st.caption("Détails techniques (debug) :")
            st.code(debug)



# Si on a une transcription réussie, proposer de l'ajouter au "document"
if st.session_state.get("last_transcript"):
    c_add, c_reset = st.columns([1,1])
    with c_add:
        add_to_doc = st.button("➕ Ajouter ce résultat au document")
    with c_reset:
        reset_doc = st.button("🧹 Réinitialiser le document")

    if add_to_doc:
        st.session_state["segments"].append(st.session_state["last_transcript"])
        st.success("Segment ajouté au document ✅")

    if reset_doc:
        st.session_state["segments"].clear()
        st.info("Document vidé.")



# Proposer le téléchargement si on a une transcription en mémoire
if st.session_state.get("last_transcript"):
    fname = f"transcription_{API_CHOICES[api_label].split()[0]}_{language_code}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    st.download_button(
        "💾 Télécharger la transcription (.txt)",
        data=st.session_state["last_transcript"].encode("utf-8"),
        file_name=fname,
        mime="text/plain",
    )


# Affichage du document cumulé (si au moins un segment)
if st.session_state["segments"]:
    st.markdown("### 📄 Document cumulé")
    for i, seg in enumerate(st.session_state["segments"], 1):
        st.write(f"{i:02d}. {seg}")

    full_text = "\n".join(st.session_state["segments"]).strip()
    st.markdown("**Texte cumulé :**")
    st.write(full_text)

    from datetime import datetime
    fname = f"transcription_cumulee_{language_code}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    st.download_button(
        "💾 Télécharger le document cumulé (.txt)",
        data=full_text.encode("utf-8"),
        file_name=fname,
        mime="text/plain",
    )





