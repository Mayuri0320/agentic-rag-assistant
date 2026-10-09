import { useState } from 'react'
import {
  generateCodeSolution,
  downloadCodeSolution,
} from '../api/client'
import type { CodingResponse } from '../api/client'

type CodingAssistantProps = {
  accessToken: string
  conversationId?: number
  onConversationCreated: (id: number) => void
}

export default function CodingAssistant({
  accessToken,
  conversationId,
  onConversationCreated,
}: CodingAssistantProps) {
  const [file, setFile] = useState<File | null>(null)
  const [instruction, setInstruction] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [result, setResult] = useState<CodingResponse | null>(null)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!file || !instruction.trim()) {
      setError(
        'Please select a source-code file and enter your instructions.',
      )
      return
    }

    setError('')
    setResult(null)
    setIsGenerating(true)

    try {
      const response = await generateCodeSolution(
        accessToken,
        file,
        instruction,
        conversationId,
      )

      setResult(response)

      if (response.conversation_id !== undefined) {
        onConversationCreated(response.conversation_id)
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Code generation failed. Please try again.',
      )
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleDownload() {
    if (!result) {
      return
    }

    setError('')
    setIsDownloading(true)

    try {
      await downloadCodeSolution(result.filename)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Download failed. Please try again.',
      )
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <section className="coding-assistant">
      <div className="coding-header">
        <h2>Coding Assistant</h2>

        <p>
          Upload your source code, describe what you want to
          change, fix, improve, or convert, and Gemini will
          generate the complete result.
        </p>
      </div>

      <div className="coding-card">
        <label htmlFor="source-code-file">
          Source code file
        </label>

        <input
          id="source-code-file"
          type="file"
          accept=".py,.java,.js,.jsx,.ts,.tsx,.cpp,.cc,.cxx,.c,.h,.hpp,.cs,.go,.rs,.php,.rb,.swift,.kt,.kts,.scala,.sql,.sh,.bash"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null)
            setResult(null)
            setError('')
          }}
        />

        {file && (
          <p className="coding-file-name">
            Selected: {file.name}
          </p>
        )}

        <label htmlFor="coding-instruction">
          Instructions
        </label>

        <textarea
          id="coding-instruction"
          value={instruction}
          onChange={(event) => {
            setInstruction(event.target.value)
            setResult(null)
            setError('')
          }}
          placeholder="For example: Convert this Python code to Java, fix the bug, improve the implementation, or explain and complete the code..."
          rows={7}
        />

        <button
          type="button"
          className="coding-generate-button"
          onClick={() => void handleGenerate()}
          disabled={
            isGenerating ||
            !file ||
            !instruction.trim()
          }
        >
          {isGenerating
            ? 'Generating with Gemini...'
            : 'Generate Code'}
        </button>

        {isGenerating && (
          <p className="coding-status">
            Gemini is working on your code. This may take a
            little while.
          </p>
        )}

        {error && (
          <p className="coding-error" role="alert">
            {error}
          </p>
        )}

        {result && (
          <div className="coding-result">
            <h3>Code generated successfully</h3>

            <p>{result.message}</p>

            <p>
              <strong>Generated language:</strong>{' '}
              {result.language}
            </p>

            <p>
              <strong>Generated file:</strong>{' '}
              {result.filename}
            </p>

            <div className="coding-solution">
              <h3>Generated Code</h3>

              <pre className="coding-code">
                <code>{result.solution_code}</code>
              </pre>
            </div>

            <div className="coding-explanation">
              <h3>Explanation</h3>

              <div className="coding-explanation-content">
                {result.explanation}
              </div>
            </div>

            <button
              type="button"
              className="coding-download-button"
              onClick={() => void handleDownload()}
              disabled={isDownloading}
            >
              {isDownloading
                ? 'Downloading...'
                : 'Download Generated File'}
            </button>
          </div>
        )}
      </div>
    </section>
  )
}