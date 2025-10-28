import { useState } from "react";
import { Course } from "../types/course";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Search, Heart, Clock, Users, BookOpen, BarChart3 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface CourseSearchPageProps {
  courses: Course[];
  bookmarkedCourses: string[];
  onToggleBookmark: (courseId: string) => void;
  onSelectCourse: (course: Course) => void;
}

export function CourseSearchPage({
  courses,
  bookmarkedCourses,
  onToggleBookmark,
  onSelectCourse,
}: CourseSearchPageProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [departmentFilter, setDepartmentFilter] = useState<string>("all");

  const filteredCourses = courses.filter((course) => {
    const matchesSearch =
      course.courseName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      course.courseCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      course.professor.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = categoryFilter === "all" || course.category === categoryFilter;
    const matchesDepartment = departmentFilter === "all" || course.department === departmentFilter;

    return matchesSearch && matchesCategory && matchesDepartment;
  });

  const categories = Array.from(new Set(courses.map((c) => c.category)));
  const departments = Array.from(new Set(courses.map((c) => c.department)));

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

  // Group courses by courseCode to find sections
  const courseGroups = filteredCourses.reduce((acc, course) => {
    if (!acc[course.courseCode]) {
      acc[course.courseCode] = [];
    }
    acc[course.courseCode].push(course);
    return acc;
  }, {} as Record<string, Course[]>);

  return (
    <div className="container mx-auto px-6 lg:px-8 py-10 lg:py-14 max-w-6xl lg:max-w-7xl">
      <div className="mb-8 lg:mb-10 flex items-end justify-between gap-4">
        <div>
          <h1 className="mb-2 text-2xl lg:text-3xl">강의 검색</h1>
          <p className="text-muted-foreground">강의명, 학수번호, 교수명으로 검색하세요</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4 mb-8">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
            <Input
              type="text"
              placeholder="강의명, 학수번호, 교수명 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 h-11"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="분류" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 분류</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="학과" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 학과</SelectItem>
              {departments.map((dept) => (
                <SelectItem key={dept} value={dept}>
                  {dept}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {(categoryFilter !== "all" || departmentFilter !== "all" || searchTerm) && (
            <Button
              variant="outline"
              onClick={() => {
                setCategoryFilter("all");
                setDepartmentFilter("all");
                setSearchTerm("");
              }}
            >
              필터 초기화
            </Button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="mb-4">
        <p className="text-muted-foreground">
          {filteredCourses.length}개의 강의가 검색되었습니다
        </p>
      </div>

      {/* Course List */}
      <div className="space-y-5">
        {Object.entries(courseGroups).map(([courseCode, courseSections]) => {
          const firstCourse = courseSections[0];
          const hasMultipleSections = courseSections.length > 1;

          return (
            <Card key={courseCode} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-start gap-3 mb-2">
                      <h3 className="flex-1">{firstCourse.courseName}</h3>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onToggleBookmark(firstCourse.id)}
                        className={bookmarkedCourses.includes(firstCourse.id) ? "text-red-500" : ""}
                      >
                        <Heart
                          size={20}
                          fill={bookmarkedCourses.includes(firstCourse.id) ? "currentColor" : "none"}
                        />
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <Badge className={getCategoryColor(firstCourse.category)}>
                        {firstCourse.category}
                      </Badge>
                      <Badge variant="outline">{firstCourse.courseCode}</Badge>
                      <Badge variant="outline">{firstCourse.credits}학점</Badge>
                    </div>
                    <p className="text-muted-foreground text-sm mb-2">{firstCourse.department}</p>
                  </div>
                </div>

                {hasMultipleSections ? (
                  <div className="space-y-3">
                    <p className="text-sm">
                      {courseSections.length}개 분반 
                      <Button
                        variant="link"
                        size="sm"
                        onClick={() => onSelectCourse(firstCourse)}
                        className="ml-2"
                      >
                        비교하기
                      </Button>
                    </p>
                    <div className="space-y-2">
                      {courseSections.map((section) => (
                        <div
                          key={section.id}
                          className="border border-border rounded-lg p-4 hover:bg-accent/50 cursor-pointer"
                          onClick={() => onSelectCourse(section)}
                        >
                          <div className="grid grid-cols-2 gap-6">
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline">{section.section}분반</Badge>
                                <span>{section.professor}</span>
                              </div>
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Clock size={16} />
                                {section.time.map((t, i) => (
                                  <span key={i}>
                                    {t.day} {t.startTime}-{t.endTime}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <Users size={16} />
                                {section.enrolled}/{section.capacity}명
                              </div>
                              <div className="flex items-center gap-2 text-muted-foreground">
                                <BarChart3 size={16} />
                                팀플 {section.syllabus.evaluationMethod.teamProject}%
                                {section.syllabus.evaluationMethod.teamProject === 0 && " (없음)"}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div
                    className="border border-border rounded-lg p-4 hover:bg-accent/50 cursor-pointer"
                    onClick={() => onSelectCourse(firstCourse)}
                  >
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <BookOpen size={16} className="text-muted-foreground" />
                          <span>{firstCourse.professor}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                          <Clock size={16} />
                          {firstCourse.time.map((t, i) => (
                            <span key={i}>
                              {t.day} {t.startTime}-{t.endTime}
                            </span>
                          ))}
                        </div>
                        <div className="text-sm text-muted-foreground">{firstCourse.room}</div>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Users size={16} />
                          수강인원: {firstCourse.enrolled}/{firstCourse.capacity}
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <BarChart3 size={16} />
                          팀플 비중: {firstCourse.syllabus.evaluationMethod.teamProject}%
                        </div>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="mt-4">
                      강의계획서 보기
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}

        {filteredCourses.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <Search className="mx-auto mb-4 text-muted-foreground" size={48} />
              <p className="text-muted-foreground">검색 결과가 없습니다</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}