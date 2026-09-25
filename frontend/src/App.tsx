import { useEffect, useRef, useState } from 'react'
import Auth from './components/Auth'
import {
  getCurrentUser,
  uploadDocument,
  sendChatMessage,
} from './api/client'
import type {
  DocumentResponse,
  TokenResponse,
  User,
} from './api/client'
import './App.css'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

function App() {
  const [accessToken, setAccessToken] = useState<string | null>(
    () => localStorage.getItem('access_token'),
  )

  const [user, setUser] = useState<User | null>(null)
  const [authLoading, setAuthLoading] = useState(true)

  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isSending, setIsSending] = useState(false)

  const [activeConversation, setActiveConversation] =
    useState('New conversation')

  const [conversationId, setConversationId] =
    useState<number | undefined>(undefined)

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null)

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const conversations = [
    'New conversation',
    'Project documentation',
    'Research questions',
  ]

  useEffect(() => {
    const verifyAuthentication = async () => {
      if (!accessToken) {
        setAuthLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUser(accessToken)
        setUser(currentUser)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setAccessToken(null)
        setUser(null)
      } finally {
        setAuthLoading(false)
      }
    }

    void verifyAuthentication()
  }, [accessToken])

  const handleAuthenticated = (tokens: TokenResponse) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    setAccessToken(tokens.access_token)
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    setAccessToken(null)
    setUser(null)
    setMessages([])
    setMessage('')
    setSelectedDocument(null)
    setConversationId(undefined)
    setActiveConversation('New conversation')
  }

  const handleFileSelected = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0]

    if (!file || !accessToken) return

    try {
      const uploadedDocument = await uploadDocument(
        accessToken,
        file,
      )

      console.log('Document uploaded:', uploadedDocument)

      setSelectedDocument(uploadedDocument.document)

      alert(
        `Uploaded: ${uploadedDocument.document.filename}\n\n` +
          `Status: ${uploadedDocument.ingestion.status}\n` +
          `Chunks: ${uploadedDocument.ingestion.chunk_count}`,
      )
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : 'Document upload failed',
      )
    } finally {
      event.target.value = ''
    }
  }

  const sendMessage = async () => {
    const trimmed = message.trim()

    if (!trimmed || !accessToken || isSending) return

    const documentId = selectedDocument?.id

    // Show the user's message immediately
    setMessages((current) => [
      ...current,
      {
        role: 'user',
        content: trimmed,
      },
    ])

    // Clear the input
    setMessage('')

    // Start loading state
    setIsSending(true)

    try {
      const response = await sendChatMessage(
        accessToken,
        trimmed,
        conversationId,
        documentId,
      )

      // Save conversation ID returned by backend
      if (response.conversation_id !== undefined) {
        setConversationId(response.conversation_id)
      }

      // Add AI response to chat
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
        },
      ])
    } catch (error) {
      console.error('Chat request failed:', error)

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            error instanceof Error
              ? `Sorry, I couldn't answer that: ${error.message}`
              : 'Sorry, something went wrong while processing your question.',
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void sendMessage()
    }
  }

  if (authLoading) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-mark">✦</div>
        <p>Loading Agentic RAG...</p>
      </div>
    )
  }

  if (!accessToken || !user) {
    return <Auth onAuthenticated={handleAuthenticated} />
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">✦</div>

          <div>
            <h1>Agentic RAG</h1>
            <span>AI Assistant</span>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={() => {
            setMessages([])
            setMessage('')
            setSelectedDocument(null)
            setConversationId(undefined)
            setActiveConversation('New conversation')
          }}
        >
          <span>＋</span>
          New conversation
        </button>

        <div className="sidebar-section">
          <div className="section-label">CONVERSATIONS</div>

          <div className="conversation-list">
            {conversations.map((conversation) => (
              <button
                key={conversation}
                className={`conversation-item ${
                  activeConversation === conversation
                    ? 'active'
                    : ''
                }`}
                onClick={() => {
                  setActiveConversation(conversation)

                  if (conversation === 'New conversation') {
                    setMessages([])
                    setMessage('')
                    setSelectedDocument(null)
                    setConversationId(undefined)
                  }
                }}
              >
                <span className="conversation-icon">◌</span>
                <span>{conversation}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-bottom">
          <button className="sidebar-link">
            <span>▣</span>
            Documents
          </button>

          <button className="sidebar-link">
            <span>⚙</span>
            Settings
          </button>

          <div className="user-card">
            <div className="avatar">
              {user.email.charAt(0).toUpperCase()}
            </div>

            <div className="user-info">
              <strong>{user.email}</strong>
              <span>Authenticated user</span>
            </div>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
              title="Sign out"
            >
              ↪
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h2>{activeConversation}</h2>

            <span className="status">
              <span className="status-dot"></span>
              Agentic RAG ready
            </span>
          </div>

          <div className="topbar-actions">
            <button className="icon-button" title="Documents">
              ▣
            </button>

            <button className="icon-button" title="Settings">
              ⚙
            </button>
          </div>
        </header>

        <section className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">✦</div>

              <h3>How can I help you?</h3>

              <p>
                Ask questions about your documents and let the
                agentic workflow find, verify, and generate the
                answer.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setMessage(
                      'What documents are available to me?',
                    )
                  }
                >
                  <strong>Explore documents</strong>

                  <span>
                    What documents are available to me?
                  </span>
                </button>

                <button
                  onClick={() =>
                    setMessage(
                      'Summarise the key information in my documents.',
                    )
                  }
                >
                  <strong>Summarise information</strong>

                  <span>
                    Summarise the key information in my
                    documents.
                  </span>
                </button>

                <button
                  onClick={() =>
                    setMessage(
                      'Explain the main findings in my documents.',
                    )
                  }
                >
                  <strong>Ask a question</strong>

                  <span>
                    Explain the main findings in my documents.
                  </span>
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((item, index) => (
                <div
                  className={`message-row ${item.role}`}
                  key={`${item.role}-${index}`}
                >
                  <div className="message-avatar">
                    {item.role === 'user'
                      ? user.email.charAt(0).toUpperCase()
                      : '✦'}
                  </div>

                  <div className="message-content">
                    <span className="message-role">
                      {item.role === 'user'
                        ? 'You'
                        : 'Agentic RAG'}
                    </span>

                    <p>{item.content}</p>
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="message-row assistant">
                  <div className="message-avatar">✦</div>

                  <div className="message-content">
                    <span className="message-role">
                      Agentic RAG
                    </span>

                    <p>Thinking...</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <div className="composer-wrapper">
          {selectedDocument && (
            <div className="selected-document">
              <div className="selected-document-info">
                <span className="selected-document-icon">
                  📄
                </span>

                <div>
                  <strong>
                    {selectedDocument.filename}
                  </strong>

                  <span>Document attached</span>
                </div>
              </div>

              <button
                type="button"
                className="selected-document-remove"
                onClick={() => setSelectedDocument(null)}
                title="Remove document"
              >
                ×
              </button>
            </div>
          )}

          <div className="composer">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              style={{ display: 'none' }}
              onChange={handleFileSelected}
            />

            <button
              className="attach-button"
              title="Attach document"
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isSending}
            >
              ＋
            </button>

            <textarea
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your documents..."
              rows={1}
              disabled={isSending}
            />

            <button
              className="send-button"
              onClick={() => void sendMessage()}
              disabled={!message.trim() || isSending}
              title="Send message"
              type="button"
            >
              {isSending ? '…' : '↑'}
            </button>
          </div>

          <div className="composer-footer">
            <span>
              Agentic RAG can make mistakes. Verify important
              information.
            </span>

            <span>
              Enter to send · Shift + Enter for new line
            </span>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App