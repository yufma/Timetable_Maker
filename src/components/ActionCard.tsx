import React from 'react'
import { Link } from 'react-router-dom'
import './ActionCard.css'

interface ActionCardProps {
  icon: string
  title: string
  description: string
  buttonText: string
  linkTo?: string
}

const ActionCard: React.FC<ActionCardProps> = ({
  icon,
  title,
  description,
  buttonText,
  linkTo = '#',
}) => {
  return (
    <div className="action-card">
      <div className="action-icon">{icon}</div>
      <h2 className="action-title">{title}</h2>
      <p className="action-description">{description}</p>
      <Link to={linkTo} className="action-button">
        {buttonText}
      </Link>
    </div>
  )
}

export default ActionCard

