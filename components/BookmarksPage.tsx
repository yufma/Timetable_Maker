import { Course } from "../types/course";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Heart, Clock, Users, BookOpen, Trash2 } from "lucide-react";

interface BookmarksPageProps {
  courses: Course[];
  bookmarkedCourses: string[];
  onToggleBookmark: (courseId: string) => void;
  onSelectCourse: (course: Course) => void;
}

export function BookmarksPage({
  courses,
  bookmarkedCourses,
  onToggleBookmark,
  onSelectCourse,
}: BookmarksPageProps) {
  const bookmarkedCourseList = courses.filter((course) =>
    bookmarkedCourses.includes(course.id)
  );

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      전공필수: "bg-red-100 text-red-800 border-red-200",
      전공선택: "bg-blue-100 text-blue-800 border-blue-200",
      기초교양: "bg-green-100 text-green-800 border-green-200",
      핵심교양: "bg-purple-100 text-purple-800 border-purple-200",
      일반교양: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
    return colors[category] || "bg-gray-100 text-gray-800 border-gray-200";
  };

  return (
    <div className="container mx-auto px-6 lg:px-8 py-10 lg:py-14 max-w-6xl lg:max-w-7xl">
      <div className="mb-8 lg:mb-10">
        <h1 className="mb-2 text-2xl lg:text-3xl">찜한 강의</h1>
        <p className="text-muted-foreground">
          {bookmarkedCourseList.length}개의 강의를 찜했습니다
        </p>
      </div>

      {bookmarkedCourseList.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Heart className="mx-auto mb-4 text-muted-foreground" size={48} />
            <h3 className="mb-2">찜한 강의가 없습니다</h3>
            <p className="text-muted-foreground mb-4">
              관심있는 강의를 찜 목록에 추가해보세요
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-5">
          {bookmarkedCourseList.map((course) => (
            <Card key={course.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="mb-2">{course.courseName}</h3>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <Badge className={getCategoryColor(course.category)}>
                        {course.category}
                      </Badge>
                      <Badge variant="outline">{course.courseCode}</Badge>
                      <Badge variant="outline">{course.section}분반</Badge>
                      <Badge variant="outline">{course.credits}학점</Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onToggleBookmark(course.id)}
                    className="text-red-500"
                  >
                    <Trash2 size={20} />
                  </Button>
                </div>

                <div className="grid grid-cols-2 gap-6 mb-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <BookOpen size={16} className="text-muted-foreground" />
                      <span>{course.professor}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock size={16} />
                      {course.time.map((t, i) => (
                        <span key={i}>
                          {t.day} {t.startTime}-{t.endTime}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Users size={16} />
                      수강인원: {course.enrolled}/{course.capacity}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {course.department} · {course.grade}학년
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectCourse(course)}
                  >
                    강의계획서 보기
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {bookmarkedCourseList.length > 0 && (
        <Card className="mt-10 bg-muted/30">
          <CardContent className="p-6">
            <h4 className="mb-4">학점 통계</h4>
            <div className="grid grid-cols-4 gap-6">
              <div>
                <p className="text-muted-foreground text-sm">총 학점</p>
                <p className="text-2xl">
                  {bookmarkedCourseList.reduce((sum, c) => sum + c.credits, 0)}학점
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-sm">전공 과목</p>
                <p className="text-2xl">
                  {
                    bookmarkedCourseList.filter(
                      (c) => c.category === "전공필수" || c.category === "전공선택"
                    ).length
                  }
                  개
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-sm">교양 과목</p>
                <p className="text-2xl">
                  {
                    bookmarkedCourseList.filter((c) =>
                      c.category.includes("교양")
                    ).length
                  }
                  개
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-sm">평균 팀플 비중</p>
                <p className="text-2xl">
                  {Math.round(
                    bookmarkedCourseList.reduce(
                      (sum, c) => sum + c.syllabus.evaluationMethod.teamProject,
                      0
                    ) / bookmarkedCourseList.length
                  )}
                  %
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}