import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 페이지 기본 설정
st.set_page_config(page_title="경덕초등학교 환경소양 측정 시스템", layout="wide")

# 메인 화면 상단 헤더 표기
st.markdown("<h1 style='text-align: center; color: #2A9D8F;'>🏫 경덕초등학교 환경소양 측정 시스템</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.05em; color: #444;'>설문도구는 다음 논문을 참고하여 제작함(*남미리 · 강진영 · 김정훈 · 김찬국 (초등학생용 환경소양 측정도구 개발, 2021))</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 0.85em; color: #999; font-style: italic;'>본 프로그램은 Google Gemini(제미나이) AI를 활용하여 작성되었습니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# -------------------------------------------------------------------------
# 🔗 [핵심] 구글 스프레드시트 실시간 연동 로직
# -------------------------------------------------------------------------
# Streamlit의 구글시트 커넥터 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 구글 시트에서 데이터 읽어오기 (ttl=0으로 설정하여 캐시 없이 실시간 데이터 로드)
try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    # 빈 시트이거나 깨진 경우를 대비해 무조건 데이터프레임 형태로 강제 변환
    df = pd.DataFrame(df)
except Exception:
    # 시트가 완전히 비어있을 때의 기본 열 구성
    columns = ["학생 식별자", "학년", "반", "번호", "차수"] + [f"지식_Q{i}" for i in range(1, 9)] + [f"정서_Q{i}" for i in range(9, 19)] + [f"실천_Q{i}" for i in range(19, 29)]
    df = pd.DataFrame(columns=columns)

# 만약 읽어온 데이터에 필수 컬럼이 없으면 에러 방지용 빈 데이터프레임 생성
if df.empty or "학생 식별자" not in df.columns:
    columns = ["학생 식별자", "학년", "반", "번호", "차수"] + [f"지식_Q{i}" for i in range(1, 9)] + [f"정서_Q{i}" for i in range(9, 19)] + [f"실천_Q{i}" for i in range(19, 29)]
    df = pd.DataFrame(columns=columns)

KNOWLEDGE_ANSWERS = {
    "Q1": 2, "Q2": 3, "Q3": 3, "Q4": 2, "Q5": 1,
    "Q6": ["1", "4"], "Q7": ["2", "4"], "Q8": ["2", "4"]
}

def score_knowledge(row):
    score = 0
    for i in range(1, 6):
        if int(row[f"지식_Q{i}"]) == KNOWLEDGE_ANSWERS[f"Q{i}"]: score += 1
    for i in range(6, 9):
        ans_list = str(row[f"지식_Q{i}"]).split(",")
        if sorted(ans_list) == sorted(KNOWLEDGE_ANSWERS[f"Q{i}"]): score += 1
    return (score / 8) * 100

# 메뉴 구성
menu = st.sidebar.radio("원하는 메뉴를 선택하세요", ["📝 학생용 설문조사 입력", "📊 교사용 결과 분석 대시보드"])

# -------------------------------------------------------------------------
# 학생용 설문조사 입력 화면
# -------------------------------------------------------------------------
if menu == "📝 학생용 설문조사 입력":
    st.subheader("🌱 학생용 환경소양 조사지")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: s_grade = st.selectbox("학년", [1, 2, 3, 4, 5, 6], index=3)
    with col2: s_class = st.number_input("반", min_value=1, max_value=15, value=1, step=1)
    with col3: s_num = st.number_input("번호", min_value=1, max_value=60, value=1, step=1)
    with col4: s_round = st.radio("제출 차수", ["1차 (4월)", "2차 (9월)"], horizontal=True)

    student_id = f"{s_grade}학년 {s_class}반 {s_num}번"
    st.markdown("---")
    answers = {}
    
    with st.form("survey_form"):
        st.markdown("#### [1] 환경지식 영역")
        answers["지식_Q1"] = st.radio("1. 환경에 관한 다음 설명 중, 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 동물과 식물은 흙, 공기, 물 등과 서로 관련이 없다.", "② 우리가 관계를 맺고 있는 주변의 모든 것은 환경이다.", "③ 환경에서 흙, 공기, 물 등은 서로 영향을 주고받지 않는다.", "④ 환경은 동물이나 식물과 같이 살아있는 생물 사이의 관계를 의미한다."][x-1])
        answers["지식_Q2"] = st.radio("2. 우리 생활과 자연환경의 관계에 대한 설명이다. 다음 중 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 우리의 생활 방식이 편리하게 바뀌어도, 자연환경은 그대로 유지된다.", "② 자연환경의 변화는 우리의 소비나 생활 방식에 영향을 미치지 않는다.", "③ 우리 지역에 도로나 건물이 새로 생기면 그 영향으로 자연환경도 바뀐다.", "④ 옛날에 사람들은 자연환경의 영향을 많이 받았으나, 오늘날 우리는 기술이 발전하여 영향을 받지 않고 살 수 있다."][x-1])
        answers["지식_Q3"] = st.radio("3. 우리가 살아가는 환경에 관한 설명이다. 다음 중 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 우리는 생활의 불편함을 겪지 않고도 모든 환경문제를 해결할 수 있다.", "② 석탄·석유와 같은 자원은 우리가 살아가는데 필요한 만큼 끊임없이 얻을 수 있다.", "③ 환경은 우리가 살아가는 기초가 되기 때문에 우리는 환경과 조화롭게 살아야 한다.", "④ 과학기술이 발전하여 환경문제의 원인과 결과를 알면, 모든 환경문제를 해결할 수 있다."][x-1])
        answers["지식_Q4"] = st.radio("4. 다음 환경문제와 그 문제를 해결하기 위한 노력을 연결한 것으로 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 열대 우림 파괴를 막기 위해 양치질할 때 컵을 사용한다.", "② 우리 학교 쓰레기를 줄이기 위해서 친구들과 환경캠페인을 한다.", "③ 맑은 물을 오염시키지 않기 위해 실내온도를 적정온도에 맞춘다.", "④ 바다 쓰레기를 줄이기 위해 사용하지 않는 전자제품의 플러그를 뽑는다."][x-1])
        answers["지식_Q5"] = st.radio("5. 다음 행동 중 자연환경에 긍정적인 영향을 주는 행동으로 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 쓰레기를 줄이기 위해 포장이 적게 된 물건을 구매한다.", "② 밝은 실내 환경을 위해 환한 낮에도 전등을 밝게 켜둔다.", "③ 화장실에서 손을 말리기 위해 손수건보다 화장지를 사용한다.", "④ 학교처럼 여러 사람이 사용하는 곳에서는 쾌적함을 위해 에너지를 마음껏 사용한다."][x-1])
        
        q6_ans = st.multiselect("6. 기후변화를 막는 방법 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 자가용보다는 대중교통을 이용한다.", "2": "② 방이나 교실 문을 열어 환기를 잘 시킨다.", "3": "③ 공기청정기를 사용하여 미세먼지를 걸러낸다.", "4": "④ 우리 지역에서 기른 재료로 만든 음식을 먹는다."}[x])
        answers["지식_Q6"] = ",".join(sorted(q6_ans))
        q7_ans = st.multiselect("7. 인간 활동의 영향으로 발생하는 환경문제에 관한 설명 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 물을 낭비하면 여름철 홍수가 자주 일어난다.", "2": "② 석탄·석유를 많이 사용하면 지구의 온도가 올라간다.", "3": "③ 태양광 발전소가 늘어나면 미세먼지 문제가 심각해진다.", "4": "④ 생물이 살아가는 곳이 파괴되면 생물의 종류가 줄어든다."}[x])
        answers["지식_Q7"] = ",".join(sorted(q7_ans))
        q8_ans = st.multiselect("8. 쓰레기를 처리하는 방법 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 전국의 쓰레기를 한곳에 모아 한꺼번에 처리한다.", "2": "② 다시 사용 가능한 유리병은 되돌려주고 돈을 받는다.", "3": "③ 집에서 태울 수 있는 쓰레기는 각자가 태워서 처리한다.", "4": "④ 페트병을 버릴 때는 병에 부착된 비닐과 페트병을 따로 분리하여 버린다."}[x])
        answers["지식_Q8"] = ",".join(sorted(q8_ans))

        st.markdown("#### [2] 환경정서 영역")
        for i in range(9, 19): answers[f"정서_Q{i}"] = st.slider(f"{i}번 문항 생각 정도", 1, 5, 3)

        st.markdown("#### [3] 환경실천 영역")
        for i in range(19, 29): answers[f"실천_Q{i}"] = st.slider(f"{i}번 문항 실천 의지", 1, 5, 3)

        submitted = st.form_submit_button("응답종료")
        if submitted:
            new_data = {"학생 식별자": student_id, "학년": int(s_grade), "반": int(s_class), "번호": int(s_num), "차수": s_round}
            new_data.update(answers)
            new_df = pd.DataFrame([new_data])
            
            # 중복 데이터 제거 (동일 학생이 동일 차수 재입력 시 기존 행 삭제 후 덮어쓰기)
            if not df.empty:
                dup_condition = (df["학생 식별자"] == student_id) & (df["차수"] == s_round)
                if dup_condition.any():
                    df = df[~dup_condition]
            
            df = pd.concat([df, new_df], ignore_index=True)
            
            # ☁️ 구글 스프레드시트에 영구 저장 업데이트
            conn.update(worksheet="Sheet1", data=df)
            st.success(f"🎉 {student_id}의 {s_round} 데이터가 구글 클라우드 시트에 안전하게 영구 저장되었습니다!")

# -------------------------------------------------------------------------
# 교사용 결과 분석 대시보드 (100% 실데이터 기준)
# -------------------------------------------------------------------------
else:
    if df.empty or len(df) == 0:
        st.warning("📊 현재 구글 시트에 저장된 실제 데이터가 없습니다. 학생들의 설문 참여를 기다려주세요.")
    else:
        # 실시간 데이터 점수화 연산
        df["지식_점수"] = df.apply(score_knowledge, axis=1)
        df["정서_평균"] = df[[f"정서_Q{i}" for i in range(9, 19)]].astype(float).mean(axis=1)
        df["실천_평균"] = df[[f"실천_Q{i}" for i in range(19, 29)]].astype(float).mean(axis=1)

        tab1, tab2 = st.tabs(["👥 1. 실제 제출 데이터 종합 분석", "👤 2. 학생별 개별 향상도 분석"])

        with tab1:
            st.subheader("📊 학교 전체 환경소양 실시간 결과")
            paired_students = df.groupby("학생 식별자").filter(lambda x: len(x["차수"].unique()) == 2)
            actual_paired_count = len(paired_students) // 2
            
            st.markdown(f"* **총 참여 학생 수:** {df['학생 식별자'].nunique()}명 / **총 저장된 데이터 수:** {len(df)}건")
            st.markdown(f"* **1차(4월) 및 2차(9월)를 모두 정상 완료한 매칭 학생 수:** {actual_paired_count}명")
            
            summary = df.groupby("차수")[["지식_점수", "정서_평균", "실천_평균"]].mean().reset_index()
            
            fig_all = go.Figure()
            colors = {"1차 (4월)": "#A2D2FF", "2차 (9월)": "#2A9D8F"}
            for r_name in summary["차수"].unique():
                r_df = summary[summary["차수"] == r_name]
                fig_all.add_trace(go.Bar(
                    x=["환경지식", "환경정서(x20)", "환경실천(x20)"],
                    y=[r_df["지식_점수"].values[0], r_df["정서_평균"].values[0]*20, r_df["실천_평균"].values[0]*20],
                    name=r_name, marker_color=colors.get(r_name, "#FFAAA6")
                ))
            st.plotly_chart(fig_all, use_container_width=True)
            
            if "1차 (4월)" in summary["차수"].values and "2차 (9월)" in summary["차수"].values:
                pk1, pk2 = summary[summary["차수"] == "1차 (4월)"]["지식_점수"].values[0], summary[summary["차수"] == "2차 (9월)"]["지식_점수"].values[0]
                pd1, pd2 = summary[summary["차수"] == "1차 (4월)"]["정서_평균"].values[0], summary[summary["차수"] == "2차 (9월)"]["정서_평균"].values[0]
                pp1, pp2 = summary[summary["차수"] == "1차 (4월)"]["실천_평균"].values[0], summary[summary["차수"] == "2차 (9월)"]["실천_평균"].values[0]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("💡 지식 평균 성취도", f"{pk2:.1f}점", f"{pk2-pk1:+.1f}점")
                c2.metric("❤️ 정서 평균 공감도", f"{pd2:.2f}점", f"{pd2-pd1:+.2f}점")
                c3.metric("🏃 실천 평균 의지력", f"{pp2:.2f}점", f"{pp2-pp1:+.2f}점")

        with tab2:
            st.subheader("🔍 학생별 개별 성장도 및 향상도 추적")
            c_grade = st.selectbox("학년 선택", sorted(df["학년"].unique()))
            c_class = st.selectbox("반 선택", sorted(df[df["학년"]==c_grade]["반"].unique()))
            c_num = st.number_input("번호 입력", min_value=1, max_value=60, value=1)
            
            target_id = f"{c_grade}학년 {c_class}반 {c_num}번"
            student_data = df[df["학생 식별자"] == target_id].sort_values("차수")
            rounds_submitted = student_data["차수"].tolist()
            
            if "1차 (4월)" in rounds_submitted and "2차 (9월)" not in rounds_submitted:
                st.error("⚠️ 이 학생은 1차(4월) 데이터만 존재하며, 아직 2차(9월) 조사를 완료하지 않았습니다.")
                st.write("📋 현재 입력된 1차(4월) 기본 점수:")
                st.dataframe(student_data[["차수", "지식_점수", "정서_평균", "실천_평균"]], use_container_width=True)
            elif "1차 (4월)" in rounds_submitted and "2차 (9월)" in rounds_submitted:
                s_pk1, s_pk2 = student_data[student_data["차수"]=="1차 (4월)"]["지식_점수"].values[0], student_data[student_data["차수"]=="2차 (9월)"]["지식_점수"].values[0]
                s_pd1, s_pd2 = student_data[student_data["차수"]=="1차 (4월)"]["정서_평균"].values[0], student_data[student_data["차수"]=="2차 (9월)"]["정서_평균"].values[0]
                s_pp1, s_pp2 = student_data[student_data["차수"]=="1차 (4월)"]["실천_평균"].values[0], student_data[student_data["차수"]=="2차 (9월)"]["실천_평균"].values[0]
                
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Bar(x=["지식", "정서", "실천"], y=[s_pk1, s_pd1, s_pp1], name="1차 (4월)", marker_color="#FFC6FF"))
                fig_ind.add_trace(go.Bar(x=["지식", "정서", "실천"], y=[s_pk2, s_pd2, s_pp2], name="2차 (9월)", marker_color="#BDB2FF"))
                st.plotly_chart(fig_ind, use_container_width=True)
                
                st.info(f"📍 **[향상도 지표]** 지식 변동: {s_pk2-s_pk1:+.1f}점 | 정서 변동: {s_pd2-s_pd1:+.2f}점 | 실천 변동: {s_pp2-s_pp1:+.2f}점")
            else:
                st.info("실제 입력된 데이터가 없습니다. 학생 정보(반/번호)를 다시 조회해 주세요.")