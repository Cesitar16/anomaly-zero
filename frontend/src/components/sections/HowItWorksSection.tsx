import { SECTION_IDS } from '../../config/site'
import { HOW_IT_WORKS } from '../../content/howItWorks'
import Badge from '../ui/Badge'
import Section from '../ui/Section'

export default function HowItWorksSection() {
  const { eyebrow, title, intro, steps, variablesHeading, variablesIntro, variables, scopeNote } =
    HOW_IT_WORKS

  return (
    <Section id={SECTION_IDS.how} eyebrow={eyebrow} title={title} intro={intro} tone="deep">
      <ol className="steps">
        {steps.map((step) => (
          <li key={step.title} className="step">
            <span className="step__number" aria-hidden="true" />
            <h3 className="step__title">{step.title}</h3>
            <p className="step__text">{step.text}</p>
          </li>
        ))}
      </ol>

      <div className="variables">
        <h3>{variablesHeading}</h3>
        <p className="variables__intro">{variablesIntro}</p>
        <ul className="grid">
          {variables.map((variable) => (
            <li key={variable.name} className="card">
              <Badge status="candidate">Candidata</Badge>
              <h4 className="card__title">{variable.name}</h4>
              <p className="variable__detail">{variable.detail}</p>
              <p className="variable__product">Producto candidato: {variable.product}</p>
            </li>
          ))}
        </ul>
        <p className="scope-note">{scopeNote}</p>
      </div>
    </Section>
  )
}
