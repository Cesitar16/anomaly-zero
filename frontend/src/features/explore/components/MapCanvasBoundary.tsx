import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { failed: boolean }

/** A fallo de MapLibre o de su chunk no debe ocultar la tabla ni la serie. */
export class MapCanvasBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // The visible fallback below is sufficient; errors are also available to the browser console.
  }

  render() {
    if (this.state.failed) {
      return <p className="explore-map__message" role="alert">El mapa no pudo iniciarse. La serie y la tabla siguen disponibles.</p>
    }
    return this.props.children
  }
}
