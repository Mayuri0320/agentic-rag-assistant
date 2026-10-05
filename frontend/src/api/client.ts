const API_BASE_URL = 'http://127.0.0.1:8000'

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type User = {
  id: number
  email: string
  is_active: boolean
}

/* =========================
   Authentication
   ========================= */

export async function register(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Registration failed')
  }

  return response.json()
}

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Login failed')
  }

  return response.json()
}

export async function refreshToken(
  refreshTokenValue: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshTokenValue,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Token refresh failed')
  }

  return response.json()
}

/* =========================
   Authenticated request helper
   ========================= */

async function authenticatedFetch(
  accessToken: string,
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(options.headers)

  headers.set('Authorization', `Bearer ${accessToken}`)

  let response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status !== 401) {
    return response
  }

  const storedRefreshToken = localStorage.getItem('refresh_token')

  if (!storedRefreshToken) {
    throw new Error('Authentication expired')
  }

  try {
    const tokens = await refreshToken(storedRefreshToken)

    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)

    const retryHeaders = new Headers(options.headers)

    retryHeaders.set(
      'Authorization',
      `Bearer ${tokens.access_token}`,
    )

    response = await fetch(url, {
      ...options,
      headers: retryHeaders,
    })

    return response
  } catch {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    throw new Error('Authentication expired')
  }
}

export async function getCurrentUser(
  accessToken: string,
): Promise<User> {
  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/auth/me`,
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Authentication expired')
  }

  return response.json()
}

/* =========================
   Chat
   ========================= */

export type ChatResponse = {
  query: string
  answer: string
  conversation_id?: number
}

export async function sendChatMessage(
  accessToken: string,
  query: string,
  conversationId?: number,
  documentId?: number,
): Promise<ChatResponse> {
  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        ...(conversationId !== undefined
          ? { conversation_id: conversationId }
          : {}),
        ...(documentId !== undefined ? { document_id: documentId } : {}),
      }),
    },
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Chat request failed')
  }

  return response.json()
}

/* =========================
   Conversations
   ========================= */

export type Conversation = {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export type ConversationMessage = {
  id: number
  role: string
  content: string
  created_at: string
}

export type ConversationListResponse = {
  conversations: Conversation[]
}

export type ConversationDetailResponse = {
  conversation: Conversation
  messages: ConversationMessage[]
}

export async function getConversations(
  accessToken: string,
): Promise<ConversationListResponse> {
  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/conversations`,
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      error?.detail ?? 'Failed to load conversations',
    )
  }

  return response.json()
}

export async function getConversation(
  accessToken: string,
  conversationId: number,
): Promise<ConversationDetailResponse> {
  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/conversations/${conversationId}`,
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      error?.detail ?? 'Failed to load conversation',
    )
  }

  return response.json()
}

/* =========================
   Documents
   ========================= */

export type DocumentResponse = {
  id: number
  filename: string
  file_type: string
  file_size: number
  storage_path: string
  status: string
  created_at: string
  updated_at: string
}

export type DocumentsResponse = {
  documents: DocumentResponse[]
}

export type IngestionResponse = {
  status: string
  chunk_count: number
  character_count: number
}

export type DocumentUploadResponse = {
  document: DocumentResponse
  ingestion: IngestionResponse
}

export async function uploadDocument(
  accessToken: string,
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/documents/upload`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    },
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Document upload failed')
  }

  return response.json()
}

export async function getDocuments(
  accessToken: string,
): Promise<DocumentsResponse> {
  const response = await authenticatedFetch(
    accessToken,
    `${API_BASE_URL}/documents`,
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)

    throw new Error(
      error?.detail ?? 'Failed to load documents',
    )
  }

  return response.json()
}