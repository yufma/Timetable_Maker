import React from 'react'
import './HowToSection.css'

const HowToSection: React.FC = () => {
  const steps = [
    {
      number: 1,
      title: '강의 검색',
      description: '관심있는 강의를 검색하고 강의계획서를 확인하세요',
    },
    {
      number: 2,
      title: '찜 목록 추가',
      description: '마음에 드는 강의를 찜 목록에 추가하세요',
    },
    {
      number: 3,
      title: '시간 설정',
      description: '선호하는 시간대와 제외할 시간대를 설정하세요',
    },
    {
      number: 4,
      title: '시간표 생성',
      description: 'AI가 추천하는 최적의 시간표를 확인하세요',
    },
  ]

  return (
    <section className="how-to-section">
      <h2 className="how-to-title">시간표 추천 시스템 사용법</h2>
      <div className="steps-container">
        {steps.map((step) => (
          <div key={step.number} className="step">
            <div className="step-number">{step.number}</div>
            <h3 className="step-title">{step.title}</h3>
            <p className="step-description">{step.description}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

export default HowToSection

