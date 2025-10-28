import { GraduationCap, Calendar, Search, Heart, LogOut, Home } from "lucide-react";
import { Button } from "./ui/button";

interface NavigationProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  onLogout: () => void;
  userName: string;
}

export function Navigation({ currentPage, onNavigate, onLogout, userName }: NavigationProps) {
  const navItems = [
    { id: "home", label: "홈", icon: Home },
    { id: "search", label: "강의 검색", icon: Search },
    { id: "recommend", label: "시간표 추천", icon: Calendar },
    { id: "bookmarks", label: "찜 목록", icon: Heart },
  ];

  return (
    <nav className="bg-primary text-primary-foreground shadow-md">
      <div className="px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <GraduationCap size={32} />
            <span className="text-xl">시간표 추천 시스템</span>
          </div>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Button
                key={item.id}
                variant={currentPage === item.id ? "secondary" : "ghost"}
                className={currentPage === item.id ? "" : "text-primary-foreground hover:bg-primary-foreground/10"}
                onClick={() => onNavigate(item.id)}
              >
                <item.icon size={18} className="mr-2" />
                {item.label}
              </Button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="hidden sm:inline ml-2">{userName}님</span>
            <Button
              variant="ghost"
              className="text-primary-foreground hover:bg-primary-foreground/10"
              onClick={onLogout}
            >
              <LogOut size={18} className="mr-2" />
              로그아웃
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden flex gap-1 pb-2 overflow-x-auto">
          {navItems.map((item) => (
            <Button
              key={item.id}
              variant={currentPage === item.id ? "secondary" : "ghost"}
              size="sm"
              className={currentPage === item.id ? "" : "text-primary-foreground hover:bg-primary-foreground/10"}
              onClick={() => onNavigate(item.id)}
            >
              <item.icon size={16} className="mr-1" />
              {item.label}
            </Button>
          ))}
        </div>
      </div>
    </nav>
  );
}