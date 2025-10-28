import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Calendar, Search, Heart, BookOpen, TrendingUp, Clock } from "lucide-react";

interface HomePageProps {
  onNavigate: (page: string) => void;
  bookmarkedCount: number;
}

export function HomePage({ onNavigate, bookmarkedCount }: HomePageProps) {
  const features = [
    {
      icon: Calendar,
      title: "시간표 추천",
      description: "AI 기반으로 최적의 시간표를 자동으로 추천받으세요",
      action: () => onNavigate("recommend"),
      buttonText: "시작하기",
    },
    {
      icon: Search,
      title: "강의 검색",
      description: "모든 강의 정보와 강의계획서를 한눈에 확인하세요",
      action: () => onNavigate("search"),
      buttonText: "검색하기",
    },
    {
      icon: Heart,
      title: "찜 목록",
      description: `관심있는 ${bookmarkedCount}개의 강의를 관리하세요`,
      action: () => onNavigate("bookmarks"),
      buttonText: "보기",
    },
  ];

  const quickStats = [
    { icon: BookOpen, label: "전체 강의 수", value: "240+" },
    { icon: TrendingUp, label: "평균 만족도", value: "4.5/5" },
    { icon: Clock, label: "시간 절약", value: "80%" },
  ];

  return (
    <div className="mx-auto px-6 lg:px-10 py-10 lg:py-14 w-full">
      {/* Hero / Intro */}
      <div className="mb-10 lg:mb-14 grid lg:grid-cols-2 gap-6 lg:gap-10 items-center">
        <div>
          <h1 className="mb-3 text-3xl lg:text-4xl font-medium tracking-tight">환영합니다!</h1>
          <p className="text-muted-foreground text-base lg:text-lg">
            똑똑한 시간표 추천으로 학기를 시작하세요
          </p>
        </div>
        <div className="flex lg:justify-end gap-3">
          <Button onClick={() => onNavigate("recommend")}>추천 시작</Button>
          <Button variant="outline" onClick={() => onNavigate("search")}>강의 검색</Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid sm:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6 mb-10 lg:mb-14">
        {quickStats.map((stat, index) => (
          <Card key={index} className="h-full">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <stat.icon className="text-primary" size={24} />
              </div>
              <div>
                <div className="text-2xl lg:text-3xl leading-none">{stat.value}</div>
                <div className="text-muted-foreground text-sm lg:text-base">{stat.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Features */}
      <div className="grid md:grid-cols-3 gap-6 lg:gap-7 mb-10 lg:mb-14">
        {features.map((feature, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow h-full flex flex-col">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="text-primary" size={24} />
              </div>
              <CardTitle className="text-lg lg:text-xl">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 flex flex-col flex-1">
              <p className="text-muted-foreground text-sm lg:text-base">{feature.description}</p>
              <div className="pt-1 mt-auto">
                <Button onClick={feature.action} className="w-full">
                  {feature.buttonText}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* How it works */}
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="text-xl lg:text-2xl">시간표 추천 시스템 사용법</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-4 gap-4 lg:gap-6">
            <div className="space-y-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground">1</div>
              <h4 className="text-base lg:text-lg">강의 검색</h4>
              <p className="text-sm text-muted-foreground">관심있는 강의를 검색하고 강의계획서를 확인하세요</p>
            </div>
            <div className="space-y-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground">2</div>
              <h4 className="text-base lg:text-lg">찜 목록 추가</h4>
              <p className="text-sm text-muted-foreground">마음에 드는 강의를 찜 목록에 추가하세요</p>
            </div>
            <div className="space-y-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground">3</div>
              <h4 className="text-base lg:text-lg">시간 설정</h4>
              <p className="text-sm text-muted-foreground">선호하는 시간대와 제외할 시간대를 설정하세요</p>
            </div>
            <div className="space-y-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground">4</div>
              <h4 className="text-base lg:text-lg">시간표 생성</h4>
              <p className="text-sm text-muted-foreground">AI가 추천하는 최적의 시간표를 확인하세요</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}