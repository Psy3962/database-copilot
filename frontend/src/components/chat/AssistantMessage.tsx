import { useState } from 'react'
import type { UIMessage } from 'ai'
import { Check, Copy } from 'lucide-react'

import { AssistantMarkdown } from '@/components/chat/AssistantMarkdown'
import { QueryResultCard } from '@/components/chat/QueryResultCard'
import { Button } from '@/components/ui/button'
import {
  queryResultFromMessage,
  textFromMessage,
} from '@/lib/query-results'

type AssistantMessageProps = {
  message: UIMessage
  isStreaming?: boolean
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      className="text-muted-foreground"
      onClick={() => void handleCopy()}
      aria-label="Copy answer"
    >
      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
    </Button>
  )
}

export function AssistantMessage({
  message,
  isStreaming = false,
}: AssistantMessageProps) {
  const text = textFromMessage(message)
  const queryResult = queryResultFromMessage(message)

  return (
    <div className="min-w-0 space-y-3">
      {text ? (
        <AssistantMarkdown text={text} />
      ) : null}

      {isStreaming && text ? (
        <span className="inline-block h-4 w-2 translate-y-0.5 animate-pulse rounded-sm bg-foreground" />
      ) : null}

      {queryResult ? <QueryResultCard result={queryResult} /> : null}

      {!isStreaming && text ? (
        <div className="flex items-center gap-1 pt-0.5">
          <CopyButton text={text} />
        </div>
      ) : null}
    </div>
  )
}
