
import { useState } from 'react'
import {
  generatePythonSolution,
  downloadPythonSolution,
} from '../api/client'
import type { CodingResponse } from '../api/client'

export default function CodingAssistant() {
  const [file, setFile] = useState<File | null>(null)
  const [instruction, setInstruction] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [result, setResult] = useState<CodingResponse | null>(null)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!file || !instruction.trim()) {
      setError('Please select a Python file and enter your instructions.')
      return
    }

    setError('')
    setResult(null)
    setIsGenerating(true)

    try {
      const response = await generatePythonSolution(file, instruction)
      setResult(response)
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
    if (!result) return

    setError('')
    setIsDownloading(true)

    try {
      await downloadPythonSolution(result.filename)
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
        <h2>Python Coding Assistant</h2>
        <p>
          Upload your starter code, describe the task, and let Gemini
          generate a Python solution.
        </p>
      </div>

      <div className="coding-card">
        <label htmlFor="python-file">Starter Python file</label>
        <input
          id="python-file"
          type="file"
          accept=".py"
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
          Assignment instructions
        </label>
        <textarea
          id="coding-instruction"
          value={instruction}
          onChange={(event) => {
            setInstruction(event.target.value)
            setResult(null)
          }}
          placeholder="Explain what the program should do, the requirements, and any constraints..."
          rows={7}
        />

        <button
          type="button"
          className="coding-generate-button"
          onClick={handleGenerate}
          disabled={isGenerating || !file || !instruction.trim()}
        >
          {isGenerating ? 'Generating with Gemini...' : 'Generate Python Solution'}
        </button>

        {isGenerating && (
          <p className="coding-status">
            Gemini is working on your solution. This may take a little while.
          </p>
        )}

        {error && (
          <p className="coding-error" role="alert">
            {error}
          </p>
        )}

        {result && (
          <div className="coding-result">
            <h3>Solution generated successfully</h3>
            <p>{result.message}</p>
            <p>
              <strong>File:</strong> {result.filename}
            </p>
            <div className="coding-explanation">
  <h3>How the solution works</h3>
  <div className="coding-explanation-content">
    {result.explanation}
  </div>
</div>
            <button
              type="button"
              className="coding-download-button"
              onClick={handleDownload}
              disabled={isDownloading}
            >
              {isDownloading ? 'Downloading...' : 'Download Python File'}
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
