import ExplorerAccessSection from '../components/sections/ExplorerAccessSection'
import Hero from '../components/sections/Hero'
import HowItWorksSection from '../components/sections/HowItWorksSection'
import ProblemSection from '../components/sections/ProblemSection'
import SolutionSection from '../components/sections/SolutionSection'
import SourcesSection from '../components/sections/SourcesSection'
import TeamSection from '../components/sections/TeamSection'
import { SITE } from '../config/site'
import useDocumentTitle from '../hooks/useDocumentTitle'

/** Página de inicio: solo compone secciones. La lógica y el contenido viven en cada una. */
export default function LandingPage() {
  useDocumentTitle(`${SITE.name} | Explora tendencias ambientales`)

  return (
    <>
      <Hero />
      <ProblemSection />
      <SolutionSection />
      <HowItWorksSection />
      <TeamSection />
      <SourcesSection />
      <ExplorerAccessSection />
    </>
  )
}
