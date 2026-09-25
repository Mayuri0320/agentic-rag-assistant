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

export async function getCurrentUser(
  accessToken: string,
): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error('Authentication expired')
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
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      query,
      ...(conversationId !== undefined
        ? { conversation_id: conversationId }
        : {}),
      ...(documentId !== undefined ? { document_id: documentId } : {}),
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Chat request failed')
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

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? 'Document upload failed')
  }

  return response.json()
}