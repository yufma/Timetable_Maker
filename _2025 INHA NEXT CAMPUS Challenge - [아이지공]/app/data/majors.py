# app.data.majors.py
FACULTIES = {
    "소프트웨어융합대학":["컴퓨터공학과",
        "인공지능공학과",
        "데이터사이언스학과",
        "스마트모빌리티공학과",
        "디자인테크놀로지학과",
        "소프트웨어융합공학연계전공",
        ],
    "기타":["자유전공", "미분류",
        ],
}


# 검증용: 모든 전공 플랫 리스트
MAJORS = [m for majors in FACULTIES.values() for m in majors]