import streamlit as st
from google import genai
import PIL.Image

# --- 1. 세션 상태 초기화 ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_solution' not in st.session_state:
    st.session_state.current_solution = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'last_processed_image' not in st.session_state:
    st.session_state.last_processed_image = None

# --- 2. 화면 설정 및 카메라 화면 키우기 (CSS 마법) ---
st.set_page_config(page_title="AI 수학 선생님", layout="wide", page_icon="🎓")

# HTML/CSS를 주입해서 카메라 비디오 화면을 가로 100%로 꽉 채웁니다.
st.markdown("""
    <style>
    [data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. API 키 처리 ---
try:
    api_key = st.secrets['GOOGLE_API_KEY']
except Exception:
    api_key = st.sidebar.text_input("Gemini API 키를 입력하세요", type="password")

st.title("🎓 AI 수학 선생님")

# --- 4. 메인 화면 ---
col1, col2 = st.columns([2, 1])

with col1:
    tab1, tab2 = st.tabs(["📸 카메라로 바로 찍기", "🖼️ 앨범에서 사진 고르기"])
    
    uploaded_file = None
    
    with tab1:
        camera_file = st.camera_input("문제 영역이 잘 보이게 찍어주세요")
        if camera_file:
            uploaded_file = camera_file
            
    with tab2:
        gallery_file = st.file_uploader("사진 파일을 선택하세요", type=["jpg", "jpeg", "png"])
        if gallery_file:
            uploaded_file = gallery_file
    
    # --- 핵심 변경: 사진이 들어오면 '버튼 없이' 바로 실행! ---
    if uploaded_file and api_key:
        image = PIL.Image.open(uploaded_file)
        
        # 똑같은 사진을 두 번 연속 분석하지 않도록 방지하는 장치입니다.
        if st.session_state.last_processed_image != uploaded_file.getvalue():
            # 사진이 바뀌었으면 즉시 분석 시작
            with st.spinner("✨ 선생님이 문제를 바로 풀고 있습니다... 뚝딱뚝딱!"):
                try:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=["너는 친절하고 꼼꼼한 수학 선생님이야. 이 문제의 풀이 과정을 단계별로 자세히 설명하고, 마지막에 정답을 명확히 알려줘.", image]
                    )
                    st.session_state.current_solution = response.text
                    st.session_state.current_image = image
                    st.session_state.last_processed_image = uploaded_file.getvalue()
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    # 결과 출력 (자동으로 뜹니다)
    if st.session_state.current_solution:
        st.divider()
        st.subheader("💡 해설지")
        st.markdown(st.session_state.current_solution)
        
        if st.button("💾 내 오답노트에 저장하기", use_container_width=True):
            st.session_state.history.append({
                "image": st.session_state.current_image,
                "solution": st.session_state.current_solution
            })
            st.toast("오답노트에 저장되었어요!", icon="🎉")

with col2:
    st.write("### 📚 나의 오답노트")
    if len(st.session_state.history) == 0:
        st.info("저장된 문제가 없습니다.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📌 문제 기록 {len(st.session_state.history) - i}"):
                st.image(item["image"], use_column_width=True)
                st.markdown(item["solution"])

