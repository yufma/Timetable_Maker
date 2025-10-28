import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { GraduationCap } from "lucide-react";

interface LoginPageProps {
  onLogin: (studentId: string, password: string) => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (studentId && password) {
      onLogin(studentId, password);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
              <GraduationCap className="text-primary-foreground" size={32} />
            </div>
          </div>
          <CardTitle className="text-2xl">시간표 추천 시스템</CardTitle>
          <p className="text-muted-foreground">학번과 비밀번호로 로그인하세요</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="studentId">학번</label>
              <Input
                id="studentId"
                type="text"
                placeholder="20231234"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password">비밀번호</label>
              <Input
                id="password"
                type="password"
                placeholder="비밀번호를 입력하세요"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full">
              로그인
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              데모용: 아무 학번/비밀번호나 입력하세요
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}