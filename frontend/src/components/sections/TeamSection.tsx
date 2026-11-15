import { SECTION_IDS } from '../../config/site'
import { TEAM } from '../../content/team'
import { getInitials } from '../../utils/getInitials'
import ExternalLink from '../ui/ExternalLink'
import Section from '../ui/Section'

export default function TeamSection() {
  const { eyebrow, title, intro, members, privacyNote, teamPage, event } = TEAM

  return (
    <Section id={SECTION_IDS.team} eyebrow={eyebrow} title={title} intro={intro} tone="paper">
      <ul className="grid">
        {members.map((member) => (
          <li key={member.name} className="card member">
            <span className="member__avatar" aria-hidden="true">
              {getInitials(member.name)}
            </span>
            <h3>{member.name}</h3>
            <p className="member__role">{member.role}</p>
            <p className="card__text">{member.focus}</p>
          </li>
        ))}
      </ul>

      <div className="team__footer">
        <p>
          {event.text} <ExternalLink href={event.link.href}>{event.link.label}</ExternalLink>
        </p>
        <p>
          <ExternalLink href={teamPage.href}>{teamPage.label}</ExternalLink>
        </p>
        <p>{privacyNote}</p>
      </div>
    </Section>
  )
}
