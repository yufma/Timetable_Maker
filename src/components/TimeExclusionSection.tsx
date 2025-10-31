import React from 'react'
import './TimeExclusionSection.css'

interface TimeExclusionSectionProps {
  excludedTimes: Set<string>
  onExcludedTimesChange: (times: Set<string>) => void
}

const TimeExclusionSection: React.FC<TimeExclusionSectionProps> = ({
  excludedTimes,
  onExcludedTimesChange,
}) => {
  const days = ['월', '화', '수', '목', '금']
  const times = [
    '09:00',
    '10:00',
    '11:00',
    '12:00',
    '13:00',
    '14:00',
    '15:00',
    '16:00',
    '17:00',
  ]

  const toggleTime = (day: string, time: string) => {
    const key = `${day}-${time}`
    const newExcludedTimes = new Set(excludedTimes)
    
    if (newExcludedTimes.has(key)) {
      newExcludedTimes.delete(key)
    } else {
      newExcludedTimes.add(key)
    }
    
    onExcludedTimesChange(newExcludedTimes)
  }

  const isExcluded = (day: string, time: string) => {
    return excludedTimes.has(`${day}-${time}`)
  }

  return (
    <div className="time-exclusion-section">
      <h2 className="section-title">제외할 시간대</h2>
      <p className="section-subtitle">수업을 듣고 싶지 않은 시간을 선택하세요</p>
      
      <div className="time-table-container">
        <table className="time-table">
          <thead>
            <tr>
              <th className="time-header">시간</th>
              {days.map((day) => (
                <th key={day} className="day-header">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {times.map((time) => (
              <tr key={time}>
                <td className="time-cell">{time}</td>
                {days.map((day) => {
                  const excluded = isExcluded(day, time)
                  return (
                    <td key={`${day}-${time}`}>
                      <button
                        type="button"
                        className={`time-cell-button ${excluded ? 'excluded' : ''}`}
                        onClick={() => toggleTime(day, time)}
                        aria-label={`${day} ${time} ${excluded ? '제외 취소' : '제외'}`}
                      >
                        {excluded && <span className="excluded-mark">×</span>}
                      </button>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <p className="instruction-text">클릭하여 제외할 시간을 선택하세요</p>
    </div>
  )
}

export default TimeExclusionSection

