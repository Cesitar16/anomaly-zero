import { SECTION_IDS } from '../../config/site'
import { PROBLEM } from '../../content/problem'
import ExternalLink from '../ui/ExternalLink'
import Section from '../ui/Section'

export default function ProblemSection() {
  const { eyebrow, title, intro, points, challengeNote } = PROBLEM

  return (
    <Section id={SECTION_IDS.problem} eyebrow={eyebrow} title={title} intro={intro} tone="paper">
      <ul className="grid">
        {points.map((point) => (
          <li key={point.title} className="card">
            <h3 className="card__title">{point.title}</h3>
            <p className="card__text">{point.text}</p>
          </li>
        ))}
      </ul>

      <div className="problem__callout">
        <h3 className="problem__callout-title">{challengeNote.title}</h3>
        <p>{challengeNote.text}</p>
        <p>
          <ExternalLink href={challengeNote.href}>{challengeNote.linkLabel}</ExternalLink>
        </p>
      </div>
    </Section>
  )
}
