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

# --- 2. 화면 설정 ---
st.set_page_config(page_title="AI 수학 선생님", layout="wide", page_icon="🎓")

# --- 3. API 키 처리 (자동 감지) ---
# 클라우드에 저장된 키(Secrets)가 있으면 그걸 쓰고, 없으면 사이드바에서 입력받음
if 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets['GOOGLE_API_KEY']
    st.sidebar.success("✅ API 키가 클라우드에서 안전하게 로드되었습니다.")
else:
    api_key = st.sidebar.text_input("Gemini API 키를 입력하세요", type="password")
    if not api_key:
        st.sidebar.warning("API 키를 입력해야 작동합니다.")

st.title("🎓 내 손안의 AI 수학 선생님")
st.write("문제를 찍거나 앨범에서 선택하면 해설해 드려요!")

# --- 4. 메인 화면 구성 (왼쪽: 입력 / 오른쪽: 기록) ---
col1, col2 = st.columns([2, 1])

with col1:
    st.write("### 📸 문제 업로드")
    # 예쁜 카메라 버튼을 위해 file_uploader 사용 (모바일 친화적)
    uploaded_file = st.file_uploader("카메라 아이콘을 눌러 사진을 찍으세요", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = PIL.Image.open(uploaded_file)
        st.image(image, caption="선택한 이미지", use_column_width=True)

        if api_key:
            client = genai.Client(api_key=api_key)
            # 버튼 디자인을 위해 type="primary" 적용
            if st.button("✨ AI 선생님! 해설해주세요", type="primary", use_container_width=True):
                with st.spinner("선생님이 문제를 분석하고 있습니다... 잠시만 기다려주세요!"):
                    try:
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=["너는 친절하고 꼼꼼한 수학 선생님이야. 이 문제의 풀이 과정을 단계별로 자세히 설명하고, 마지막에 정답을 명확히 알려줘.", image]
                        )
                        st.session_state.current_solution = response.text
                        st.session_state.current_image = image
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

    # 해설 결과 표시 영역
    if st.session_state.current_solution:
        st.divider()
        st.subheader("💡 해설지")
        st.markdown(st.session_state.current_solution)

        if st.button("💾 내 오답노트에 저장하기", use_container_width=True):
            st.session_state.history.append({
                "image": st.session_state.current_image,
                "solution": st.session_state.current_solution
            })
            st.toast("오답노트에 저장되었어요!", icon="🎉")  # 알림 메시지 띄우기

with col2:
    st.write("### 📚 나의 오답노트")
    if len(st.session_state.history) == 0:
        st.info("저장된 문제가 없습니다.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):  # 최신순으로 보여주기
            with st.expander(f"📌 문제 기록 {len(st.session_state.history) - i}"):
                st.image(item["image"], use_column_width=True)
                st.markdown(item["solution"])