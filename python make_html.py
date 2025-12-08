import asyncio
from pycomcigan import TimeTable
import datetime

# ==========================================
# HTML 템플릿 (디자인)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{teacher_name} 선생님 시간표</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .container {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; width: 100%; }}
        h1 {{ text-align: center; color: #333; margin-bottom: 5px; }}
        .update-time {{ text-align: center; color: #888; font-size: 0.85em; margin-bottom: 20px; }}
        
        /* 스크롤 가능한 탭 */
        .tabs {{ display: flex; overflow-x: auto; gap: 10px; margin-bottom: 20px; padding-bottom: 5px; }}
        .tab {{ 
            padding: 10px 20px; text-align: center; border-radius: 20px; 
            color: #555; font-weight: bold; background: #eee; cursor: pointer; 
            white-space: nowrap; flex-shrink: 0; transition: 0.3s;
        }}
        .tab.active {{ background: #4a90e2; color: white; box-shadow: 0 4px 6px rgba(74, 144, 226, 0.3); }}
        
        .content {{ display: none; }}
        .content.active {{ display: block; animation: fadeIn 0.5s; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }}
        th, td {{ border: 1px solid #e1e4e8; padding: 12px 8px; text-align: center; font-size: 0.95rem; }}
        th {{ background-color: #4a90e2; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        
        .period {{ background-color: #edf2f7; font-weight: bold; color: #4a5568; width: 40px; }}
        .subject {{ font-weight: bold; display: block; color: #2d3748; }}
        .class-info {{ font-size: 0.8em; color: #718096; display: block; margin-top: 2px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
    <script>
        function openTab(event, tabId) {{
            var i, contents, tabs;
            
            // 모든 내용 숨기기
            contents = document.getElementsByClassName("content");
            for (i = 0; i < contents.length; i++) {{ contents[i].classList.remove("active"); }}
            
            // 모든 탭 비활성화
            tabs = document.getElementsByClassName("tab");
            for (i = 0; i < tabs.length; i++) {{ tabs[i].classList.remove("active"); }}
            
            // 선택된 것만 활성화
            document.getElementById(tabId).classList.add("active");
            event.currentTarget.classList.add("active");
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📅 {school_name} {teacher_name}T</h1>
        <div class="update-time">최종 업데이트: {update_time}</div>

        <div class="tabs">
            {tab_buttons}
        </div>

        {tab_contents}
    </div>
</body>
</html>
"""

async def get_week_data(school_name, target_teacher, week_num):
    """
    특정 주차의 데이터를 가져와서 HTML Table Body(행)를 반환합니다.
    수업 데이터가 하나도 없으면 None을 반환합니다.
    """
    try:
        tt = TimeTable(school_name, week_num=week_num)
        my_schedule = [["" for _ in range(9)] for _ in range(6)]
        has_data = False # 데이터가 있는지 확인용

        # 1~3학년, 1~15반 데이터 스캔
        for grade in range(1, 4):
            for class_num in range(1, 16):
                try:
                    class_data = tt.timetable[grade][class_num]
                except: continue

                for day_idx in range(1, 6):
                    for lesson in class_data[day_idx]:
                        if target_teacher in lesson.teacher:
                            my_schedule[day_idx][lesson.period] = {
                                "subject": lesson.subject,
                                "class": f"{grade}-{class_num}"
                            }
                            has_data = True # 수업 하나라도 찾음!

        # 데이터가 아예 없으면 (방학이거나 서버에 등록 안됨) 중단
        if not has_data:
            return None

        # HTML 행 만들기
        rows = ""
        for period in range(1, 8):
            rows += f"<tr><td class='period'>{period}</td>"
            for day in range(1, 6):
                data = my_schedule[day][period]
                if data:
                    rows += f"<td><span class='subject'>{data['subject']}</span><span class='class-info'>{data['class']}</span></td>"
                else:
                    rows += "<td></td>"
            rows += "</tr>"
        
        return rows

    except Exception:
        return None # 에러 나면 데이터 없는 것으로 간주

async def create_auto_html():
    school = "송양고등학교"
    teacher = "정찬" # 검색용 (2글자)
    display_name = "정찬혁" # 화면 표시용
    
    print(f"🚀 '{school}' 데이터 수집을 시작합니다...")

    tab_buttons_html = ""
    tab_contents_html = ""
    
    # 최대 5주치까지 시도해봅니다. (보통 0, 1, 2주차 정도까지 있음)
    max_weeks = 5 
    
    for w in range(max_weeks):
        print(f"📡 {w}주차 데이터 요청 중...", end="\r")
        
        # 데이터 가져오기
        table_rows = await get_week_data(school, teacher, w)
        
        # 데이터가 없으면 반복문 종료 (더 이상 미래 데이터 없음)
        if table_rows is None:
            print(f"\n✋ {w}주차부터는 데이터가 없어 수집을 종료합니다.")
            break
            
        # 탭 버튼 HTML 추가
        tab_label = "이번 주" if w == 0 else "다음 주" if w == 1 else f"{w}주 후"
        is_active = "active" if w == 0 else "" # 첫 번째 탭만 활성화
        
        tab_buttons_html += f"""
            <div class="tab {is_active}" onclick="openTab(event, 'week{w}')">{tab_label}</div>
        """
        
        # 탭 내용 HTML 추가
        tab_contents_html += f"""
        <div id="week{w}" class="content {is_active}">
            <table>
                <thead>
                    <tr><th width="10%">교시</th><th width="18%">월</th><th width="18%">화</th><th width="18%">수</th><th width="18%">목</th><th width="18%">금</th></tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """

    # 최종 HTML 조립
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    final_html = HTML_TEMPLATE.format(
        school_name=school,
        teacher_name=display_name,
        update_time=now,
        tab_buttons=tab_buttons_html,
        tab_contents=tab_contents_html
    )

    # 파일 저장
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("\n✅ 'index.html' 파일 생성 완료! 깃허브에 Push 하세요.")

if __name__ == "__main__":
    asyncio.run(create_auto_html())