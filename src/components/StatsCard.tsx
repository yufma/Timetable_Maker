import React from 'react'
import './StatsCard.css'

interface StatsCardProps {
  icon: string
  number: string
  label: string
}

const StatsCard: React.FC<StatsCardProps> = ({ icon, number, label }) => {
  return (
    <div className="stats-card">
      <div className="stats-icon">{icon}</div>
      <div className="stats-number">{number}</div>
      <div className="stats-label">{label}</div>
    </div>
  )
}

export default StatsCard

