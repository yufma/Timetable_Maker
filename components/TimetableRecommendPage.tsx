import { useState } from "react";
import { Course } from "../types/course";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { Sparkles, RefreshCw, Download } from "lucide-react";
import { TimetableView } from "./TimetableView";

interface TimetableRecommendPageProps {
  courses: Course[];
  completedCourses: string[];
  onUpdateCompletedCourses: (courses: string[]) => void;
}

export function TimetableRecommendPage({
  courses,
  completedCourses,
  onUpdateCompletedCourses,
}: TimetableRecommendPageProps) {
  const [step, setStep] = useState<"setup" | "result">("setup");
  const [selectedDepartment, setSelectedDepartment] = useState("컴퓨터공학과");
  const [selectedGrade, setSelectedGrade] = useState(2);
  const [excludedTimes, setExcludedTimes] = useState<{ day: string; time: string }[]>([]);
  const [recommendedTimetables, setRecommendedTimetables] = useState<Course[][]>([]);
  const [selectedTimetableIndex, setSelectedTimetableIndex] = useState(0);

  const days = ["월", "화", "수", "목", "금"];
  const times = [
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
  ];

  const toggleExcludedTime = (day: string, time: string) => {
    const key = `${day}-${time}`;
    const exists = excludedTimes.some((t) => `${t.day}-${t.time}` === key);
    if (exists) {
      setExcludedTimes(excludedTimes.filter((t) => `${t.day}-${t.time}` !== key));
    } else {
      setExcludedTimes([...excludedTimes, { day, time }]);
    }
  };

  const isTimeExcluded = (day: string, time: string) => {
    return excludedTimes.some((t) => t.day === day && t.time === time);
  };

  const generateTimetable = () => {
    const availableCourses = courses.filter((course) => {
      if (course.department !== selectedDepartment && !course.category.includes("교양")) {
        return false;
      }

      if (completedCourses.includes(course.id)) {
        return false;
      }

      for (const timeSlot of course.time) {
        for (const excluded of excludedTimes) {
          if (timeSlot.day === excluded.day) {
            const courseStart = parseInt(timeSlot.startTime.split(":")[0]);
            const excludedHour = parseInt(excluded.time.split(":")[0]);
            if (courseStart === excludedHour) {
              return false;
            }
          }
        }
      }

      return true;
    });

    const priorityOrder = ["기초교양", "전공필수", "전공선택", "핵심교양", "일반교양"];

    const sortedCourses = [...availableCourses].sort((a, b) => {
      const aPriority = priorityOrder.indexOf(a.category);
      const bPriority = priorityOrder.indexOf(b.category);
      return aPriority - bPriority;
    });

    const timetables: Course[][] = [];

    for (let i = 0; i < 3; i++) {
      const timetable: Course[] = [];
      const usedTimeSlots: string[] = [];
      let totalCredits = 0;
      const maxCredits = 18;

      for (const course of sortedCourses) {
        if (totalCredits + course.credits > maxCredits) continue;

        let hasConflict = false;
        for (const timeSlot of course.time) {
          const key = `${timeSlot.day}-${timeSlot.startTime}`;
          if (usedTimeSlots.includes(key)) {
            hasConflict = true;
            break;
          }
        }

        if (!hasConflict) {
          timetable.push(course);
          totalCredits += course.credits;
          for (const timeSlot of course.time) {
            usedTimeSlots.push(`${timeSlot.day}-${timeSlot.startTime}`);
          }
        }

        if (timetable.length >= 6) break;
      }

      if (timetable.length > 0) {
        timetables.push(timetable);
      }
    }

    setRecommendedTimetables(timetables);
    setSelectedTimetableIndex(0);
    setStep("result");
  };

  if (step === "result") {
    const currentTimetable = recommendedTimetables[selectedTimetableIndex] || [];
    const totalCredits = currentTimetable.reduce((sum, c) => sum + c.credits, 0);

    return (
      <div className="container mx-auto px-6 lg:px-8 py-10 lg:py-14 max-w-6xl">
        <div className="mb-8">
          <Button variant="ghost" onClick={() => setStep("setup")} className="mb-4">
            ← 설정으로 돌아가기
          </Button>
          <h1 className="mb-2">추천 시간표</h1>
          <p className="text-muted-foreground">
            {recommendedTimetables.length}개의 시간표 옵션이 생성되었습니다
          </p>
        </div>

        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {recommendedTimetables.map((_, index) => (
            <Button
              key={index}
              variant={selectedTimetableIndex === index ? "default" : "outline"}
              onClick={() => setSelectedTimetableIndex(index)}
            >
              옵션 {index + 1}
            </Button>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TimetableView courses={currentTimetable} />
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>시간표 정보</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-muted-foreground text-sm">총 학점</p>
                    <p className="text-2xl">{totalCredits}학점</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-sm">과목 수</p>
                    <p className="text-2xl">{currentTimetable.length}개</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button className="flex-1" size="sm">
                    <Download size={16} className="mr-2" />
                    저장
                  </Button>
                  <Button variant="outline" size="sm" onClick={generateTimetable}>
                    <RefreshCw size={16} className="mr-2" />
                    재생성
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>과목 목록</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {currentTimetable.map((course) => (
                    <div key={course.id} className="p-3 border border-border rounded-lg">
                      <div className="mb-2">
                        <h4 className="text-sm">{course.courseName}</h4>
                        <p className="text-xs text-muted-foreground">{course.professor}</p>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant="outline" className="text-xs">
                          {course.category}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {course.credits}학점
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 lg:px-8 py-10 lg:py-14 max-w-5xl">
      <div className="mb-8">
        <h1 className="mb-2">시간표 추천 설정</h1>
        <p className="text-muted-foreground">정보를 입력하면 최적의 시간표를 추천해드립니다</p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>기본 정보</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block mb-2">학과</label>
              <select
                className="w-full p-2 border border-border rounded-md"
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
              >
                <option>인공지능공학과</option>
                <option>전기공학과</option>
                <option>기계공학과</option>
              </select>
            </div>
            <div>
              <label className="block mb-2">학년</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4].map((grade) => (
                  <Button
                    key={grade}
                    variant={selectedGrade === grade ? "default" : "outline"}
                    onClick={() => setSelectedGrade(grade)}
                  >
                    {grade}학년
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>제외할 시간대</CardTitle>
            <p className="text-sm text-muted-foreground">수업을 듣고 싶지 않은 시간을 선택하세요</p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border border-border p-2 bg-muted">시간</th>
                    {days.map((day) => (
                      <th key={day} className="border border-border p-2 bg-muted">
                        {day}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {times.map((time) => (
                    <tr key={time}>
                      <td className="border border-border p-2 text-sm text-center">{time}</td>
                      {days.map((day) => (
                        <td
                          key={`${day}-${time}`}
                          className={`border border-border p-2 text-center cursor-pointer hover:bg-accent ${
                            isTimeExcluded(day, time) ? "bg-red-100" : ""
                          }`}
                          onClick={() => toggleExcludedTime(day, time)}
                        >
                          {isTimeExcluded(day, time) && "✕"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-sm text-muted-foreground mt-4">클릭하여 제외할 시간을 선택하세요</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>수강 완료 과목</CardTitle>
            <p className="text-sm text-muted-foreground">이미 수강한 과목을 선택하세요 (추천에서 제외됩니다)</p>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
              {courses
                .filter((c) => c.department === selectedDepartment || c.category.includes("교양"))
                .map((course) => (
                  <div key={course.id} className="flex items-center gap-2">
                    <Checkbox
                      id={`completed-${course.id}`}
                      checked={completedCourses.includes(course.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          onUpdateCompletedCourses([...completedCourses, course.id]);
                        } else {
                          onUpdateCompletedCourses(
                            completedCourses.filter((id) => id !== course.id),
                          );
                        }
                      }}
                    />
                    <label htmlFor={`completed-${course.id}`} className="text-sm cursor-pointer">
                      {course.courseName}
                    </label>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        <Button onClick={generateTimetable} size="lg" className="w-full group">
          <Sparkles className="mr-2 group-hover:rotate-12 transition-transform" size={20} />
          시간표 추천받기
        </Button>
      </div>
    </div>
  );
}