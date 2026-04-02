import streamlit as st
import fitz  # PyMuPDF
import os
import random
from datetime import date
from kiwipiepy import Kiwi
from gensim.models import Word2Vec

# --- 1. 기본 설정 및 데이터 학습 (캐싱 처리하여 속도 최적화) ---
@st.cache_resource
def train_plave_ai():
    kiwi = Kiwi()
    pdf_texts = ""
    # 같은 폴더에 있는 모든 PDF 읽기
    for filename in os.listdir('.'):
        if filename.endswith('.pdf'):
            doc = fitz.open(filename)
            for page in doc:
                pdf_texts += page.get_text() + "\n"
    
    sentences = kiwi.split_into_sents(pdf_texts)
    processed_data = []
    for sent in sentences:
        tokens = kiwi.tokenize(sent.text)
        words = [t.form for t in tokens if t.tag.startswith('N') or t.tag == 'SL']
        if words: processed_data.append(words)
    
    model = Word2Vec(sentences=processed_data, vector_size=100, window=5, min_count=2, sg=1)
    return model

# --- 2. 매일 바뀌는 정답 선정 로직 ---
def get_daily_target(model):
    # 정답 후보군 (제공해주신 문서 기반 핵심 단어들)
    target_pool = [
        "예준", "노아", "밤비", "은호", "하민", "플레이브", "PLLI", "폴리",
        "아스테룸", "카엘룸", "테라", "맏형즈", "베리즈", "댕댕즈", "예라인",
        "쁜라인", "노라인", "야타즈", "냥냥즈", "댄라즈", "댕냥즈", "도크루",
        "기다릴게", "여섯번째여름", "WAY4LUV", "Dash", "BBUU", "노스라이팅", "안바빠"
    ]
    # AI가 학습한 단어만 필터링
    valid_targets = [w for w in target_pool if w in model.wv]
    
    # 오늘 날짜를 숫자로 바꿔서 '랜덤 시드'로 사용 (모두에게 같은 정답 제공)
    today_seed = date.today().strftime("%Y%m%d")
    random.seed(today_seed)
    return random.choice(valid_targets)

# --- 3. 웹 UI 구성 ---
st.set_page_config(page_title="PLAVE 꼬맨틀", page_icon="💙")
st.title("💙 플레이브 꼬맨틀")
st.write("단어의 의미적 유사도를 이용해 오늘의 정답을 맞혀보세요!")

# AI 로딩
with st.spinner('아스테룸의 지식을 불러오는 중...'):
    model = train_plave_ai()

target_word = get_daily_target(model)

# 게임 진행 세션 상태 관리
if 'history' not in st.session_state:
    st.session_state.history = []

# 단어 입력창
with st.form(key='guess_form', clear_on_submit=True):
    user_input = st.text_input("단어를 입력하세요:").strip()
    submit_button = st.form_submit_button(label='입력')

if submit_button and user_input:
    if user_input == target_word:
        st.balloons()
        st.success(f"🎉 정답입니다! 오늘의 단어는 '{target_word}'였습니다!")
    elif user_input not in model.wv:
        st.warning(f"'{user_input}'은(는) AI가 모르는 단어입니다.")
    else:
        # 유사도 계산
        sim = model.wv.similarity(target_word, user_input)
        score = round((sim + 1) / 2 * 100, 2)
        st.session_state.history.append({"단어": user_input, "점수": score})
        # 점수 높은 순으로 정렬
        st.session_state.history.sort(key=lambda x: x['점수'], reverse=True)

# 시도한 기록 표시
if st.session_state.history:
    st.write("### 추측 기록")
    for item in st.session_state.history:
        color = "red" if item['점수'] > 80 else "orange" if item['점수'] > 60 else "black"
        st.write(f"- **{item['단어']}**: :{color}[{item['점수']}점]")