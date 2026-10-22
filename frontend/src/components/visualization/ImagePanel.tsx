import type { ReactNode } from 'react'

interface ImagePanelProps {
  src: string
  alt: string
  title?: string
  caption?: string
  children?: ReactNode
  className?: string
}

/**
 * An image display with an accessible caption.
 *
 * The component never rewrites or enhances the image: it renders exactly the
 * bytes served by the backend artefact endpoint.
 */
export function ImagePanel({ src, alt, title, caption, children, className = '' }: ImagePanelProps) {
  return (
    <figure className={className}>
      {title && <figcaption className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">{title}</figcaption>}
      <img src={src} alt={alt} className="mx-auto max-h-80 w-auto object-contain" loading="lazy" />
      {caption && <p className="mt-2 text-center text-xs text-slate-500">{caption}</p>}
      {children}
    </figure>
  )
}

export default ImagePanel
