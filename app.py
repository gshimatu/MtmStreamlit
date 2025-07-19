import streamlit as st
import os
import subprocess
import tempfile
import time
import base64
import platform
import shutil

# --- Configuration ---
# Limite de taille de fichier à 500 Mo
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Configuration de la page et style ---
st.set_page_config(
    page_title="Convertisseur MP4 en MP3",
    page_icon="logo.ico",
    layout="centered"
)

# Injection de CSS 
st.markdown("""
    <style>
    .st-emotion-cache-18ni7ap {
        background-color: #03333c;
        border: none;
    }
    .st-emotion-cache-1j0d76g {
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        border-radius: 20px;
    }
    .st-emotion-cache-163j06l {
        color: #3fd3ca;
    }
    .st-emotion-cache-16ajigk {
        background: linear-gradient(-45deg, #03333c, #011920, #044349, #011e23);
        background-size: 400% 400%;
        animation: backgroundShift 15s ease infinite;
        color: #fff;
    }
    @keyframes backgroundShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .hero-title {
        color: #03333c;
        font-size: 2.25rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    .hero-subtext {
        color: #9ca3af;
        font-size: 0.875rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .glass-box {
        backdrop-filter: blur(12px);
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        border-radius: 20px;
        padding: 2rem;
    }
    .stFileUploader {
        border: 2px dashed #d1d5db !important;
        border-radius: 0.75rem !important;
        background-color: #fff !important;
    }
    .stDownloadButton {
        background: linear-gradient(90deg, #ec4899 0%, #8b5cf6 100%);
        color: #fff;
        font-weight: bold;
        border-radius: 1rem;
        box-shadow: 0 4px 24px rgba(139, 92, 246, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        border: none !important;
    }
    .stDownloadButton:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 32px rgba(236, 72, 153, 0.3);
    }
    .logo-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 1.5rem;
        width: 100px;
        height: 100px;
        border-radius: 20px;
        box-shadow: 0 2px 12px rgba(63, 211, 202, 0.15);
        background: #fff;
        object-fit: contain;
    }
    .footer-photo {
        width: 60px;
        height: 60px;
        object-fit: cover;
        border-radius: 50%;
        border: 3px solid #3fd3ca;
        box-shadow: 0 2px 8px rgba(63, 211, 202, 0.15);
        margin-right: 1rem;
        background: #fff;
    }
    .footer-author {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-top: 1.5rem;
        color: #03333c;
        font-weight: 500;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Logo en haut de l'application ---
st.image("logo.png", width=100, output_format="PNG", caption=None, use_container_width=False)

# --- Fonctions  ---
def convert_mp4_to_mp3(input_file_path, output_dir):
    """
    Convertit un fichier vidéo MP4 en un fichier audio MP3 en utilisant FFmpeg.
    """
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_mp3_name = f"{base_name}.mp3"
    output_mp3_path = os.path.join(output_dir, output_mp3_name)

    # 1. Cherche ffmpeg globalement (dans le PATH)
    ffmpeg_path = shutil.which("ffmpeg")

    # 2. Sinon, tente le binaire local dans bin/
    if not ffmpeg_path:
        if platform.system() == 'Windows':
            ffmpeg_filename = "ffmpeg.exe"
        else:
            ffmpeg_filename = "ffmpeg"
        local_ffmpeg = os.path.join(os.getcwd(), "bin", ffmpeg_filename)
        if os.path.isfile(local_ffmpeg):
            # Sur Windows, pas besoin de vérifier les droits d'exécution
            if platform.system() == 'Windows' or os.access(local_ffmpeg, os.X_OK):
                ffmpeg_path = local_ffmpeg
    
    # 3. Si aucun binaire trouvé, affiche une erreur
    if not ffmpeg_path:
        st.error("Erreur : FFmpeg n'est pas disponible sur ce système. Installez-le globalement ou placez le binaire dans le dossier bin/ de votre projet.")
        return None

    command = [
        ffmpeg_path,
        "-i", input_file_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        output_mp3_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return output_mp3_path
    except FileNotFoundError:
        st.error("Erreur : FFmpeg n'a pas été trouvé. Veuillez vous assurer qu'il est installé globalement ou dans le dossier bin de votre projet.")
        return None
    except subprocess.CalledProcessError as e:
        st.error(f"Erreur lors de la conversion : {e.stderr}")
        return None

def get_binary_file_downloader_html(file_path, file_name):
    """Génère un lien de téléchargement HTML pour un fichier."""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f"""
        <a href="data:file/mp3;base64,{b64}" download="{file_name}">
            <button class="stDownloadButton">Télécharger votre MP3</button>
        </a>
    """

# --- Interface de l'application principale ---
st.markdown('<div class="glass-box">', unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align: center;">
        <i class="fas fa-file-audio" style="font-size: 3rem; color: #3fd3ca; margin-bottom: 1rem;"></i>
        <h1 class="hero-title">
            Convertisseur MP4 <span style="color: #3fd3ca;">→</span> MP3
        </h1>
        <p class="hero-subtext">
            Transformez vos vidéos en fichiers audio de haute qualité et gratuitement !
        </p>
    </div>
    """, unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Glissez-déposez votre fichier ou cliquez pour parcourir",
    type=['mp4'],
    accept_multiple_files=False
)

if uploaded_file is not None:
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        st.error(f"La taille du fichier excède la limite de {MAX_FILE_SIZE_MB} Mo.")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_path = os.path.join(temp_dir, uploaded_file.name)

            with open(temp_video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.info(f"Fichier sélectionné : {uploaded_file.name}")

            if st.button("Convertir en MP3", key="convert_btn"):
                with st.spinner("Conversion en cours..."):
                    mp3_path = convert_mp4_to_mp3(temp_video_path, temp_dir)

                if mp3_path:
                    st.success("Conversion terminée avec succès !")
                    st.markdown(get_binary_file_downloader_html(mp3_path, os.path.basename(mp3_path)), unsafe_allow_html=True)

# Section bas de page
# Remplacer la balise <img> par st.image dans une disposition centrée
footer_col1, footer_col2 = st.columns([1, 8])
with footer_col1:
    st.image("Shimatologue.jpg", width=60, output_format="JPEG", use_container_width=False)
with footer_col2:
    st.markdown('<span style="color:#03333c; font-weight:500; font-size:1.1rem; vertical-align:middle;">Gauthier Shimatu (le Shimatologue)</span>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)