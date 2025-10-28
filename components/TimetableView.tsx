import { Course } from "../types/course";

interface TimetableViewProps {
  courses: Course[];
}

export function TimetableView({ courses }: TimetableViewProps) {
  const days = ["월", "화", "수", "목", "금"];
  const hours = Array.from({ length: 10 }, (_, i) => 9 + i); // 9:00 to 18:00

  const colors = [
    "bg-blue-200 border-blue-400 text-blue-900",
    "bg-green-200 border-green-400 text-green-900",
    "bg-yellow-200 border-yellow-400 text-yellow-900",
    "bg-purple-200 border-purple-400 text-purple-900",
    "bg-pink-200 border-pink-400 text-pink-900",
    "bg-indigo-200 border-indigo-400 text-indigo-900",
    "bg-red-200 border-red-400 text-red-900",
    "bg-orange-200 border-orange-400 text-orange-900",
  ];

  // Assign colors to courses
  const courseColors = new Map<string, string>();
  courses.forEach((course, index) => {
    courseColors.set(course.id, colors[index % colors.length]);
  });

  // Create a grid structure
  const grid: (Course | null)[][] = days.map(() => hours.map(() => null));

  // Place courses in the grid
  courses.forEach((course) => {
    course.time.forEach((timeSlot) => {
      const dayIndex = days.indexOf(timeSlot.day);
      if (dayIndex === -1) return;

      const startHour = parseInt(timeSlot.startTime.split(":")[0]);
      const endHour = parseInt(timeSlot.endTime.split(":")[0]);
      const startMinute = parseInt(timeSlot.startTime.split(":")[1]);
      const endMinute = parseInt(timeSlot.endTime.split(":")[1]);

      for (let hour = startHour; hour < endHour; hour++) {
        const hourIndex = hours.indexOf(hour);
        if (hourIndex !== -1) {
          grid[dayIndex][hourIndex] = course;
        }
      }

      // Handle partial hours
      if (endMinute > 0) {
        const hourIndex = hours.indexOf(endHour);
        if (hourIndex !== -1 && !grid[dayIndex][hourIndex]) {
          grid[dayIndex][hourIndex] = course;
        }
      }
    });
  });

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse min-w-[600px]">
          <thead>
            <tr>
              <th className="border border-border p-2 bg-muted w-20">시간</th>
              {days.map((day) => (
                <th key={day} className="border border-border p-2 bg-muted">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {hours.map((hour, hourIndex) => (
              <tr key={hour} className="h-16">
                <td className="border border-border p-2 text-sm text-center bg-muted/50">
                  {hour}:00
                </td>
                {days.map((day, dayIndex) => {
                  const course = grid[dayIndex][hourIndex];
                  
                  // Check if this is the first cell of a course block
                  const isFirstCell =
                    course &&
                    (hourIndex === 0 || grid[dayIndex][hourIndex - 1] !== course);

                  // Calculate rowspan
                  let rowspan = 1;
                  if (isFirstCell && course) {
                    for (let i = hourIndex + 1; i < hours.length; i++) {
                      if (grid[dayIndex][i] === course) {
                        rowspan++;
                      } else {
                        break;
                      }
                    }
                  }

                  // Skip cells that are part of a previous rowspan
                  if (course && !isFirstCell) {
                    return null;
                  }

                  return (
                    <td
                      key={`${day}-${hour}`}
                      className={`border border-border p-2 ${
                        course ? courseColors.get(course.id) : "bg-background"
                      }`}
                      rowSpan={rowspan}
                    >
                      {isFirstCell && course && (
                        <div className="text-xs">
                          <div className="line-clamp-2 mb-1">{course.courseName}</div>
                          <div className="text-xs opacity-80">{course.professor}</div>
                          <div className="text-xs opacity-80">{course.room}</div>
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}