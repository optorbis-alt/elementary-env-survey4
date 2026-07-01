import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# 페이지 기본 설정
st.set_page_config(page_title="경덕초등학교 환경소양 측정 시스템", layout="wide")

# 메인 화면 상단 헤더 표기
st.markdown("<h1 style='text-align: center; color: #2A9D8F;'>🏫 경덕초등학교 환경소양 측정 시스템</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.05em; color: #444;'>설문도구는 다음 논문을 참고하여 제작함(*남미리 · 강진영 · 김정훈 · 김찬국 (초등학생용 환경소양 측정도구 개발, 2021))</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 0.85em; color: #999; font-style: italic;'>본 프로그램은 Google Gemini(제미나이) AI를 활용하여 작성되었습니다.</p>", unsafe_allow_html=True)
st.markdown("---")

# 🔒 [고동시성 제어] gspread 기본 드라이버를 이용한 행 단위 독립 보안 연결
@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    if "spreadsheet" in creds_dict:
        creds_dict.pop("spreadsheet")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    gc = get_gspread_client()
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    spreadsheet = gc.open_by_url(spreadsheet_url)
    sheet = spreadsheet.worksheet("Sheet1")
except Exception as e:
    st.error(f"❌ 구글 시트 연결 실패! Secrets 설정을 확인하세요. (오류: {e})")
    st.stop()

# 실시간 데이터 로드
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception:
    df = pd.DataFrame()

# 구조틀 정의
headers = ["학생 식별자", "학년", "반", "번호", "차수"] + [f"지식_Q{i}" for i in range(1, 9)] + [f"정서_Q{i}" for i in range(9, 19)] + [f"실천_Q{i}" for i in range(19, 29)]

if df.empty or "학생 식별자" not in df.columns:
    if not sheet.row_values(1):
        sheet.append_row(headers)
    df = pd.DataFrame(columns=headers)

KNOWLEDGE_ANSWERS = {
    "Q1": 2, "Q2": 3, "Q3": 3, "Q4": 2, "Q5": 1,
    "Q6": ["1", "4"], "Q7": ["2", "4"], "Q8": ["2", "4"]
}

def score_knowledge(row):
    score = 0
    try:
        for i in range(1, 6):
            val = row[f"지식_Q{i}"]
            if pd.isna(val) or val == "": continue
            if int(float(val)) == KNOWLEDGE_ANSWERS[f"Q{i}"]: score += 1
        for i in range(6, 9):
            val = row[f"지식_Q{i}"]
            if pd.isna(val) or val == "": continue
            ans_list = [x.strip() for x in str(val).split(",") if x.strip()]
            if sorted(ans_list) == sorted(KNOWLEDGE_ANSWERS[f"Q{i}"]): score += 1
    except Exception:
        return 0
    return (score / 8) * 100

menu = st.sidebar.radio("원하는 메뉴를 선택하세요", ["📝 학생용 설문조사 입력", "📊 교사용 결과 분석 대시보드"])

# 학생용 설문조사 입력 화면
if menu == "📝 학생용 설문조사 입력":
    st.subheader("🌱 학생용 환경소양 조사지")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: s_grade = st.selectbox("학년", [1, 2, 3, 4, 5, 6], index=3)
    with col2: s_class = st.number_input("반", min_value=1, max_value=15, value=1, step=1)
    with col3: s_num = st.number_input("번호", min_value=1, max_value=60, value=1, step=1)
    with col4: s_round = st.radio("제출 차수", ["1차 (4월)", "2차 (9월)"], horizontal=True)

    student_id = f"{int(s_grade)}학년 {int(s_class)}반 {int(s_num)}번"
    st.markdown("---")
    answers = {}
    
    with st.form("survey_form"):
        st.markdown("#### [1] 환경지식 영역")
        answers["지식_Q1"] = st.radio("1. 환경에 관한 다음 설명 중, 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 동물과 식물은 흙, 공기, 물 등과 서로 관련이 없다.", "② 우리가 관계를 맺고 있는 주변의 모든 것은 환경이다.", "③ 환경에서 흙, 공기, 물 등은 서로 영향을 주고받지 않는다.", "④ 환경은 동물이나 식물과 같이 살아있는 생물 사이의 관계를 의미한다."][x-1])
        answers["지식_Q2"] = st.radio("2. 우리 생활과 자연환경의 관계에 대한 설명이다. 다음 중 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 우리의 생활 방식이 편리하게 바뀌어도, 자연환경은 그대로 유지된다.", "② 자연환경의 변화는 우리의 소비나 생활 방식에 영향을 미치지 않는다.", "③ 우리 지역에 도로나 건물이 새로 생기면 그 영향으로 자연환경도 바뀐다.", "④ 옛날에 사람들은 자연환경의 영향을 많이 받았으나, 오늘날 우리는 기술이 발전하여 영향을 받지 않고 살 수 있다."][x-1])
        # [오타 수정] axioms 지우고 '해결할 수 있다'로 교정
        answers["지식_Q3"] = st.radio("3. 우리가 살아가는 환경에 관한 설명이다. 다음 중 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 우리는 생활의 불편함을 겪지 않고도 모든 환경문제를 해결할 수 있다.", "② 석탄·석유와 같은 자원은 우리가 살아가는데 필요한 만큼 끊임없이 얻을 수 있다.", "③ 환경은 우리가 살아가는 기초가 되기 때문에 우리는 환경과 조화롭게 살아야 한다.", "④ 과학기술이 발전하여 환경문제의 원인과 결과를 알면, 모든 환경문제를 해결할 수 있다."][x-1])
        answers["지식_Q4"] = st.radio("4. 다음 환경문제와 그 문제를 해결하기 위한 노력을 연결한 것으로 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 열대 우림 파괴를 막기 위해 양치질할 때 컵을 사용한다.", "② 우리 학교 쓰레기를 줄이기 위해서 친구들과 환경캠페인을 한다.", "③ 맑은 물을 오염시키지 않기 위해 실내온도를 적정온도에 맞춘다.", "④ 바다 쓰레기를 줄이기 위해 사용하지 않는 전자제품의 플러그를 뽑는다."][x-1])
        answers["지식_Q5"] = st.radio("5. 다음 행동 중 자연환경에 긍정적인 영향을 주는 행동으로 가장 적절한 것은?", [1, 2, 3, 4], format_func=lambda x: ["① 쓰레기를 줄이기 위해 포장이 적게 된 물건을 구매한다.", "② 밝은 실내 환경을 위해 환한 낮에도 전등을 밝게 켜둔다.", "③ 화장실에서 손을 말리기 위해 손수건보다 화장지를 사용한다.", "④ 학교처럼 여러 사람이 사용하는 곳에서는 쾌적함을 위해 에너지를 마음껏 사용한다."][x-1])
        
        st.caption("※ 아래 6~8번 문항은 알맞은 정답을 '2가지' 선택하세요.")
        q6_ans = st.multiselect("6. 기후변화를 막는 방법 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 자가용보다는 대중교통을 이용한다.", "2": "② 방이나 교실 문을 열어 환기를 잘 시킨다.", "3": "③ 공기청정기를 사용하여 미세먼지를 걸러낸다.", "4": "④ 우리 지역에서 기른 재료로 만든 음식을 먹는다."}[x])
        answers["지식_Q6"] = ",".join(sorted(q6_ans))
        q7_ans = st.multiselect("7. 인간 활동의 영향으로 발생하는 환경문제에 관한 설명 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 물을 낭비하면 여름철 홍수가 자주 일어난다.", "2": "② 석탄·석유를 많이 사용하면 지구의 온도가 올라간다.", "3": "③ 태양광 발전소가 늘어나면 미세먼지 문제가 심각해진다.", "4": "④ 생물이 살아가는 곳이 파괴되면 생물의 종류가 줄어든다."}[x])
        answers["지식_Q7"] = ",".join(sorted(q7_ans))
        q8_ans = st.multiselect("8. 쓰레기를 처리하는 방법 중 가장 적절한 2가지를 고르면?", ["1", "2", "3", "4"], format_func=lambda x: {"1": "① 전국의 쓰레기를 한곳에 모아 한꺼번에 처리한다.", "2": "② 다시 사용 가능한 유리병은 되돌려주고 돈을 받는다.", "3": "③ 집에서 태울 수 있는 쓰레기는 각자가 태워서 처리한다.", "4": "④ 페트병을 버릴 때는 병에 부착된 비닐과 페트병을 따로 분리하여 버린다."}[x])
        answers["지식_Q8"] = ",".join(sorted(q8_ans))

        st.markdown("#### [2] 환경정서 영역")
        likert_labels = {1: "매우 그렇지 않다", 2: "그렇지 않다", 3: "보통이다", 4: "그렇다", 5: "매우 그렇다"}
        disposition_questions = {
            9: "나는 자연의 소리(새 소리, 파도 소리, 나뭇잎 소리 등)를 들으면 기분이 좋아진다.",
            10: "나는 산이나 바다 같은 자연이 좋다.",
            11: "나는 사람들이 캔이나 병을 분리배출하지 않고 일반 쓰레기통에 버리면 마음이 불편하다.",
            12: "멸종위기에 처한 동식물이 사는 곳은 개발하기보다 그대로 지키는 것이 낫다.",
            13: "환경을 보호하기 위해 내 생활이 조금 불편해져도 괜찮다.",
            14: "나는 과학기술의 발달만으로 기후변화를 모두 해결할 수 없다고 생각한다.",
            15: "내가 쓰레기 분리배출을 잘하면 우리 지역의 환경을 개선하는 데 도움이 될 것이다.",
            16: "나는 우리가 겪고 있는 환경문제를 해결할 책임이 있다.",
            17: "나는 가족이나 친구가 에너지 절약을 실천하도록 도울 수 있다.",
            18: "환경문제를 해결하기 위해 친구나 가족과 함께 노력한다면 더 좋은 결과를 얻을 것이다."
        }
        for i, q in disposition_questions.items():
            answers[f"정서_Q{i}"] = st.select_slider(f"{i}. {q}", options=[1, 2, 3, 4, 5], value=3, format_func=lambda x: likert_labels[x])

        st.markdown("#### [3] 환경실천 영역")
        practice_questions = {
            19: "나는 물을 사용하지 않을 경우, 샤워기나 수도꼭지를 잠글 것이다.",
            20: "나는 음식물 쓰레기가 적게 나오도록 노력할 것이다.",
            21: "나는 부모님께 조금 비싸더라도 친환경 제품을 구매하자고 말씀을 드릴 것이다.",
            22: "나는 물건을 살 때, 꼭 필요한 물건인지 충분히 따져본 후 구매를 할 것이다.",
            23: "나는 주변 사람들에게 가까운 거리는 걷거나 대중교통을 이용하도록 이야기할 것이다.",
            24: "나는 환경에 관한 책이나 TV 프로그램, 인터넷 등을 찾아볼 것이다.",
            25: "나는 친구들에게 우리 학교나 지역의 환경 캠페인에 함께 참여하자고 이야기할 것이다.",
            26: "나는 학급회의에서 우리 학교와 지역의 환경문제를 이야기할 때 적극적으로 내 의견을 말할 것이다.",
            27: "나는 우리 지역의 환경문제를 발견한다면 시청이나 구청에 알릴 것이다.",
            28: "미래에 내가 투표할 수 있게 된다면 환경을 위해 노력하는 후보에게 투표할 생각이 있다."
        }
        for i, q in practice_questions.items():
            answers[f"실천_Q{i}"] = st.select_slider(f"{i}. {q}", options=[1, 2, 3, 4, 5], value=3, format_func=lambda x: likert_labels[x])

        submitted = st.form_submit_button("응답종료")
        if submitted:
            try:
                latest_data = sheet.get_all_records()
                df_latest = pd.DataFrame(latest_data)
                
                new_row_values = [student_id, int(s_grade), int(s_class), int(s_num), s_round] + \
                                 [answers[f"지식_Q{i}"] for i in range(1, 9)] + \
                                 [answers[f"정서_Q{i}"] for i in range(9, 19)] + \
                                 [answers[f"실천_Q{i}"] for i in range(19, 29)]
                
                is_overwritten = False
                
                if not df_latest.empty and "학생 식별자" in df_latest.columns:
                    match = df_latest[(df_latest["학생 식별자"] == student_id) & (df_latest["차수"] == s_round)]
                    if not match.empty:
                        row_idx = int(match.index[0]) + 2
                        sheet.delete_rows(row_idx)
                        sheet.append_row(new_row_values)
                        is_overwritten = True
                
                if not is_overwritten:
                    sheet.append_row(new_row_values)
                
                if is_overwritten:
                    st.warning(f"⚠️ [이전 저장데이터 삭제됨] {student_id}의 {s_round} 기존 데이터가 완벽하게 삭제되고 최신 응답으로 교체되었습니다.")
                else:
                    st.success(f"✅ [저장성공] {student_id}의 {s_round} 설문 데이터가 안전하게 등록되었습니다!")
                    
            except Exception as e:
                st.error(f"❌ [저장실패] 서버 혼잡으로 저장이 취소되었습니다. 잠시 후 다시 눌러주세요. (에러: {e})")

# 교사용 결과 분석 대시보드
else:
    if df.empty or len(df) == 0:
        st.warning("📊 현재 구글 시트에 저장된 실제 데이터가 없습니다.")
    else:
        df["지식_점수"] = df.apply(score_knowledge, axis=1)
        df["정서_평균"] = df[[f"정서_Q{i}" for i in range(9, 19)]].astype(float).mean(axis=1)
        df["실천_평균"] = df[[f"실천_Q{i}" for i in range(19, 29)]].astype(float).mean(axis=1)

        tab1, tab2 = st.tabs(["👥 1. 실제 제출 데이터 종합 분석", "👤 2. 학생별 개별 향상도 분석"])

        with tab1:
            st.subheader("📊 학교 전체 환경소양 실시간 결과")
            
            # 1차(사전)와 2차(사후) 모두 완료한 매칭 학생단 식별
            paired_selector = df.groupby("학생 식별자").filter(lambda x: len(x["차수"].unique()) == 2)
            actual_paired_count = len(paired_selector) // 2
            
            st.markdown(f"* **총 참여 학생 수:** {df['학생 식별자'].nunique()}명 | **총 제출 데이터 수:** {len(df)}건")
            st.markdown(f"* **1차 및 2차를 모두 완료한 매칭 분석 대상자:** {actual_paired_count}명")
            
            # [통계 교정] 학술 연구용 동일집단 비교 토글 스위치 제공
            analysis_type = st.radio("📈 통계 분석 모델 선택", ["모든 제출 데이터 포함 (단순 누적 평균)", "1차·2차 조사 모두 마친 동일 학생만 포함 (학술 비교용)"], horizontal=True)
            
            plot_df = paired_selector if "동일 학생만 포함" in analysis_type else df
            
            if plot_df.empty:
                st.info("선택하신 통계 모델에 해당하는 매칭 데이터가 아직 부족합니다.")
            else:
                summary = plot_df.groupby("차수")[["지식_점수", "정서_평균", "실천_평균"]].mean().reset_index()
                
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
                
                # [로직 교정] 데이터 수집 현황(4월 단독 vs 9월 매칭)에 따라 유연하게 카드를 출력하는 로직
                pk_4 = summary[summary["차수"] == "1차 (4월)"]["지식_점수"].values[0] if "1차 (4월)" in summary["차수"].values else None
                pk_9 = summary[summary["차수"] == "2차 (9월)"]["지식_점수"].values[0] if "2차 (9월)" in summary["차수"].values else None
                
                pd_4 = summary[summary["차수"] == "1차 (4월)"]["정서_평균"].values[0] if "1차 (4월)" in summary["차수"].values else None
                pd_9 = summary[summary["차수"] == "2차 (9월)"]["정서_평균"].values[0] if "2차 (9월)" in summary["차수"].values else None
                
                pp_4 = summary[summary["차수"] == "1차 (4월)"]["실천_평균"].values[0] if "1차 (4월)" in summary["차수"].values else None
                pp_9 = summary[summary["차수"] == "2차 (9월)"]["실천_평균"].values[0] if "2차 (9월)" in summary["차수"].values else None
                
                c1, c2, c3 = st.columns(3)
                
                # 2차(9월) 결과 위주 출력 (1차 대비 성장률 자동 연산)
                if pk_9 is not None:
                    c1.metric("💡 지식 평균 성취도 (9월 기준)", f"{pk_9:.1f}점", f"{pk_9-pk_4:+.1f}점" if pk_4 is not None else None)
                    c2.metric("❤️ 정서 평균 공감도 (9월 기준)", f"{pd_9:.2f}점", f"{pd_9-pd_4:+.2f}점" if pd_4 is not None else None)
                    c3.metric("🏃 실천 평균 의지력 (9월 기준)", f"{pp_9:.2f}점", f"{pp_9-pp_4:+.2f}점" if pp_4 is not None else None)
                # 학기 초 1차(4월) 데이터만 단독 존재할 때의 예외 안전망
                elif pk_4 is not None:
                    c1.metric("💡 지식 평균 성취도 (4월 기준)", f"{pk_4:.1f}점")
                    c2.metric("❤️ 정서 평균 공감도 (4월 기준)", f"{pd_4:.2f}점")
                    c3.metric("🏃 실천 평균 의지력 (4월 기준)", f"{pp_4:.2f}점")

        with tab2:
            st.subheader("🔍 학생별 개별 성장도 및 향상도 추적")
            actual_students = sorted(df["학생 식별자"].dropna().unique())
            
            if not actual_students:
                st.info("현재 분석할 수 있는 학생 데이터가 데이터베이스에 존재하지 않습니다.")
            else:
                selected_student = st.selectbox("분석할 학생을 고르세요", actual_students)
                student_data = df[df["학생 식별자"] == selected_student].sort_values("차수")
                rounds_submitted = student_data["차수"].tolist()
                
                st.markdown(f"### 📍 데이터 분석 대상: `{selected_student}`")
                
                if "1차 (4월)" in rounds_submitted and "2차 (9월)" not in rounds_submitted:
                    st.error("⚠️ 이 학생은 1차(4월) 데이터만 존재하며, 아직 2차(9월) 조사를 완료하지 않았습니다.")
                    st.write("📋 현재 입력 완료된 1차(4월) 기본 점수:")
                    st.dataframe(student_data[["차수", "지식_점수", "정서_평균", "실천_평균"]], use_container_width=True)
                elif "1차 (4월)" in rounds_submitted and "2차 (9월)" in rounds_submitted:
                    s_pk1 = student_data[student_data["차수"]=="1차 (4월)"]["지식_점수"].values[0]
                    s_pk2 = student_data[student_data["차수"]=="2차 (9월)"]["지식_점수"].values[0]
                    s_pd1 = student_data[student_data["차수"]=="1차 (4월)"]["정서_평균"].values[0]
                    s_pd2 = student_data[student_data["차수"]=="2차 (9월)"]["정서_평균"].values[0]
                    s_pp1 = student_data[student_data["차수"]=="1차 (4월)"]["실천_평균"].values[0]
                    s_pp2 = student_data[student_data["차수"]=="2차 (9월)"]["실천_평균"].values[0]
                    
                    fig_ind = go.Figure()
                    fig_ind.add_trace(go.Bar(x=["지식 점수 (100점)", "정서 평균 (5점)", "실천 평균 (5점)"], y=[s_pk1, s_pd1, s_pp1], name="1차 (4월)", marker_color="#FFC6FF"))
                    fig_ind.add_trace(go.Bar(x=["지식 점수 (100점)", "정서 평균 (5점)", "실천 평균 (5점)"], y=[s_pk2, s_pd2, s_pp2], name="2차 (9월)", marker_color="#BDB2FF"))
                    st.plotly_chart(fig_ind, use_container_width=True)
                    
                    st.markdown("#### 📝 이 학생만을 위한 항목별 성장 피드백")
                    k_diff = s_pk2 - s_pk1
                    d_diff = s_pd2 - s_pd1
                    p_diff = s_pp2 - s_pp1
                    
                    k_txt = f"**{k_diff:+.1f}점** 변동함." if k_diff != 0 else "점수 변동 없음."
                    d_txt = f"**{d_diff:+.2f}점** 변동함." if d_diff != 0 else "점수 변동 없음."
                    p_txt = f"**{p_diff:+.2f}점** 변동함." if p_diff != 0 else "점수 변동 없음."

                    st.info(f"📍 **[환경지식 영역]** 사전 대비 {k_txt}\n\n📍 **[환경정서 영역]** 사전 대비 {d_txt}\n\n📍 **[환경실천 영역]** 사전 대비 {p_txt}")
                elif "2차 (9월)" in rounds_submitted and "1차 (4월)" not in rounds_submitted:
                    st.warning("⚠️ 이 학생은 2차(9월) 데이터만 존재하고, 1차(4월) 데이터가 누락되어 비교할 수 없습니다.")
                    st.dataframe(student_data[["차수", "지식_점수", "정서_평균", "실천_평균"]], use_container_width=True)
