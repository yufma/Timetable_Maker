import React from 'react'
import ActionCard from './ActionCard'
import './ActionSection.css'

interface ActionSectionProps {
  wishlistCount: number
}

const ActionSection: React.FC<ActionSectionProps> = ({ wishlistCount }) => {
  const actions = [
    {
      icon: '📅',
      title: '시간표 추천',
      description: 'AI 기반으로 최적의 시간표를 자동으로 추천받으세요',
      buttonText: '시작하기',
      linkTo: '/schedule',
    },
    {
      icon: '🔍',
      title: '강의 검색',
      description: '모든 강의 정보와 강의계획서를 한눈에 확인하세요',
      buttonText: '검색하기',
      linkTo: '/search',
    },
    {
      icon: '❤️',
      title: '찜 목록',
      description: `관심있는 ${wishlistCount}개의 강의를 관리하세요`,
      buttonText: '보기',
      linkTo: '/wishlist',
    },
  ]

  return (
    <section className="action-section">
      {actions.map((action, index) => (
        <ActionCard
          key={index}
          icon={action.icon}
          title={action.title}
          description={action.description}
          buttonText={action.buttonText}
          linkTo={action.linkTo}
        />
      ))}
    </section>
  )
}

export default ActionSection

