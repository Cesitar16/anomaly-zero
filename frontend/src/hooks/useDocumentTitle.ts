import { useEffect } from 'react'

/** Mantiene el <title> de la pestaña acorde a la página actual (útil para lectores de pantalla). */
export default function useDocumentTitle(title: string): void {
  useEffect(() => {
    document.title = title
  }, [title])
}
