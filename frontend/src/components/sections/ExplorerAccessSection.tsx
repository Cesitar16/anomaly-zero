import { SECTION_IDS } from '../../config/site'
import { EXPLORER } from '../../content/explorer'
import ExplorerCta from '../ui/ExplorerCta'
import Section from '../ui/Section'

export default function ExplorerAccessSection() {
  const { eyebrow, title, text, honesty } = EXPLORER.access

  return (
    <Section id={SECTION_IDS.access} eyebrow={eyebrow} title={title} intro={text} tone="deep">
      <div className="access__actions">
        <ExplorerCta variant="accent" />
        <p className="access__honesty">{honesty}</p>
      </div>
    </Section>
  )
}
