import React from 'react'
import StatsCard from './StatsCard'
import './StatsSection.css'

const StatsSection: React.FC = () => {
  const stats = [
    { icon: '📖', number: '240+', label: '전체 강의 수' },
    { icon: '📊', number: '4.5/5', label: '평균 만족도' },
    { icon: '⏰', number: '80%', label: '시간 절약' },
  ]

  return (
    <section className="stats-section">
      {stats.map((stat, index) => (
        <StatsCard
          key={index}
          icon={stat.icon}
          number={stat.number}
          label={stat.label}
        />
      ))}
    </section>
  )
}

export default StatsSection

