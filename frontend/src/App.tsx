import { useEffect, useRef, useState } from 'react'
import Auth from './components/Auth'
import CodingAssistant from './components/CodingAssistant'
import {
  getCurrentUser,
  uploadDocument,
  getDocuments,
  sendChatMessage,
  getConversations,
  getConversation,
} from './api/client'
import type {
  DocumentResponse,
  TokenResponse,
  User,
  Conversation,
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

  const [showCodingAssistant, setShowCodingAssistant] = useState(false)

  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isSending, setIsSending] = useState(false)

  const [activeConversation, setActiveConversation] =
    useState('New conversation')

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoadingConversations, setIsLoadingConversations] =
    useState(false)

  const [conversationId, setConversationId] =
    useState<number | undefined>(undefined)

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null)

  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [showDocuments, setShowDocuments] = useState(false)

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  /*
   * =========================
   * Authentication
   * =========================
   */

  useEffect(() => {
    const verifyAuthentication = async () => {
      if (!accessToken) {
        setAuthLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUser(accessToken)
        setUser(currentUser)
        setIsLoadingDocuments(true)

      try {
       const response = await getDocuments(accessToken)
       setDocuments(response.documents)
      } catch (error) {
       console.error('Failed to load documents:', error)
       setDocuments([])
      }finally {
  setIsLoadingDocuments(false)
}

        /*
         * Load the user's saved conversations.
         */
        setIsLoadingConversations(true)

        try {
          const response = await getConversations(accessToken)
          setConversations(response.conversations)
        } catch (error) {
          console.error(
            'Failed to load conversations:',
            error,
          )
          setConversations([])
        } finally {
          setIsLoadingConversations(false)
        }
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setAccessToken(null)
        setUser(null)
        setConversations([])
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
    setConversations([])
  }

  /*
   * =========================
   * New Conversation
   * =========================
   */

  const startNewConversation = () => {
    if (isSending) return

    setMessages([])
    setMessage('')
    setSelectedDocument(null)
    setConversationId(undefined)
    setActiveConversation('New conversation')
  }

  /*
   * =========================
   * Document Upload
   * =========================
   */

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

  /*
   * =========================
   * Load Existing Conversation
   * =========================
   */

  const loadConversation = async (id: number) => {
    if (!accessToken || isSending) return

    try {
      const response = await getConversation(
        accessToken,
        id,
      )

      setConversationId(response.conversation.id)
      setActiveConversation(response.conversation.title)

      setMessages(
        response.messages
          .filter(
            (item) =>
              item.role === 'user' ||
              item.role === 'assistant',
          )
          .map((item) => ({
            role: item.role as 'user' | 'assistant',
            content: item.content,
          })),
      )

      setSelectedDocument(null)
      setMessage('')
    } catch (error) {
      console.error(
        'Failed to load conversation:',
        error,
      )

      alert(
        error instanceof Error
          ? error.message
          : 'Failed to load conversation',
      )
    }
  }

  /*
   * =========================
   * Send Message
   * =========================
   */

  const sendMessage = async () => {
    const trimmed = message.trim()

    if (!trimmed || !accessToken || isSending) return

    const documentId = selectedDocument?.id

    /*
     * Remember whether this is a brand-new conversation.
     */
    const isNewConversation = conversationId === undefined

    /*
     * Show the user's message immediately.
     */
    setMessages((current) => [
      ...current,
      {
        role: 'user',
        content: trimmed,
      },
    ])

    setMessage('')
    setIsSending(true)

    try {
      const response = await sendChatMessage(
        accessToken,
        trimmed,
        conversationId,
        documentId,
      )

      /*
       * Save the conversation ID returned by backend.
       */
      if (response.conversation_id !== undefined) {
        setConversationId(response.conversation_id)
      }

      /*
       * Add AI response to chat.
       */
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
        },
      ])

      /*
       * If this was a new conversation, refresh the sidebar
       * so the newly created conversation appears immediately.
       */
      if (
        isNewConversation &&
        response.conversation_id !== undefined
      ) {
        try {
          const updatedConversations =
            await getConversations(accessToken)

          setConversations(
            updatedConversations.conversations,
          )

          const newConversation =
            updatedConversations.conversations.find(
              (conversation) =>
                conversation.id ===
                response.conversation_id,
            )

          if (newConversation) {
            setActiveConversation(
              newConversation.title,
            )
          }
        } catch (error) {
          console.error(
            'Failed to refresh conversations:',
            error,
          )
        }
      } else {
        /*
         * Existing conversation may have an updated title or
         * updated_at timestamp, so refresh the sidebar too.
         */
        try {
          const updatedConversations =
            await getConversations(accessToken)

          setConversations(
            updatedConversations.conversations,
          )
        } catch (error) {
          console.error(
            'Failed to refresh conversations:',
            error,
          )
        }
      }
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

  /*
   * =========================
   * Keyboard Handling
   * =========================
   */

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (
      event.key === 'Enter' &&
      !event.shiftKey
    ) {
      event.preventDefault()
      void sendMessage()
    }
  }

  /*
   * =========================
   * Loading Screen
   * =========================
   */

  if (authLoading) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-mark">✦</div>
        <p>Loading Agentic RAG...</p>
      </div>
    )
  }

  /*
   * =========================
   * Authentication Screen
   * =========================
   */

  if (!accessToken || !user) {
    return (
      <Auth
        onAuthenticated={handleAuthenticated}
      />
    )
  }

  /*
   * =========================
   * Main Application
   * =========================
   */

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

        {/* New conversation */}
        <button
          className="new-chat-button"
          onClick={startNewConversation}
          disabled={isSending}
        >
          <span>＋</span>
          New conversation
        </button>

        {/* Conversation list */}
        <div className="sidebar-section">
          <div className="section-label">
            CONVERSATIONS
          </div>

          <div className="conversation-list">
            {isLoadingConversations ? (
              <div className="conversation-empty">
                Loading conversations...
              </div>
            ) : conversations.length === 0 ? (
              <div className="conversation-empty">
                No saved conversations yet.
              </div>
            ) : (
              conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  className={`conversation-item ${
                    conversationId === conversation.id
                      ? 'active'
                      : ''
                  }`}
                  onClick={() =>
                    void loadConversation(
                      conversation.id,
                    )
                  }
                  disabled={isSending}
                  title={conversation.title}
                >
                  <span className="conversation-icon">
                    ◌
                  </span>

                  <span>
                    {conversation.title}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Sidebar bottom */}
        <div className="sidebar-bottom">
          <button 
          className="sidebar-link"
          onClick={() => setShowDocuments(true)}
          >
            <span>▣</span>
            Documents
          </button>
          <button
          className="sidebar-link"
          onClick={() => {
          setShowDocuments(false)
          setShowCodingAssistant(true)
          }}
          >
          <span>⌘</span>
          Coding Assistant
         </button>

          <button className="sidebar-link">
            <span>⚙</span>
            Settings
          </button>

          <div className="user-card">
            <div className="avatar">
              {user.email
                .charAt(0)
                .toUpperCase()}
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
            <button
              className="icon-button"
              title="Documents"
            >
              ▣
            </button>

            <button
              className="icon-button"
              title="Settings"
            >
              ⚙
            </button>
          </div>
        </header>

        <section
        className="chat-area"
        style={{ display: showCodingAssistant ? 'none' : undefined }}
        >
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">
                ✦
              </div>

              <h3>How can I help you?</h3>

              <p>
                Ask questions about your documents
                and let the agentic workflow find,
                verify, and generate the answer.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setMessage(
                      'What documents are available to me?',
                    )
                  }
                >
                  <strong>
                    Explore documents
                  </strong>

                  <span>
                    What documents are available to
                    me?
                  </span>
                </button>

                <button
                  onClick={() =>
                    setMessage(
                      'Summarise the key information in my documents.',
                    )
                  }
                >
                  <strong>
                    Summarise information
                  </strong>

                  <span>
                    Summarise the key information in
                    my documents.
                  </span>
                </button>

                <button
                  onClick={() =>
                    setMessage(
                      'Explain the main findings in my documents.',
                    )
                  }
                >
                  <strong>
                    Ask a question
                  </strong>

                  <span>
                    Explain the main findings in my
                    documents.
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
                      ? user.email
                          .charAt(0)
                          .toUpperCase()
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
                  <div className="message-avatar">
                    ✦
                  </div>

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

       
          {showCodingAssistant && (
            <CodingAssistant
              accessToken={accessToken}
              conversationId={conversationId}
              onConversationCreated={(id) => {
                setConversationId(id)
              }}
            />
          )}
           <div
            className="composer-wrapper"
            style={{ display: showCodingAssistant ? 'none' : undefined }}
            >
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

                  <span>
                    Document attached
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="selected-document-remove"
                onClick={() =>
                  setSelectedDocument(null)
                }
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
              onClick={() =>
                fileInputRef.current?.click()
              }
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
              disabled={
                !message.trim() || isSending
              }
              title="Send message"
              type="button"
            >
              {isSending ? '…' : '↑'}
            </button>
          </div>

          <div className="composer-footer">
            <span>
              Agentic RAG can make mistakes. Verify
              important information.
            </span>

            <span>
              Enter to send · Shift + Enter for new
              line
            </span>
          </div>
        </div>
        {showDocuments && (
          <section className="documents-panel">
            <div className="documents-panel-header">
              <div>
                <h2>My Documents</h2>
                <p>
                  Documents uploaded to your account
                </p>
              </div>

              <button
                type="button"
                className="documents-panel-close"
                onClick={() => setShowDocuments(false)}
              >
                Close
              </button>
            </div>

            {isLoadingDocuments ? (
              <p>Loading documents...</p>
            ) : documents.length === 0 ? (
              <p>No documents uploaded yet.</p>
            ) : (
              <div className="documents-list">
                {documents.map((document) => (
                  <div
                    className="document-item"
                    key={document.id}
                  >
                    <div>
                      <strong>{document.filename}</strong>

                      <span>
                        {document.file_type} ·{' '}
                        {document.status}
                      </span>
                    </div>

                    <span>
                      {document.file_size} bytes
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

      </main>
    </div>
  )
}

export default App