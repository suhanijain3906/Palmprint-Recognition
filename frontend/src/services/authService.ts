import apiClient from './apiClient'
import type { AuthMode, LoginRequest, RegisterRequest, TokenResponse, UserInfo } from '../types'

/**
 * Authentication service.
 *
 * The access token is also returned in the JSON body for non-browser clients,
 * but the frontend relies on the HttpOnly `access_token` cookie set by the
 * backend. That keeps the token out of JavaScript and lets plain <img> and
 * download requests authenticate without extra headers.
 */
export const authService = {
  async mode(): Promise<AuthMode> {
    const { data } = await apiClient.get<AuthMode>('/auth/mode')
    return data
  },

  async login(payload: LoginRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload)
    return data
  },

  async register(payload: RegisterRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/register', payload)
    return data
  },

  async me(): Promise<UserInfo> {
    const { data } = await apiClient.get<UserInfo>('/auth/me')
    return data
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },
}

export default authService
