import { useState, useRef, useEffect } from 'react'
import { X } from 'lucide-react'

interface Props {
  options: string[]
  value: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}

export default function TagInput({ options, value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState('')
  const [open, setOpen]   = useState(false)
  const containerRef      = useRef<HTMLDivElement>(null)

  const matches = query
    ? options.filter(o => o.toLowerCase().includes(query.toLowerCase()) && !value.includes(o))
    : []

  const add = (item: string) => {
    onChange([...value, item])
    setQuery('')
    setOpen(false)
  }

  const remove = (item: string) => onChange(value.filter(v => v !== item))

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div style={{ position: 'relative' }} ref={containerRef}>
      <div className="tag-input-wrap">
        <div className="tags-row">
          {value.map(v => (
            <span key={v} className="pill">
              {v}
              <span className="pill-x" onClick={() => remove(v)}><X size={11} /></span>
            </span>
          ))}
        </div>
        <input
          className="tag-bare-input"
          value={query}
          placeholder={value.length ? '' : placeholder}
          onChange={e => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => query && setOpen(true)}
        />
      </div>
      {open && matches.length > 0 && (
        <div className="dropdown-list">
          {matches.map(m => (
            <div key={m} className="dropdown-item" onMouseDown={() => add(m)}>
              {m}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
