export interface Course {
  id: string;
  courseCode: string;
  courseName: string;
  professor: string;
  credits: number;
  time: TimeSlot[];
  room: string;
  category: "기초교양" | "핵심교양" | "일반교양" | "전공필수" | "전공선택";
  department: string;
  grade: number; // 학년
  section: string; // 분반
  capacity: number;
  enrolled: number;
  syllabus: Syllabus;
}

export interface TimeSlot {
  day: "월" | "화" | "수" | "목" | "금";
  startTime: string;
  endTime: string;
}

export interface Syllabus {
  courseObjective: string;
  evaluationMethod: {
    midterm: number;
    final: number;
    assignment: number;
    attendance: number;
    teamProject: number;
    others: number;
  };
  weeklyPlan: WeeklyPlan[];
  textbook: string;
  notes: string;
}

export interface WeeklyPlan {
  week: number;
  topic: string;
  content: string;
}

export interface TimetableSlot {
  course: Course;
  color: string;
}

export interface UserProfile {
  studentId: string;
  name: string;
  department: string;
  grade: number;
  completedCourses: string[]; // course IDs
  bookmarkedCourses: string[]; // course IDs
}

export interface TimePreference {
  preferredTimes: TimeSlot[];
  excludedTimes: TimeSlot[];
}