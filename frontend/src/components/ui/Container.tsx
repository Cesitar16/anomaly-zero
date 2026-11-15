import type { ElementType, HTMLAttributes } from 'react'

interface ContainerProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType
}

/** Limita el ancho del contenido y centra. Única fuente del "ancho de página". */
export default function Container({
  as: Tag = 'div',
  className = '',
  children,
  ...rest
}: ContainerProps) {
  return (
    <Tag className={`container ${className}`.trim()} {...rest}>
      {children}
    </Tag>
  )
}
