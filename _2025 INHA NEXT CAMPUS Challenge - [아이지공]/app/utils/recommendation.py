"""
main.py에서 전달하는 데이터 형식:

previous_courses / available_courses: List[Dict[str, Any]]
    각 과목은 다음과 같은 형식:
    {
        "course_id": "AIE1001",           # 학수번호
        "course_name": "인공지능의 이해",  # 과목명
        "time_raw": "월1,2,3:강의실",     # 시간 (선택적, 없을 수 있음)
        "credit": 3,                       # 학점 (int 또는 float)
        "prof": "홍길동",                  # 교수명 (선택적)
        "file_id": "AIE1001.001.json"     # 파일 ID (선택적)
    }

input_data: Dict[str, Any]
    {
        "previous_courses": [...],         # 이전 수강 내역
        "available_courses": [...],        # 사용 가능한 과목 목록
        "target_credits": 15               # 목표 학점
    }
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import json
import re
from datetime import datetime as dt

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# .env 파일에서 환경 변수 로드
load_dotenv()


class CourseRecommender:
    #과목 추천을 위한 일련의 함수들을 모아둔 클래스
    
    
    def __init__(
        self,
        #사용할 모델
        llm_model: str = "gpt-3.5-turbo",
        
        #창의성 값(높을수록 다양한 답변 생성)
        temperature: float = 0.7,
        
        #로그 저장 디렉토리
        log_dir: Optional[str] = None,
        
        #로깅 활성화 여부
        enable_logging: bool = True
    ):
        #__init__ 인자로 초기화
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.enable_logging = enable_logging
        
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path(__file__).parent / "logs"
        
        if self.enable_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _parse_time_schedule(self, time_str: str) -> Dict[str, List[int]]:
        """
        시간 문자열 파싱
        - "월1,2,3" -> {"월": [1,2,3]}
        - "월1,2,3:강의실명" -> {"월": [1,2,3]} (강의실 정보 제거)
        - "월1,2,3,화3,4,5" -> {"월": [1,2,3], "화": [3,4,5]}
        - "웹강의" 또는 "온라인" -> {}
        """
        schedule = {}
        if not time_str:
            return schedule
        
        time_str = str(time_str).strip()
        
        # 웹강의 또는 온라인 체크
        if "웹강의" in time_str or "온라인" in time_str or "온라" in time_str:
            return schedule
        
        # ":" 뒤의 강의실 정보 제거 (예: "월1,2,3:강의실명" -> "월1,2,3")
        if ":" in time_str:
            time_str = time_str.split(":")[0].strip()
        
        # 요일별로 분리하여 파싱
        parts = re.split(r'([월화수목금토일])', time_str)
        current_day = None
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in ["월", "화", "수", "목", "금", "토", "일"]:
                current_day = part
                if current_day not in schedule:
                    schedule[current_day] = []
            elif current_day:
                # 숫자들 추출 (예: "1,2,3" -> [1,2,3])
                times = re.findall(r'\d+', part)
                schedule[current_day].extend([int(t) for t in times])
        
        return schedule
    
    #시간 충돌 유효성 검사
    def _check_time_conflict(self, courses: List[Dict[str, Any]]) -> Dict[str, Any]:
        conflicts = []
        course_schedules = []
        
        for course in courses:
            schedule = self._parse_time_schedule(course.get("시간", ""))
            course_schedules.append({
                "학수번호": course.get("학수번호", ""),
                "과목명": course.get("과목명", ""),
                "시간": course.get("시간", ""),
                "schedule": schedule
            })
        
        # 모든 과목 쌍에 대해 시간 충돌 검사
        for i in range(len(course_schedules)):
            for j in range(i + 1, len(course_schedules)):
                c1, c2 = course_schedules[i], course_schedules[j]
                for day in ["월", "화", "수", "목", "금", "토", "일"]:
                    times1 = c1["schedule"].get(day, [])
                    times2 = c2["schedule"].get(day, [])
                    if times1 and times2:
                        overlap = set(times1) & set(times2)
                        if overlap:
                            conflicts.append({
                                "과목1": {"학수번호": c1["학수번호"], "과목명": c1["과목명"], "시간": c1["시간"]},
                                "과목2": {"학수번호": c2["학수번호"], "과목명": c2["과목명"], "시간": c2["시간"]},
                                "충돌_요일": day,
                                "충돌_시간": sorted(list(overlap))
                            })
        
        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts,
            "conflict_count": len(conflicts)
        }
    #학점 값을 연산에 용이하게 정규화
    def _normalize_credit(self, credit_value: Any) -> float:
        if credit_value is None:
            return 0.0
        if isinstance(credit_value, (int, float)):
            return float(credit_value)
        credits_str = str(credit_value).strip()
        match = re.search(r'(\d+\.?\d*)', credits_str)
        if match:
            return float(match.group(1))
        return 0.0
    
    #학점 유효성 검사, 설정한 모든 학점을 채웠는지 여부 확인
    def _check_credits(self, courses: List[Dict[str, Any]], target_credits: Optional[int] = None) -> Dict[str, Any]:
        total_credits = 0.0
        for course in courses:
            credit = course.get("학점", 0)
            total_credits += self._normalize_credit(credit)
        
        is_valid = True
        if target_credits is not None:
            is_valid = abs(total_credits - target_credits) < 0.5
        
        return {
            "total_credits": total_credits,
            "target_credits": target_credits,
            "is_valid": is_valid,
            "difference": total_credits - target_credits if target_credits else None
        }
    
    #과목 정보를 표준 형식으로 변환 (main.py 형식: course_id, course_name, time_raw, credit)
    def _get_course_info(self, course: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "학수번호": course.get("course_id", ""),
            "과목명": course.get("course_name", ""),
            "시간": course.get("time_raw", ""),
            "학점": course.get("credit", 0)
        }
    
    #추천 결과 최종 검증 함수, 모든 검증 함수 호출함
    def _validate_result(
        self,
        result: Dict[str, Any],
        input_data: Dict[str, Any],
        available_courses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """추천 결과 검증"""
        # 추천된 학수번호 추출
        recommended_codes = result.get("recommended_codes", [])
        if not recommended_codes:
            response = result.get("raw_response", "")
            codes = re.findall(r'\b([A-Z]{3}\d{4})\b', response)
            # 중복 제거
            seen = set()
            recommended_codes = []
            for code in codes:
                if code not in seen:
                    seen.add(code)
                    recommended_codes.append(code)
        
        # 사용 가능한 과목을 표준 형식으로 변환하고 학수번호로 인덱싱 (시간별로 구분)
        # 같은 학수번호의 다른 섹션들을 모두 저장
        available_dict_by_code = {}
        for course in available_courses:
            normalized = self._get_course_info(course)
            code = normalized["학수번호"]
            if code:
                if code not in available_dict_by_code:
                    available_dict_by_code[code] = []
                available_dict_by_code[code].append(normalized)
        
        # 추천된 과목 정보 가져오기 (중복 제거)
        recommended_courses = []
        seen_codes = set()
        for code in recommended_codes:
            if code in seen_codes:
                continue  # 이미 추가된 학수번호는 건너뜀
            if code in available_dict_by_code:
                # 같은 학수번호의 첫 번째 섹션 사용 (또는 시간 정보가 있으면 매칭)
                # 일단 첫 번째 섹션 사용
                recommended_courses.append(available_dict_by_code[code][0])
                seen_codes.add(code)
        
        # 검증 (우선순위: 1. 학점 이하, 2. 핵심교양 학점 이하, 3. 카테고리 중복 없음)
        credits_check = self._check_credits(recommended_courses, input_data.get("target_credits"))
        # 학점이 목표 이하인지 확인 (초과하지 않도록)
        credits_check["is_valid"] = credits_check["total_credits"] <= (input_data.get("target_credits") or 999)
        time_check = self._check_time_conflict(recommended_courses)
        
        # 웹강의 학점 제한 검증
        web_credits_check = {"is_valid": True, "total_web_credits": 0.0}
        max_web_credits = input_data.get("max_web_credits")
        if max_web_credits is not None:
            total_web_credits = 0.0
            for course in recommended_courses:
                time_str = course.get("시간", "")
                if time_str and ("웹강의" in time_str or "온라인" in time_str or "온라" in time_str):
                    total_web_credits += self._normalize_credit(course.get("학점", 0))
            web_credits_check = {
                "is_valid": total_web_credits <= max_web_credits,
                "total_web_credits": total_web_credits,
                "max_web_credits": max_web_credits
            }
        
        # 카테고리 제한 검증 (핵심교양 카테고리별 최대 1개)
        category_check = {"is_valid": True, "violations": []}
        core_category_constraint = input_data.get("core_category_constraint", False)
        
        # 핵심교양 학점 검증
        core_credits_check = {"is_valid": True, "total_core_credits": 0.0}
        core_credits_target = input_data.get("core_credits_target")
        
        if core_category_constraint:
            # 추천된 과목 중 핵심교양의 카테고리별 개수 확인
            core_courses_by_category = {}
            total_core_credits = 0.0
            for course in recommended_courses:
                course_code = course.get("학수번호", "")
                # available_courses에서 해당 과목의 카테고리 정보 찾기
                for av_course in available_courses:
                    if av_course.get("course_id") == course_code:
                        if av_course.get("priority") == 4:  # 핵심교양
                            cat_id = av_course.get("core_category_id")
                            total_core_credits += self._normalize_credit(course.get("학점", 0))
                            if cat_id:
                                if cat_id not in core_courses_by_category:
                                    core_courses_by_category[cat_id] = []
                                core_courses_by_category[cat_id].append(course_code)
                        break
            
            # 같은 카테고리에서 2개 이상 선택되었는지 확인
            violations = []
            for cat_id, codes in core_courses_by_category.items():
                if len(codes) > 1:
                    violations.append(f"핵심교양 카테고리 {cat_id}에서 {len(codes)}개 선택됨 ({', '.join(codes)}) - 최대 1개만 가능")
            
            if violations:
                category_check = {
                    "is_valid": False,
                    "violations": violations
                }
            
            # 핵심교양 학점 검증 (정확히 맞춤)
            if core_credits_target is not None and core_credits_target > 0:
                core_credits_check = {
                    "is_valid": abs(total_core_credits - core_credits_target) < 0.5,
                    "total_core_credits": total_core_credits,
                    "target_core_credits": core_credits_target
                }
        
        # 우선순위 검증 (낮은 우선순위 선택 시 높은 우선순위가 비어있으면 안 됨)
        priority_check = {"is_valid": True, "violations": []}
        priority_order = input_data.get("priority_order", [1, 2, 3, 4, 5])  # 입력 데이터에서 가져오기 (전공필수/전공선택이 이미 포함된 경우 [3, 4, 5] 등)
        priority_names = {1: "전공필수", 2: "전공선택", 3: "기초/중점 교양", 4: "핵심교양", 5: "일반교양"}
        
        # 각 우선순위별로 사용 가능한 과목이 있는지 확인
        available_by_priority = {}
        for av_course in available_courses:
            priority = av_course.get("priority", 5)
            if priority not in available_by_priority:
                available_by_priority[priority] = []
            available_by_priority[priority].append(av_course)
        
        # 추천된 과목들의 우선순위 확인
        selected_priorities = set()
        for course in recommended_courses:
            course_code = course.get("학수번호", "")
            for av_course in available_courses:
                if av_course.get("course_id") == course_code:
                    priority = av_course.get("priority", 5)
                    selected_priorities.add(priority)
                    break
        
        # 우선순위 위반 체크: 
        # 낮은 우선순위를 선택했는데, 높은 우선순위에 선택 가능한 과목이 있었는데 선택하지 않은 경우
        violations = []
        for priority in priority_order:
            if priority not in selected_priorities:
                # 이 우선순위를 선택하지 않았다면
                # 1. 이 우선순위에 사용 가능한 과목이 있는지 확인
                has_available = priority in available_by_priority and len(available_by_priority[priority]) > 0
                
                # 2. 더 낮은 우선순위를 선택했는지 확인
                lower_priorities_selected = [p for p in selected_priorities if p > priority]
                
                # 3. 위반: 사용 가능한 과목이 있는데 선택하지 않고, 더 낮은 우선순위를 선택한 경우
                if has_available and lower_priorities_selected:
                    violations.append(f"{priority_names.get(priority, f'우선순위{priority}')}에 선택 가능한 과목이 있는데 선택하지 않았고, 대신 {', '.join(priority_names.get(p, f'우선순위{p}') for p in sorted(lower_priorities_selected))}를 선택함")
        
        if violations:
            priority_check = {
                "is_valid": False,
                "violations": violations
            }
        
        # 검증 우선순위: 1. 학점 이하, 2. 핵심교양 학점 정확히, 3. 카테고리 중복 없음, 4. 우선순위 순서 준수
        # 시간 충돌과 웹강의 학점 제한도 검증에 포함
        is_valid = (
            credits_check["is_valid"] and  # 1. 학점이 목표 이하
            core_credits_check["is_valid"] and  # 2. 핵심교양 학점이 정확히 목표와 일치
            category_check["is_valid"] and  # 3. 핵심교양 카테고리 중복 없음
            priority_check["is_valid"] and  # 4. 우선순위 순서 준수
            not time_check["has_conflict"] and  # 시간 충돌 없음
            web_credits_check["is_valid"]  # 웹강의 학점 제한 준수
        )
        
        return {
            "credits_validation": credits_check,
            "time_validation": time_check,
            "web_credits_validation": web_credits_check,
            "category_validation": category_check,
            "core_credits_validation": core_credits_check,
            "priority_validation": priority_check,
            "recommended_courses": recommended_courses,
            "is_valid": is_valid
        }
    
    #프롬프트 생성 함수
    def _create_prompt(self, input_data: Dict[str, Any]) -> str:
        previous_courses = input_data.get("previous_courses", [])
        available_courses = input_data.get("available_courses", [])
        target_credits = input_data.get("target_credits", 0)
        max_web_credits = input_data.get("max_web_credits", None)  # 웹강의 최대 학점
        priority_order = input_data.get("priority_order", [1, 2, 3, 4, 5])
        core_category_constraint = input_data.get("core_category_constraint", False)
        user_feedback = input_data.get("user_feedback", None)  # 사용자 피드백
        
        # 과목 정보를 표준 형식으로 변환
        previous_normalized = [self._get_course_info(c) for c in previous_courses]
        
        # 우선순위별로 그룹화
        priority_groups = {}
        for course in available_courses:
            normalized = self._get_course_info(course)
            priority = course.get("priority", 5)
            category = course.get("category", "일반교양")
            core_cat_id = course.get("core_category_id")
            is_web = course.get("is_web", False)
            
            if priority not in priority_groups:
                priority_groups[priority] = []
            
            priority_groups[priority].append({
                **normalized,
                "category": category,
                "core_category_id": core_cat_id,
                "is_web": is_web
            })
        
        previous_text = "\n".join([
            f"- {c['학수번호']}: {c['과목명']} (시간: {c['시간'] or '없음'}, 학점: {c['학점']})"
            for c in previous_normalized if c['학수번호']
        ]) if previous_normalized else "없음"
        
        # 우선순위별로 과목 목록 구성
        priority_names = {
            1: "전공필수",
            2: "전공선택",
            3: "기초/중점 교양",
            4: "핵심교양",
            5: "일반교양"
        }
        
        courses_sections = []
        for priority in priority_order:
            if priority not in priority_groups:
                continue
            
            category_name = priority_names.get(priority, f"우선순위{priority}")
            courses_list = priority_groups[priority]
            
            # 핵심교양의 경우 카테고리별로 구분
            if priority == 4 and core_category_constraint:
                # 카테고리별로 그룹화
                cat_groups = {}
                for c in courses_list:
                    cat_id = c.get("core_category_id")
                    if cat_id:
                        if cat_id not in cat_groups:
                            cat_groups[cat_id] = []
                        cat_groups[cat_id].append(c)
                
                for cat_id in sorted(cat_groups.keys()):
                    cat_courses = cat_groups[cat_id]
                    cat_text = "\n".join([
                        f"  - {c['학수번호']}: {c['과목명']} (시간: {c['시간'] or '없음'}, 학점: {c['학점']}, {'웹강의' if c.get('is_web') else '대면'})"
                        for c in cat_courses if c['학수번호']
                    ])
                    courses_sections.append(f"[{category_name} - 카테고리 {cat_id}] (⚠️ 카테고리당 최대 1개만 선택 가능):\n{cat_text}")
            else:
                cat_text = "\n".join([
                    f"  - {c['학수번호']}: {c['과목명']} (시간: {c['시간'] or '없음'}, 학점: {c['학점']}, {'웹강의' if c.get('is_web') else '대면'})"
                    for c in courses_list if c['학수번호']
                ])
                courses_sections.append(f"[{category_name}]:\n{cat_text}")
        
        courses_text = "\n\n".join(courses_sections)
        
        constraints = []
        if core_category_constraint:
            constraints.append("⚠️ 중요: 핵심교양은 같은 카테고리에서 최대 1개 과목만 선택 가능합니다.")
        if max_web_credits is not None:
            constraints.append(f"⚠️ 중요: 웹강의(온라인 강의)는 총 {max_web_credits}학점을 초과할 수 없습니다.")
        core_credits_target = input_data.get("core_credits_target")
        if core_credits_target is not None and core_credits_target > 0:
            constraints.append(f"⚠️ 중요: 핵심교양 학점의 총합은 정확히 {core_credits_target}와 일치해야 합니다.")
        
        constraints_text = "\n".join(constraints) if constraints else ""
        
        # priority_order가 [3, 4, 5]로 시작하면 전공필수/전공선택이 이미 포함된 것
        if priority_order and len(priority_order) > 0 and priority_order[0] != 1:
            # 전공필수/전공선택이 이미 포함된 경우
            included_priorities = []
            if 1 not in priority_order:
                included_priorities.append("전공필수")
            if 2 not in priority_order:
                included_priorities.append("전공선택")
            
            priority_instruction = f"""
⚠️ 중요: 전공필수와 전공선택은 이미 시간표에 포함되어 있습니다.
따라서 아래 과목 목록에서만 선택하시면 됩니다.

현재 선택 가능한 우선순위:
{', '.join([priority_names.get(p, f'우선순위{p}') for p in priority_order])}

⚠️ 선택 방법:
1. 우선순위가 높은 순서대로 가능한 학점을 배정합니다: {priority_order[0]}순위 -> {priority_order[1] if len(priority_order) > 1 else ''}순위 -> {priority_order[2] if len(priority_order) > 2 else ''}순위
2. 각 우선순위 내에서 여러 과목을 선택할 수 있습니다
   - 각 우선순위에서 목표 학점을 채울 수 있을 때까지 여러 과목 선택
3. 검증 실패 시 같은 우선순위 내에서 다른 과목 조합을 시도할 수 있습니다
   - 우선순위 순서는 유지하되, 각 우선순위 내에서 다른 과목 선택 시도

이 우선순위 규칙은 다른 모든 조건보다 우선합니다!"""
        else:
            priority_instruction = f"""

우선순위 순서
1순위: 전공필수 (최우선 - 반드시 먼저 선택)
2순위: 전공선택 (1순위 처리 후)
3순위: 기초/중점 교양 (2순위 처리 후)
4순위: 핵심교양 (3순위 처리 후)
5순위: 일반교양 (최후순위 - 4순위 처리 후)

⚠️ 선택 방법:
1. 우선순위가 높은 순서대로 가능한 학점을 배정합니다: 1순위 -> 2순위 -> 3순위 -> 4순위 -> 5순위
2. 각 우선순위 내에서 여러 과목을 선택할 수 있습니다
   - 예: 전공필수에서 3개 과목(9학점), 전공선택에서 2개 과목(6학점) 선택 가능
   - 각 우선순위에서 목표 학점을 채울 수 있을 때까지 여러 과목 선택
3. 검증 실패 시 같은 우선순위 내에서 다른 과목 조합을 시도할 수 있습니다
   - 예: 전공필수 A, B, C 선택 후 검증 실패 → A, B, D 또는 A, C, E 등 다른 조합 시도
   - 우선순위 순서는 유지하되, 각 우선순위 내에서 다른 과목 선택 시도

이 우선순위 규칙은 다른 모든 조건보다 우선합니다!"""
        
        # 사용자 피드백이 있으면 추가
        feedback_section = ""
        if user_feedback and user_feedback.strip():
            feedback_section = f"""
═══════════════════════════════════════════════════════════════
💬 사용자 피드백
═══════════════════════════════════════════════════════════════
{user_feedback}

⚠️ 중요: 위 피드백을 반드시 고려하여 새로운 시간표를 추천해주세요.
이전 추천과 다른 방향으로 개선된 시간표를 제안해주세요.

"""
        
        return f"""이전 수강 내역:
{previous_text}

사용 가능한 과목 목록 (우선순위별):
{courses_text}

목표 학점: {target_credits}학점

{constraints_text}

{priority_instruction}

{feedback_section}═══════════════════════════════════════════════════════════════
📋 추천 조건 (반드시 순서대로 준수)
═══════════════════════════════════════════════════════════════

[필수 조건 - 반드시 만족해야 함]

1. 우선순위 순서 반드시 준수
   - 우선순위가 높은 순서대로 가능한 학점을 채웁니다
   - 각 우선순위 내에서 여러 과목을 선택할 수 있습니다
   - 예: 기초/중점 교양 3개(9학점), 핵심교양 2개(6학점) 등
   - 낮은 우선순위를 선택하기 전에 높은 우선순위의 모든 가능한 과목을 먼저 고려

2. 목표 학점({target_credits}학점)을 초과하지 않으면서 최대한 많은 학점을 채우도록 선택
   - 목표 학점 이하의 최대값을 선택 (예: 목표 18학점이면 17학점보다 18학점이 더 좋음)
   - 단, 우선순위 순서를 준수하면서 선택해야 함

3. 핵심교양 학점을 정확히 목표 학점과 일치하도록 선택
   {f'(목표: {core_credits_target}학점)' if core_credits_target and core_credits_target > 0 else ''}

4. 핵심교양은 같은 카테고리에서 중복 선택하지 않기 (카테고리당 최대 1개)

5. 시간이 겹치지 않도록 과목 선택

6. 웹강의 학점 제한을 준수 (최대 9학점)

[추가 고려사항]
- 이전 수강 내역과 연관성 있는 과목 우선 추천
- 각 과목은 한 번만 선택 (중복 선택 금지)
- 각 과목의 학수번호를 정확히 포함 (예: AIE1001, GEE1002)

과목을 추천해주세요. 학수번호를 명확히 표시해주세요.

추가로, 추천한 시간표에 대한 설명이나 제안을 간단히 제공해주세요:
- 이 시간표의 장점이나 특징
- 주의할 점이나 보완 제안
- 추가 고려사항 등

응답 형식:
[추천 과목]
- 학수번호1, 학수번호2, ...

[추천 시간표에 대한 제안]
여기에 제안이나 설명을 작성해주세요."""
    
    def _create_retry_prompt(self, input_data: Dict[str, Any], previous_validation: Dict[str, Any]) -> str:
        """재시도용 프롬프트 생성"""
        base_prompt = self._create_prompt(input_data)
        
        issues = []
        credits_val = previous_validation.get("credits_validation", {})
        if not credits_val.get("is_valid", True):
            issues.append(f"학점 초과: 목표 {credits_val.get('target_credits')}학점 이하여야 하지만 {credits_val.get('total_credits')}학점으로 추천됨 (초과: {credits_val.get('total_credits', 0) - credits_val.get('target_credits', 0):.1f}학점)")
        
        time_val = previous_validation.get("time_validation", {})
        if time_val.get("has_conflict", False):
            conflicts = time_val.get("conflicts", [])
            conflict_details = "\n".join([
                f"- {c['과목1']['학수번호']}와 {c['과목2']['학수번호']}가 {c['충돌_요일']}요일 {c['충돌_시간']}교시에 충돌"
                for c in conflicts
            ])
            issues.append(f"시간 충돌:\n{conflict_details}")
        
        web_val = previous_validation.get("web_credits_validation", {})
        if not web_val.get("is_valid", True):
            issues.append(f"웹강의 학점 초과: {web_val.get('total_web_credits', 0)}학점이 선택되었지만 최대 {web_val.get('max_web_credits', 9)}학점까지만 가능합니다.")
        
        category_val = previous_validation.get("category_validation", {})
        if not category_val.get("is_valid", True):
            violations = category_val.get("violations", [])
            issues.append(f"카테고리 제한 위반: {chr(10).join('- ' + v for v in violations)}")
        
        core_credits_val = previous_validation.get("core_credits_validation", {})
        if not core_credits_val.get("is_valid", True):
            diff = core_credits_val.get('total_core_credits', 0) - core_credits_val.get('target_core_credits', 0)
            issues.append(f"핵심교양 학점 불일치: 목표 {core_credits_val.get('target_core_credits', 0)}학점이지만 {core_credits_val.get('total_core_credits', 0)}학점으로 추천됨 (차이: {diff:+.1f}학점)")
        
        priority_val = previous_validation.get("priority_validation", {})
        if not priority_val.get("is_valid", True):
            violations = priority_val.get("violations", [])
            issues.append(f"⚠️ 우선순위 위반 (중요!): {chr(10).join('- ' + v for v in violations)} - 반드시 높은 우선순위부터 선택해야 합니다.")
        
        prev_codes = [c.get("학수번호", "") for c in previous_validation.get("recommended_courses", [])]
        
        return f"""{base_prompt}

⚠️ 이전 추천 시도에서 문제가 발견되어 다시 요청합니다.

이전 추천 결과: {', '.join(prev_codes) if prev_codes else '없음'}

발견된 문제점:
{chr(10).join(f'- {issue}' for issue in issues) if issues else '- 없음'}

위 문제점을 해결하여 다시 추천해주세요.

⚠️ 중요: 검증 실패 시 같은 우선순위 내에서 다른 과목 조합을 고려해보세요.
- 예: 전공필수에서 A, B, C를 선택했는데 검증 실패 → A, B, D 또는 A, C, E 등 다른 조합 시도
- 우선순위 순서는 유지하되, 각 우선순위 내에서 다른 과목 선택을 시도하세요."""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """응답 파싱 (학수번호 추출 및 제안 추출)"""
        codes = re.findall(r'\b([A-Z]{3}\d{4})\b', response)
        # 중복 제거 (순서 유지)
        seen = set()
        unique_codes = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        
        # 추가 제안 추출
        suggestion = ""
        # "[추천 시간표에 대한 제안]" 또는 "[제안]" 등의 섹션 찾기
        suggestion_patterns = [
            r'\[추천 시간표에 대한 제안\]\s*\n?(.+?)(?=\n\n|\n\[|$)',
            r'\[제안\]\s*\n?(.+?)(?=\n\n|\n\[|$)',
            r'추천 시간표에 대한 제안[:\s]*\n?(.+?)(?=\n\n|\n\[|$)',
            r'제안[:\s]*\n?(.+?)(?=\n\n|\n\[|$)',
        ]
        
        for pattern in suggestion_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                suggestion = match.group(1).strip()
                break
        
        # 패턴이 없으면 전체 응답에서 학수번호 부분을 제외한 나머지 추출 시도
        if not suggestion:
            # 학수번호 부분을 제거하고 나머지 텍스트 추출
            lines = response.split('\n')
            suggestion_lines = []
            in_suggestion = False
            for line in lines:
                # 학수번호가 포함된 줄은 건너뛰기
                if re.search(r'\b([A-Z]{3}\d{4})\b', line):
                    continue
                # "추천 과목", "학수번호" 등의 헤더는 건너뛰기
                if re.search(r'(추천 과목|학수번호|과목 추천|추천)', line, re.IGNORECASE):
                    continue
                # 숫자로 시작하는 리스트 항목은 건너뛰기 (1. AIE1002 같은 형식)
                if re.match(r'^\d+\.?\s*[A-Z]{3}\d{4}', line):
                    continue
                # 빈 줄이 아닌 의미있는 내용만 추가
                if line.strip() and len(line.strip()) > 10:
                    suggestion_lines.append(line.strip())
            
            if suggestion_lines:
                suggestion = '\n'.join(suggestion_lines[:10])  # 최대 10줄만
        
        return {
            "recommended_codes": unique_codes,
            "raw_response": response,
            "suggestion": suggestion
        }
    
    def _save_log(self, input_data: Dict[str, Any], prompt: str, response: str, result: Dict[str, Any], validation: Optional[Dict[str, Any]] = None):
        """로그 저장"""
        if not self.enable_logging:
            return
        
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = self.log_dir / f"recommendation_log_{timestamp}.json"
        
        log_data = {
            "timestamp": dt.now().isoformat(),
            "input_data": input_data,
            "prompt": prompt,
            "response": response,
            "result": result,
            "validation": validation
        }
        
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"로그 저장 실패: {e}")
    
    def recommend(
        self,
        input_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """과목 추천 수행"""
        system_prompt = "당신은 시간표 작성 전문가입니다. 학생의 수강 과목 정보를 바탕으로 주어진 학점 내에서 최대한의 전공 과목 학점과 전체 학점을 채울 수 있도록 수강내역을 고려하여 작성하세요."
        
        for attempt in range(max_retries):
            # 프롬프트 생성
            if attempt > 0 and "previous_validation" in locals():
                prompt = self._create_retry_prompt(input_data, previous_validation)
            else:
                prompt = self._create_prompt(input_data)
            
            # LLM 호출
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
            response = self.llm.invoke(messages).content
            
            # 응답 파싱
            result = self._parse_response(response)
            result["attempt"] = attempt + 1
            
            # 검증
            available_courses = input_data.get("available_courses", [])
            validation = self._validate_result(result, input_data, available_courses)
            result["validation"] = validation
            
            # 검증 통과 시 반환
            if validation["is_valid"]:
                self._save_log(input_data, prompt, response, result, validation)
                return result
            
            previous_validation = validation
            
            # 마지막 시도가 아니면 계속
            if attempt < max_retries - 1:
                print(f"검증 실패 (시도 {attempt + 1}/{max_retries}). 재시도 중...")
        
        # 모든 시도 실패
        self._save_log(input_data, prompt, response, result, validation)
        print(f"최대 재시도 횟수({max_retries})에 도달했습니다.")
        return result


def recommend(
    input_data: Dict[str, Any],
    llm_model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_retries: int = 3,
    enable_logging: bool = True,
    log_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    과목 추천 함수
    
    Args:
        input_data: 입력 데이터 (파일 상단 주석 참고)
            - previous_courses: 이전 수강 내역 (main.py 형식)
            - available_courses: 사용 가능한 과목 목록 (main.py 형식)
            - target_credits: 목표 학점
        llm_model: LLM 모델명 (기본값: "gpt-3.5-turbo")
        temperature: 모델 온도 (기본값: 0.7)
        max_retries: 최대 재시도 횟수 (기본값: 3)
        enable_logging: 로깅 활성화 여부 (기본값: True)
        log_dir: 로그 저장 디렉토리 (None이면 recommendation/logs 사용)
    
    Returns:
        {
            "recommended_codes": ["GEE1001", "GEE1002", ...],
            "raw_response": "...",
            "attempt": 1,
            "validation": {
                "credits_validation": {...},
                "time_validation": {...},
                "recommended_courses": [...],
                "is_valid": True/False
            }
        }
    """
    recommender = CourseRecommender(
        llm_model=llm_model,
        temperature=temperature,
        enable_logging=enable_logging,
        log_dir=log_dir
    )
    
    return recommender.recommend(input_data, max_retries=max_retries)


if __name__ == "__main__":
    # 예제 사용법 (main.py 형식)
    # API 키는 .env 파일에서 자동으로 로드됩니다
    # 또는 환경 변수로 설정: export OPENAI_API_KEY=your-key-here
    
    input_data = {
        "previous_courses": [
            {"course_id": "GEE1001", "course_name": "명언으로 배우는 한자와 한문", "time_raw": "월1,2,3", "credit": 3}
        ],
        "available_courses": [
            {"course_id": "GEE1001", "course_name": "명언으로 배우는 한자와 한문", "time_raw": "월1,2,3", "credit": 3},
            {"course_id": "GEE1002", "course_name": "동화와 마법의 상상력", "time_raw": "화3,4,5", "credit": 3},
            {"course_id": "GEE1005", "course_name": "영화로 보는 한국문화", "time_raw": "수1,2,3", "credit": 3},
            {"course_id": "GEE1006", "course_name": "동화의이해", "time_raw": "목2,3,4", "credit": 3},
            {"course_id": "GEE1012", "course_name": "창작을 위한 글쓰기 실습", "time_raw": "금1,2,3", "credit": 3}
        ],
        "target_credits": 15
    }
    
    result = recommend(input_data, enable_logging=True, max_retries=3)
    
    print("\n추천 결과:")
    print("-" * 60)
    if result.get("validation", {}).get("is_valid"):
        print("✅ 검증 통과")
        print(f"추천된 과목: {', '.join(result['recommended_codes'])}")
    else:
        print("❌ 검증 실패")
    print(result)

