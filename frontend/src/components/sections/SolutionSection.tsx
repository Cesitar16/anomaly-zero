import { SECTION_IDS } from '../../config/site'
import { SOLUTION } from '../../content/solution'
import Badge from '../ui/Badge'
import Section from '../ui/Section'

export default function SolutionSection() {
  const { eyebrow, title, intro, goals, statusHeading, statusIntro, statusItems } = SOLUTION

  return (
    <Section id={SECTION_IDS.solution} eyebrow={eyebrow} title={title} intro={intro} tone="surface">
      <ol className="goals">
        {goals.map((goal, index) => (
          <li key={goal.title} className="card">
            <span className="goal__label" aria-hidden="true">
              {String(index + 1).padStart(2, '0')}
            </span>
            <h3 className="card__title">{goal.title}</h3>
            <p className="card__text">{goal.text}</p>
          </li>
        ))}
      </ol>

      <div className="status-block">
        <h3>{statusHeading}</h3>
        <p className="status-block__intro">{statusIntro}</p>
        <ul className="status-list">
          {statusItems.map((item) => (
            <li key={item.title} className="status-item">
              <Badge status={item.status}>{item.statusLabel}</Badge>
              <div className="status-item__body">
                <p className="status-item__title">{item.title}</p>
                <p className="status-item__text">{item.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  )
}
