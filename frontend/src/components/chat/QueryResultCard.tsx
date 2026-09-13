import { useState } from 'react'
import { Check, ChevronDown, Copy } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { QueryResultPayload } from '@/lib/query-results'

function displayValue(value: unknown): string {
  if (value === null) return 'NULL'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function QueryResultCard({ result }: { result: QueryResultPayload }) {
  const [showSql, setShowSql] = useState(false)
  const [copied, setCopied] = useState(false)

  async function copySql() {
    await navigator.clipboard.writeText(result.sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <section className="overflow-hidden rounded-xl border bg-card shadow-xs">
      <div className="flex items-center justify-between gap-3 border-b px-3 py-2">
        <div>
          <p className="text-xs font-medium">Query result</p>
          <p className="text-[0.7rem] text-muted-foreground">
            {result.rowCount} rows · {result.elapsedMs} ms
            {result.truncated ? ' · limited' : ''}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowSql((value) => !value)}
        >
          SQL
          <ChevronDown className={`size-3.5 transition-transform ${showSql ? 'rotate-180' : ''}`} />
        </Button>
      </div>

      {showSql ? (
        <div className="relative border-b bg-muted/40 p-3">
          <pre className="overflow-x-auto pr-8 font-mono text-xs whitespace-pre-wrap">
            {result.sql}
          </pre>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="absolute top-2 right-2"
            onClick={() => void copySql()}
            aria-label="Copy SQL"
          >
            {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
          </Button>
        </div>
      ) : null}

      <div className="max-h-96 overflow-auto">
        <table className="w-full min-w-max text-left text-xs">
          <thead className="sticky top-0 bg-muted">
            <tr>
              {result.columns.map((column) => (
                <th key={column} className="border-b px-3 py-2 font-medium">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="odd:bg-muted/20">
                {result.columns.map((column, columnIndex) => (
                  <td key={`${column}-${columnIndex}`} className="border-b px-3 py-2">
                    {displayValue(row[columnIndex])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {result.rows.length === 0 ? (
          <p className="p-4 text-center text-xs text-muted-foreground">No rows returned.</p>
        ) : null}
      </div>
    </section>
  )
}
