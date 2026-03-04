import streamlit as st
import librosa
import numpy as np
from music21 import stream, note, duration, key
import tempfile
import os

st.set_page_config(page_title="iPad 線上和聲產生器", layout="centered")
st.title("🎼 優化版：自動調性與和聲產生器")

def get_diatonic_harmony(melody_note_name, detected_key):
    """根據調性計算順階三度和聲音符"""
    try:
        m_note = note.Note(melody_note_name)
        # 在該調性的音階中找上方的第三個音
        # 例如 C 大調中，C 的三度是 E，D 的三度是 F
        scale = detected_key.getScale()
        h_note = m_note.transpose(detected_key.getScale().degreeToStep(3))
        return h_note
    except:
        # 如果判斷失敗，預設向上移 4 或 3 個半音
        return m_note.transpose(4)

def process_audio(audio_path):
    y, sr = librosa.load(audio_path)
    # 偵測音高
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6'))
    
    # 建立主旋律流以進行調性分析
    raw_melody = stream.Part()
    temp_notes = []
    for f in f0[::100]: # 抽樣降低運算負擔
        if not np.isnan(f):
            temp_notes.append(note.Note(librosa.hz_to_note(f)))
    raw_melody.append(temp_notes)
    
    # --- 自動分析調性 ---
    detected_key = raw_melody.analyze('key')
    st.info(f"偵測到調性：**{detected_key.name}**")

    # 建立正式樂譜
    score = stream.Score()
    p1 = stream.Part(id='Melody')
    p2 = stream.Part(id='Harmony')

    # 處理音符 (每 0.25 秒一拍)
    step = int(0.25 * sr / 512)
    for i in range(0, len(f0), step):
        f = f0[i]
        if not np.isnan(f):
            n_name = librosa.hz_to_note(f)
            m_n = note.Note(n_name, quarterLength=1.0)
            
            # 使用優化後的順階和聲邏輯
            h_n = get_diatonic_harmony(n_name, detected_key)
            h_n.quarterLength = 1.0
            
            p1.append(m_n)
            p2.append(h_n)
        else:
            p1.append(note.Rest(quarterLength=1.0))
            p2.append(note.Rest(quarterLength=1.0))

    score.insert(0, p1)
    score.insert(0, p2)
    return score

# --- 前端介面 ---
uploaded_file = st.file_uploader("iPad 錄音或上傳音訊", type=["wav", "mp3", "m4a"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(uploaded_file.read())
        
    if st.button("生成線上樂譜"):
        with st.spinner("正在分析旋律並計算和聲..."):
            my_score = process_audio(tmp.name)
            xml_path = "result.xml"
            my_score.write('musicxml', fp=xml_path)
            
            with open(xml_path, "rb") as f:
                st.download_button("📥 下載 MusicXML 樂譜", f, "my_harmony.xml")
    os.remove(tmp.name)
