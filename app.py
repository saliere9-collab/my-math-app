import streamlit as st
from google import genai
import PIL.Image
from streamlit_cropper import st_cropper # 새로운 라이브러리 가져오기
import io

# --- 1. 세션 상태 초기화 ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_solution' not in st.session_state:
    st.session_state.current_solution = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'last_processed_image' not in st.session_state:
    st.session_state.last_processed_image = None

# --- 2. 화면 설정 ---
st.set_page_config(page_title="AI 수학 선생님", layout="wide", page_icon="🎓")

# --- 3. API 키 처리 ---
try:
    api_key = st.secrets['GOOGLE_API_KEY']
except Exception:
    api_key = st.sidebar.text_input("Gemini API 키를 입력하세요", type="password")

st.title("🎓 내 손안의 AI 수학 선생님")

# --- 4. 메인 화면 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.write("### 📸 문제 업로드 & 편집")
    st.info("💡 팁: 사진을 올린 후, 아래 편집기에서 문제 영역만 지정해 주세요. 가로/세로 비율은 자유롭게 조절 가능합니다.")
    
    # 파일 업로드
    uploaded_file = st.file_uploader("찍어둔 문제 사진을 올려주세요", type=["jpg", "jpeg", "png"])
    
    # 편집된 이미지를 담을 변수
    final_image = None
    
    if uploaded_file:
        img = PIL.Image.open(uploaded_file)
        
        # --- ✂️ 이미지 편집 도구 (Cropper) 배치 ---
        st.write("#### ✂️ 문제 영역 자르기")
        
        # 사이드바에 회전 제어판 만들기
        st.sidebar.write("---")
        st.sidebar.write("### 🔄 이미지 회전")
        # 90도씩 회전시키는 버튼
        if st.sidebar.button("↪️ 시계 방향으로 90도 회전"):
            img = img.rotate(-90, expand=True)
        if st.sidebar.button("↩️ 반시계 방향으로 90도 회전"):
            img = img.rotate(90, expand=True)
            
        # 자르기 도구 실행 (aspect_ratio=None 으로 설정하여 자유 비율로 자르기)
        # 중요: 편집 도구 아래에 '편집 완료' 버튼이 생깁니다.
        final_image = st_cropper(img, realtime_update=False, box_color='#FF0000', aspect_ratio=None, return_type='image')
        
        if final_image:
            st.success("✅ 편집 완료! 아래 버튼을 누르면 선생님이 문제를 풉니다.")
            st.image(final_image, caption="분석에 사용할 편집된 이미지", width=300)

    # --- 🤖 문제 풀기 실행 (버튼 방식으로 변경) ---
    # 편집이 중요한 앱이므로, 자동 실행 대신 편집 확인 후 버튼을 누르는 방식으로 변경합니다.
    if final_image and api_key:
        if st.button("✨ 선생님! 이 영역을 해설해주세요", type="primary", use_container_width=True):
            # 편집된 이미지의 바이트 데이터를 가져와서 중복 체크
            img_bytes = io.BytesIO()
            final_image.save(img_bytes, format='PNG')
            current_img_data = img_bytes.getvalue()
            
            if st.session_state.last_processed_image != current_img_data:
                with st.spinner("✨ 선생님이 문제를 분석하고 있습니다... 뚝딱뚝딱!"):
                    try:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=["너는 친절하고 꼼꼼한 수학 선생님이야. 이 문제의 풀이 과정을 단계별로 자세히 설명하고, 마지막에 정답을 명확히 알려줘.", final_image]
                        )
                        st.session_state.current_solution = response.text
                        st.session_state.current_image = final_image
                        st.session_state.last_processed_image = current_img_data
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

    # 결과 출력
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
                
# io 라이브러리가 필요해서 맨 위에 추가해줍니다 (코드가 복잡해 보여서 설명만 드리고 코드 내에 포함시켰습니다)
import io



