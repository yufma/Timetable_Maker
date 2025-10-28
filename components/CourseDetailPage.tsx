import { Course } from "../types/course";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { ArrowLeft, Heart, Clock, MapPin, Users, BookOpen } from "lucide-react";
import { Progress } from "./ui/progress";

interface CourseDetailPageProps {
  course: Course;
  onBack: () => void;
  isBookmarked: boolean;
  onToggleBookmark: () => void;
  relatedCourses?: Course[];
  onSelectCourse?: (course: Course) => void;
}

export function CourseDetailPage({
  course,
  onBack,
  isBookmarked,
  onToggleBookmark,
  relatedCourses = [],
  onSelectCourse,
}: CourseDetailPageProps) {
  const { syllabus } = course;

  return (
    <div className="container mx-auto px-6 lg:px-8 py-10 lg:py-14 max-w-5xl lg:max-w-6xl">
      <Button variant="ghost" onClick={onBack} className="mb-4">
        <ArrowLeft className="mr-2" size={18} />
        목록으로
      </Button>

      {/* Course Header */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <h1 className="mb-3 text-2xl lg:text-3xl font-medium tracking-tight">{course.courseName}</h1>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge>{course.category}</Badge>
                <Badge variant="outline">{course.courseCode}</Badge>
                <Badge variant="outline">{course.section}분반</Badge>
                <Badge variant="outline">{course.credits}학점</Badge>
              </div>
            </div>
            <Button
              variant={isBookmarked ? "default" : "outline"}
              onClick={onToggleBookmark}
            >
              <Heart size={18} className="mr-2" fill={isBookmarked ? "currentColor" : "none"} />
              {isBookmarked ? "찜 해제" : "찜하기"}
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <BookOpen size={18} />
                <span>교수: {course.professor}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock size={18} />
                <span>
                  {course.time.map((t, i) => (
                    <span key={i} className="mr-2">
                      {t.day} {t.startTime}-{t.endTime}
                    </span>
                  ))}
                </span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin size={18} />
                <span>{course.room}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Users size={18} />
                <span>
                  수강인원: {course.enrolled}/{course.capacity}
                </span>
              </div>
              <Progress value={(course.enrolled / course.capacity) * 100} className="h-2" />
              <p className="text-sm text-muted-foreground">
                {course.department} · {course.grade}학년
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Course Objective */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>강의 목표</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{syllabus.courseObjective}</p>
        </CardContent>
      </Card>

      {/* Evaluation Method */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>평가 방법</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(syllabus.evaluationMethod).map(([key, value]) => {
              if (value === 0) return null;
              const labels: Record<string, string> = {
                midterm: "중간고사",
                final: "기말고사",
                assignment: "과제",
                attendance: "출석",
                teamProject: "팀 프로젝트",
                others: "기타",
              };
              return (
                <div key={key}>
                  <div className="flex justify-between mb-2">
                    <span>{labels[key]}</span>
                    <span>{value}%</span>
                  </div>
                  <Progress value={value} className="h-2" />
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h4 className="mb-2">평가 요약</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">시험 비중</p>
                <p>
                  {syllabus.evaluationMethod.midterm + syllabus.evaluationMethod.final}%
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">과제 비중</p>
                <p>{syllabus.evaluationMethod.assignment}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">팀플 비중</p>
                <p>
                  {syllabus.evaluationMethod.teamProject}%
                  {syllabus.evaluationMethod.teamProject === 0 && " (없음)"}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Plan */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>주차별 강의 계획</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {syllabus.weeklyPlan.map((plan) => (
              <div key={plan.week} className="border-l-2 border-primary pl-4">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline">{plan.week}주차</Badge>
                  <h4>{plan.topic}</h4>
                </div>
                <p className="text-muted-foreground text-sm">{plan.content}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Additional Info */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>교재</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{syllabus.textbook}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>유의사항</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{syllabus.notes}</p>
          </CardContent>
        </Card>
      </div>

      {/* Related Courses (Same course, different sections) */}
      {relatedCourses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>다른 분반</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {relatedCourses.map((related) => (
                <div
                  key={related.id}
                  className="p-4 border border-border rounded-lg hover:bg-accent/50 cursor-pointer"
                  onClick={() => onSelectCourse?.(related)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">{related.section}분반</Badge>
                        <span>{related.professor}</span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {related.time.map((t, i) => (
                          <span key={i} className="mr-2">
                            {t.day} {t.startTime}-{t.endTime}
                          </span>
                        ))}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        팀플 {related.syllabus.evaluationMethod.teamProject}% · 과제 {related.syllabus.evaluationMethod.assignment}%
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      자세히
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}