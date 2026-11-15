import { COPY, DEMO_SCENARIOS } from '../content/exploreCopy'

export interface DemoScenariosProps {
  scenario: string | null
  onChange(scenario: string | null): void
}

/** Solo existe con datos sintéticos: elige qué responde el servicio simulado para revisar cada estado. */
export function DemoScenarios({ scenario, onChange }: DemoScenariosProps) {
  return (
    <section className="explore-demo" aria-labelledby="explore-demo-title">
      <h2 id="explore-demo-title" className="explore-panel__title">
        {COPY.demo.title}
      </h2>
      <p className="explore-muted">{COPY.demo.note}</p>
      <div className="explore-field">
        <label htmlFor="explore-scenario">{COPY.demo.label}</label>
        <select
          id="explore-scenario"
          value={scenario ?? ''}
          onChange={(event) => onChange(event.target.value === '' ? null : event.target.value)}
        >
          <option value="">{COPY.demo.options['']}</option>
          {DEMO_SCENARIOS.map((id) => (
            <option key={id} value={id}>
              {COPY.demo.options[id]}
            </option>
          ))}
        </select>
      </div>
    </section>
  )
}
