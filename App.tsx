import { useState } from "react";
import { LoginPage } from "./components/LoginPage";
import { Navigation } from "./components/Navigation";
import { HomePage } from "./components/HomePage";
import { CourseSearchPage } from "./components/CourseSearchPage";
import { CourseDetailPage } from "./components/CourseDetailPage";
import { BookmarksPage } from "./components/BookmarksPage";
import { TimetableRecommendPage } from "./components/TimetableRecommendPage";
import { mockCourses } from "./data/mockCourses";
import { Course } from "./types/course";
import { useLocalStorage } from "./hooks/useLocalStorage";

type PageType =
  | "home"
  | "search"
  | "recommend"
  | "bookmarks"
  | "detail";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useLocalStorage(
    "isLoggedIn",
    false,
  );
  const [userName, setUserName] = useLocalStorage(
    "userName",
    "",
  );
  const [currentPage, setCurrentPage] =
    useState<PageType>("home");
  const [selectedCourse, setSelectedCourse] =
    useState<Course | null>(null);
  const [bookmarkedCourses, setBookmarkedCourses] =
    useLocalStorage<string[]>("bookmarkedCourses", []);
  const [completedCourses, setCompletedCourses] =
    useLocalStorage<string[]>("completedCourses", []);

  const handleLogin = (studentId: string, password: string) => {
    setIsLoggedIn(true);
    setUserName(`${studentId.slice(0, 4)}학번`);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserName("");
    setCurrentPage("home");
  };

  const handleToggleBookmark = (courseId: string) => {
    if (bookmarkedCourses.includes(courseId)) {
      setBookmarkedCourses(
        bookmarkedCourses.filter((id) => id !== courseId),
      );
    } else {
      setBookmarkedCourses([...bookmarkedCourses, courseId]);
    }
  };

  const handleSelectCourse = (course: Course) => {
    setSelectedCourse(course);
    setCurrentPage("detail");
  };

  const handleNavigate = (page: string) => {
    setCurrentPage(page as PageType);
    setSelectedCourse(null);
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation
        currentPage={currentPage}
        onNavigate={handleNavigate}
        onLogout={handleLogout}
        userName={userName}
      />
      <main className="w-full">
        {currentPage === "home" && (
          <HomePage
            onNavigate={handleNavigate}
            bookmarkedCount={bookmarkedCourses.length}
          />
        )}
        {currentPage === "search" && (
          <CourseSearchPage
            courses={mockCourses}
            bookmarkedCourses={bookmarkedCourses}
            onToggleBookmark={handleToggleBookmark}
            onSelectCourse={handleSelectCourse}
          />
        )}
        {currentPage === "recommend" && (
          <TimetableRecommendPage
            courses={mockCourses}
            completedCourses={completedCourses}
            onUpdateCompletedCourses={setCompletedCourses}
          />
        )}
        {currentPage === "bookmarks" && (
          <BookmarksPage
            courses={mockCourses}
            bookmarkedCourses={bookmarkedCourses}
            onToggleBookmark={handleToggleBookmark}
            onSelectCourse={handleSelectCourse}
          />
        )}
        {currentPage === "detail" && selectedCourse && (
          <CourseDetailPage
            course={selectedCourse}
            onBack={() => setCurrentPage("search")}
            isBookmarked={bookmarkedCourses.includes(
              selectedCourse.id,
            )}
            onToggleBookmark={() =>
              handleToggleBookmark(selectedCourse.id)
            }
            relatedCourses={mockCourses.filter(
              (c) =>
                c.courseCode === selectedCourse.courseCode &&
                c.id !== selectedCourse.id,
            )}
            onSelectCourse={handleSelectCourse}
          />
        )}
      </main>
    </div>
  );
}