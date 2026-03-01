import streamlit as st
from google import genai
import PIL.Image
import PIL.ImageOps  # 사진 방향을 바로잡기 위해 추가
from streamlit_cropper import st_cropper
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
if 'rotation' not in st.session_state:
    st.session_state.rotation = 0

# --- 2. 화면 설정 ---
st.set_page_config(page_title="AI 수학 선생님", layout="wide", page_icon="🎓")

# --- 3. API 키 처리 ---
try:
    api_key = st.secrets['GOOGLE_API_KEY']
except Exception:
    api_key = st.sidebar.text_input("Gemini API 키를 입력하세요", type="password")

st.title("🎓 내 손안의 AI 수학 선생님")

col1, col2 = st.columns([2, 1])

with col1:
    st.write("### 📸 문제 업로드 & 편집")
    uploaded_file = st.file_uploader("찍어둔 문제 사진을 올려주세요", type=["jpg", "jpeg", "png"])
    
    final_image = None
    
    if uploaded_file:
        # 사진 불러오기
        img = PIL.Image.open(uploaded_file)
        
        # [수정 1] 핸드폰 사진의 돌아간 방향을 자동으로 바로잡기
        img = PIL.ImageOps.exif_transpose(img)
        
        # [수정 2] 회전 버튼을 편집창 바로 위로 배치 (모바일에서 누르기 좋게)
        st.write("#### 🔄 사진 방향 조절")
        r_col1, r_col2, r_col3 = st.columns(3)
        if r_col1.button("↩️ 왼쪽 회전"):
            st.session_state.rotation += 90
        if r_col2.button("↪️ 오른쪽 회전"):
            st.session_state.rotation -= 90
        if r_col3.button("🧹 초기화"):
            st.session_state.rotation = 0
            
        # 회전 적용
        if st.session_state.rotation != 0:
            img = img.rotate(st.session_state.rotation, expand=True)

        # [수정 3] 편집창이 화면 밖으로 나가지 않게 크기 제한
        st.write("#### ✂️ 문제 영역 선택")
        st.info("빨간 사각형을 조절해 문제만 가둬주세요!")
        
        # canvas_size를 400으로 제한하여 모바일 화면에 쏙 들어가게 만듭니다.
        final_image = st_cropper(
            img, 
            realtime_update=True, 
            box_color='#FF0000', 
            aspect_ratio=None, 
            return_type='image',
            canvas_size=400 # 이 설정이 화면 탈출을 막아줍니다!
        )
        
        if final_image:
            st.image(final_image, caption="이 영역을 분석합니다", width=200)

    # --- 🤖 문제 풀기 실행 ---
    if final_image and api_key:
        if st.button("✨ 선생님! 이 영역 해설해주세요", type="primary", use_container_width=True):
            img_bytes = io.BytesIO()
            final_image.save(img_bytes, format='PNG')
            current_img_data = img_bytes.getvalue()
            
            if st.session_state.last_processed_image != current_img_data:
                with st.spinner("🔍 선생님이 문제를 분석 중..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=["너는 친절한 수학 선생님이야. 이 문제의 풀이 과정을 단계별로 자세히 설명하고 정답을 알려줘.", final_image]
                        )
                        st.session_state.current_solution = response.text
                        st.session_state.current_image = final_image
                        st.session_state.last_processed_image = current_img_data
                    except Exception as e:
                        st.error(f"오류: {e}")

    if st.session_state.current_solution:
        st.divider()
        st.subheader("💡 해설지")
        st.markdown(st.session_state.current_solution)
        
        if st.button("💾 오답노트 저장", use_container_width=True):
            st.session_state.history.append({
                "image": st.session_state.current_image,
                "solution": st.session_state.current_solution
            })
            st.toast("저장 완료! 🎉")

with col2:
    st.write("### 📚 나의 오답노트")
    if not st.session_state.history:
        st.info("저장된 기록이 없습니다.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📌 문제 {len(st.session_state.history) - i}"):
                st.image(item["image"], use_column_width=True)
                st.markdown(item["solution"])



