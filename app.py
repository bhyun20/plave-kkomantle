import streamlit as st
import fitz  # PyMuPDF
import os
import random
from datetime import date
from kiwipiepy import Kiwi
from collections import Counter
import math

# --- 1. 데이터 학습 및 유사도 엔진 (내장 방식) ---
@st.cache_resource
def prepare_plave_engine():
    kiwi = Kiwi()
    pdf_texts = ""
    for filename in os.listdir('.'):
        if filename.endswith('.pdf'):
            doc = fitz.open(filename)
            for page in doc:
                pdf_texts += page.get_text() + "\n"
    
    # 단어별 문맥 파악을 위한 데이터 구조 생성
    tokens = kiwi.tokenize(pdf_texts)
    words = [t.form for t in tokens if t.tag.startswith('N') or t.tag == 'SL']
    
    # 단어 간 공기(Co-occurrence) 빈도 계산
    word_counts = Counter(words)
    return word_counts, words

def calculate_score(target, guess, all_words):
    if target == guess: return 100.0
    if guess not in all_words: return 0.0
    
    # 단순 빈도와 거리 기반의 유사도 시뮬레이션 로직
    # (실제 꼬맨틀의 느낌을 내기 위해 텍스트 내 거리 기반 점수 부여)
    indices_target = [i for i, x in enumerate(all_words) if x == target]
    indices_guess = [i for i, x in enumerate(all_words) if x == guess]
    
    min_dist = float('inf')
    for t_idx in indices_target:
        for g_idx in indices_guess:
            dist = abs(t_idx - g_idx)
            if dist < min_dist: min_dist = dist
    
    # 거리가 가까울수록 높은 점수 (최대 100점, 최소 0점)
    score = max(0, 100 - (math.log(min_dist + 1) * 10))
    return round(score, 2)

# --- 2. 웹 UI 및 로직 ---
st.set_page_config(page_title="PLAVE 꼬맨틀", page_icon="💙")
st.title("💙 플레이브 꼬맨틀")
st.write("아스테룸의 지식을 바탕으로 오늘의 단어를 맞춰보세요!")

with st.spinner('데이터를 분석 중입니다...'):
    word_counts, all_words = prepare_plave_engine()

# 매일 바뀌는 정답 후보
target_pool = ["예준", "노아", "밤비", "은호", "하민", "플레이브", "PLLI", "아스테룸", "카엘룸", "테라", "냥냥즈", "야타즈", "댕댕즈", "맏형즈", "쁜라인"]
valid_targets = [w for w in target_pool if w in word_counts]
today_seed = date.today().strftime("%Y%m%d")
random.seed(today_seed)
target_word = random.choice(valid_targets)

if 'history' not in st.session_state:
    st.session_state.history = []

with st.form(key='guess_form', clear_on_submit=True):
    user_input = st.text_input("단어 입력:").strip()
    submit = st.form_submit_button('확인')

if submit and user_input:
    if user_input == target_word:
        st.balloons()
        st.success(f"🎊 정답입니다! 오늘의 단어는 '{target_word}'였습니다!")
    elif user_input not in word_counts:
        st.warning(f"'{user_input}'은(는) 문서에 등장하지 않는 단어입니다.")
    else:
        score = calculate_score(target_word, user_input, all_words)
        st.session_state.history.append({"단어": user_input, "점수": score})
        st.session_state.history.sort(key=lambda x: x['점수'], reverse=True)

if st.session_state.history:
    st.write("### 추측 기록")
    for item in st.session_state.history:
        st.write(f"- **{item['단어']}**: {item['점수']}점")