import streamlit as st
from google import genai
import PIL.Image
import PIL.ImageOps
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
        
        # 1. 자동 방향 수정
        img = PIL.ImageOps.exif_transpose(img)
        
        # 2. 회전 조절
        st.write("#### 🔄 사진 방향 조절")
        r_col1, r_col2, r_col3 = st.columns(3)
        if r_col1.button("↩️ 왼쪽 회전"):
            st.session_state.rotation += 90
        if r_col2.button("↪️ 오른쪽 회전"):
            st.session_state.rotation -= 90
        if r_col3.button("🧹 초기화"):
            st.session_state.rotation = 0
            
        if st.session_state.rotation != 0:
            img = img.rotate(st.session_state.rotation, expand=True)

        # 3. [핵심] 편집창이 화면 밖으로 나가지 않게 이미지 크기를 미리 줄임
        # 가로 400픽셀을 기준으로 비율에 맞춰 축소
        max_width = 400
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), PIL.Image.Resampling.LANCZOS)

        st.write("#### ✂️ 문제 영역 선택")
        st.info("빨간 사각형을 조절해 문제만 가둬주세요!")
        
        # 에러를 일으켰던 canvas_size를 빼고 실행합니다.
        final_image = st_cropper(
            img, 
            realtime_update=True, 
            box_color='#FF0000', 
            aspect_ratio=None, 
            return_type='image'
        )
        
        if final_image:
            st.write("▼ 편집된 이미지 확인")
            st.image(final_image, width=200)

    # --- 🤖 문제 풀기 실행 ---
    if final_image and api_key:
        if st.button("✨ 선생님! 이 영역 해설해주세요", type="primary", use_container_width=True):
            # 편집된 이미지의 데이터를 체크용으로 변환
            img_bytes = io.BytesIO()
            final_image.save(img_bytes, format='PNG')
            current_img_data = img_bytes.getvalue()
            
            # 중복 실행 방지 체크
            if st.session_state.last_processed_image != current_img_data:
                with st.spinner("🔍 선생님이 문제를 분석 중..."):
                    try:
                        # 1. Gemini 클라이언트 연결
                        client = genai.Client(api_key=api_key)
                        
                        # 2. 핵심만 집어주는 일타강사 주문서(프롬프트)
                        prompt = """
                        너는 핵심만 찌르는 명쾌한 수학 선생님이야. 
                        사진 속 문제를 분석해서 다음 양식에 맞춰 아주 간결하게 설명해줘.
                        
                        1. **핵심 개념**: 문제 풀이에 필요한 공식이나 원리 (한 줄 요약)
                        2. **풀이 과정**: 단계별로 번호를 매겨서 설명 (최대 4단계)
                        3. **최종 정답**: 결과값을 명확하게 강조
                        
                        * 답변은 친절하되, 장황한 설명은 절대 생략할 것.
                        """
                        
                        # 3. AI에게 분석 요청
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[prompt, final_image]
                        )
                        
                        # 4. 결과 저장
                        st.session_state.current_solution = response.text
                        st.session_state.current_image = final_image
                        st.session_state.last_processed_image = current_img_data
                        
                    except Exception as e:
                        # 이 부분이 사라졌거나 들여쓰기가 틀리면 에러가 납니다!
                        st.error(f"오류가 발생했습니다: {e}")

    # --- 결과 출력 영역 ---
    if st.session_state.current_solution:
        st.divider()
        st.subheader("💡 해설지")
        st.markdown(st.session_state.current_solution)
        
        if st.button("💾 이 해설을 오답노트에 저장", use_container_width=True):
            st.session_state.history.append({
                "image": st.session_state.current_image,
                "solution": st.session_state.current_solution
            })
            st.toast("오답노트에 저장 완료! 🎉")

with col2:
    st.write("### 📚 나의 오답노트")
    if not st.session_state.history:
        st.info("저장된 기록이 없습니다.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📌 문제 {len(st.session_state.history) - i}"):
                st.image(item["image"], use_column_width=True)
                st.markdown(item["solution"])






