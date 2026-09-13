import type { UIMessage } from 'ai'

import { AssistantMessage } from '@/components/chat/AssistantMessage'
import { textFromMessage } from '@/lib/query-results'

type MessageBubbleProps = {
  message: UIMessage
  isStreaming?: boolean
}

export function MessageBubble({
  message,
  isStreaming,
}: MessageBubbleProps) {
  if (message.role === 'assistant') {
    return (
      <AssistantMessage
        message={message}
        isStreaming={isStreaming}
      />
    )
  }

  const text = textFromMessage(message)

  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-md bg-secondary px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-secondary-foreground">
        {text}
      </div>
    </div>
  )
}
