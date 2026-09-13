import { isDataUIPart, type UIMessage } from 'ai'

export type QueryResultPayload = {
  queryId: string
  sql: string
  columns: string[]
  rows: unknown[][]
  rowCount: number
  truncated: boolean
  elapsedMs: number
}

export type PipelineStage =
  | 'analyzing'
  | 'searching'
  | 'reading'
  | 'querying'
  | 'verifying'
  | 'retrying'
  | 'streaming'

export type PipelineStatus = {
  stage: PipelineStage
  message: string
}

function isQueryResultData(data: unknown): data is QueryResultPayload {
  if (typeof data !== 'object' || data === null) return false
  const record = data as Record<string, unknown>
  return (
    typeof record.queryId === 'string' &&
    typeof record.sql === 'string' &&
    Array.isArray(record.columns) &&
    Array.isArray(record.rows) &&
    typeof record.rowCount === 'number' &&
    typeof record.truncated === 'boolean' &&
    typeof record.elapsedMs === 'number'
  )
}

export function isQueryResultPart(
  part: UIMessage['parts'][number],
): part is UIMessage['parts'][number] & {
  type: 'data-query-result'
  data: QueryResultPayload
} {
  return (
    isDataUIPart(part) &&
    part.type === 'data-query-result' &&
    isQueryResultData(part.data)
  )
}

export function isStatusPart(
  part: unknown,
): part is { type: 'data-status'; data: PipelineStatus } {
  if (typeof part !== 'object' || part === null) return false
  const record = part as Record<string, unknown>
  if (
    record.type !== 'data-status' ||
    typeof record.data !== 'object' ||
    record.data === null
  ) {
    return false
  }
  const data = record.data as Record<string, unknown>
  return typeof data.stage === 'string' && typeof data.message === 'string'
}

export function queryResultFromMessage(
  message: UIMessage,
): QueryResultPayload | undefined {
  return message.parts.find(isQueryResultPart)?.data
}

export function textFromMessage(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('')
}
