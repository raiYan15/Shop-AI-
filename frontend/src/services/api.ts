/**
 * ShopMind AI — Backend API Service Layer
 * All API calls go through /api (proxied by Vite → http://localhost:8000)
 */

const API_BASE = '/api';

const TOKEN_KEY = 'shopmind_token';
const REFRESH_TOKEN_KEY = 'shopmind_refresh_token';
const USER_KEY  = 'shopmind_user';

// Re-export Product type so legacy components can import from here
export type { Product } from '../data/mockData';

// ──────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────

export interface BackendProduct {
  product_id: string;
  product_name: string;
  category: string;
  price: string;
  rating: number;
  rating_count: string;
  similarity_score?: number;
  score?: number;
  reason?: string;
}

export interface SearchResponse {
  query: string;
  results: BackendProduct[];
  count: number;
}

export interface RecommendationResponse {
  query_product_id: string;
  recommendations: BackendProduct[];
  count: number;
  timestamp: string;
}

export interface HybridRecommendationItem extends LiveProduct {
  recommendation_score?: number;
  ai_match_label?: string;
  why_recommended?: string;
  live_price_indicator?: 'LIVE' | 'DATASET';
  is_new_arrival?: boolean;
  score_components?: {
    recommendation_score: number;
    semantic_similarity: number;
    user_interest_match: number;
    rating_score: number;
    popularity_score: number;
    price_affinity: number;
  };
}

export interface HybridRecommendationInsight {
  product_id: string;
  product_name: string;
  pros: string[];
  cons: string[];
  best_use_cases: string[];
  value_for_money_score: number;
  recommendation_confidence: number;
}

export interface HybridRecommendationBundle {
  user_id: string;
  country: string;
  weights: {
    fusion: { dataset: number; semantic: number; live: number };
    priority: { dataset: number; live: number };
  };
  summary: {
    products_analyzed: number;
    ai_accuracy: number;
    live_product_count: number;
    last_update_time: string;
    fallback_chain: string[];
    live_cache_source?: string;
    live_cache_updates?: number;
  };
  sections: {
    hybrid_recommendations: HybridRecommendationItem[];
    new_products: HybridRecommendationItem[];
    similar_products: HybridRecommendationItem[];
    trending_ai_students: HybridRecommendationItem[];
    ai_product_insights: HybridRecommendationInsight[];
  };
}

export interface ReviewSummary {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  overall_sentiment: string;
  key_strengths: string[];
  key_weaknesses: string[];
  average_confidence: number;
}

export interface ReviewIntelligenceResponse {
  product_id: string;
  analysis: { sentiment: string; confidence: number; text: string }[];
  summary: ReviewSummary;
  timestamp: string;
}

export interface CopilotResponse {
  query: string;
  advice: string;
  retrieved_products: BackendProduct[];
  confidence: number;
  timestamp: string;
}

export interface BackendStats {
  total_products: number;
  index_vectors: number;
  embedding_dimension: number;
  categories: number;
  avg_rating: number;
}

export interface HealthResponse {
  status: string;
  mongodb?: string;
  faiss_vectors?: number;
  models_loaded: boolean;
}

export interface LiveProduct {
  product_id: string;
  product_name: string;
  title?: string;
  description?: string;
  brand?: string;
  category: string;
  price: string;
  price_value?: number;
  original_price?: string;
  rating: number;
  rating_count?: string;
  stock?: number;
  thumbnail?: string;
  images?: string[];
  tags?: string[];
  ai_match?: number;
  similarity_score?: number;
  reason?: string;
}

export interface ProductsPageResponse {
  products: LiveProduct[];
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface LiveProductsResponse extends ProductsPageResponse {
  realtime?: boolean;
  server_time?: string;
  data_source?: string;
}

export interface TrendingResponse {
  trending_categories: { category: string; product_count: number; rank: number }[];
  products: LiveProduct[];
  count: number;
}

export interface AmazonCategoryProxyResponse {
  source: string;
  endpoint: string;
  country: string;
  fetched_at: string;
  data: unknown;
}

export interface NewArrivalsResponse {
  products: LiveProduct[];
  count: number;
}

export interface CompareResponse {
  product_a: LiveProduct;
  product_b: LiveProduct;
  summary: string;
  recommended_id: string;
  reasons: string[];
}

export interface ChatResponse {
  message: string;
  reply: string;
  products: LiveProduct[];
  confidence: number;
  timestamp?: string;
}

export interface DashboardProfile {
  name: string;
  first_name: string;
  last_name: string;
  email: string;
  profile_image?: string;
  role: string;
  membership_type: string;
  registered_at: string;
  last_login: string;
}

export interface DashboardPayload {
  profile: DashboardProfile;
  metrics: {
    total_saved: number;
    orders_count: number;
    ai_chats_count: number;
    wishlist_count: number;
    cart_count: number;
  };
  favorite_categories: { name: string; score: number }[];
  recent_searches: string[];
  cart: {
    count: number;
    items: Array<{
      product_id: string;
      name: string;
      price: number;
      quantity: number;
      thumbnail?: string;
    }>;
  };
  wishlist: {
    count: number;
    items: Array<{
      product_id: string;
      name: string;
      price: number;
      category?: string;
      thumbnail?: string;
      deal_savings?: number;
    }>;
  };
  history: {
    orders: Array<{
      order_id: string;
      created_at: string;
      total: number;
      items_count: number;
      status: string;
    }>;
  };
  analytics: {
    shopping_activity: Record<string, number>;
    search_trends: Array<{ day: number; count: number }>;
    ai_usage_last_30d: number;
    recommendation_accuracy: number;
    most_viewed_categories: { name: string; score: number }[];
    most_purchased_categories: { name: string; score: number }[];
  };
  settings: {
    theme_preference: string;
    notification_settings: Record<string, unknown>;
    shopping_preferences: Record<string, unknown>;
  };
}

// ──────────────────────────────────────────────────────────────
// HTTP Utilities
// ──────────────────────────────────────────────────────────────

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const isRefreshEndpoint = url.includes('/auth/refresh');
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (response.status === 401 && !isRefreshEndpoint) {
    const refreshed = await refreshAccessTokenInternal();
    if (refreshed) {
      const retry = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...authHeader(), ...options?.headers },
        ...options,
      });
      if (!retry.ok) {
        const retryDetail = await retry.text().catch(() => retry.statusText);
        throw new APIError(retry.status, retryDetail);
      }
      return retry.json() as Promise<T>;
    }
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new APIError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

// ──────────────────────────────────────────────────────────────
// Health Check
// ──────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<HealthResponse> {
  return fetchJSON<HealthResponse>(`${API_BASE}/health`);
}

export async function getStats(): Promise<BackendStats> {
  return fetchJSON<BackendStats>(`${API_BASE}/stats`);
}

export async function getProducts(
  page: number = 1,
  limit: number = 20,
  category?: string
): Promise<ProductsPageResponse> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (category) params.set('category', category);
  return fetchJSON<ProductsPageResponse>(`${API_BASE}/products?${params}`);
}

export async function getLiveProducts(
  page: number = 1,
  limit: number = 20,
  category?: string,
  sort: 'updated_at' | 'rating' | 'price' | 'title' = 'updated_at'
): Promise<LiveProductsResponse> {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    sort,
  });
  if (category) params.set('category', category);
  return fetchJSON<LiveProductsResponse>(`${API_BASE}/products/live?${params}`);
}

export interface LiveProductsStreamOptions {
  page?: number;
  limit?: number;
  category?: string;
  sort?: 'updated_at' | 'rating' | 'price' | 'title';
  interval?: number;
}

export function streamLiveProducts(
  onMessage: (payload: LiveProductsResponse) => void,
  onError?: (error: Event) => void,
  options: LiveProductsStreamOptions = {}
): () => void {
  const params = new URLSearchParams({
    page: String(options.page ?? 1),
    limit: String(options.limit ?? 20),
    sort: options.sort ?? 'updated_at',
    interval: String(options.interval ?? 5),
  });
  if (options.category) params.set('category', options.category);

  const url = `${API_BASE}/products/stream?${params.toString()}`;
  const source = new EventSource(url);

  const parseAndEmit = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as LiveProductsResponse;
      onMessage(data);
    } catch {
      // ignore malformed payloads
    }
  };

  source.addEventListener('update', parseAndEmit as EventListener);
  source.addEventListener('heartbeat', parseAndEmit as EventListener);
  if (onError) source.onerror = onError;

  return () => {
    source.removeEventListener('update', parseAndEmit as EventListener);
    source.removeEventListener('heartbeat', parseAndEmit as EventListener);
    source.close();
  };
}

export async function searchProducts(
  q: string,
  k: number = 10
): Promise<SearchResponse> {
  const encoded = encodeURIComponent(q);
  const data = await fetchJSON<{
    query: string;
    results: LiveProduct[];
    count: number;
  }>(`${API_BASE}/search?q=${encoded}&k=${k}`);
  return {
    query: data.query,
    results: data.results.map((p) => ({
      product_id: p.product_id,
      product_name: p.product_name || p.title || '',
      category: p.category,
      price: p.price,
      rating: p.rating,
      rating_count: p.rating_count || '0',
      similarity_score: p.similarity_score,
      score: p.ai_match,
      reason: p.reason,
    })),
    count: data.count,
  };
}

export async function getTrending(): Promise<TrendingResponse> {
  return fetchJSON<TrendingResponse>(`${API_BASE}/trending`);
}

export async function getNewArrivals(): Promise<NewArrivalsResponse> {
  return fetchJSON<NewArrivalsResponse>(`${API_BASE}/new-arrivals`);
}

export async function getAmazonProductCategoryList(
  country: string = 'US'
): Promise<AmazonCategoryProxyResponse> {
  return fetchJSON<AmazonCategoryProxyResponse>(
    `${API_BASE}/external/amazon/product-category-list?country=${encodeURIComponent(country)}`
  );
}

export async function compareProducts(
  productA: string,
  productB: string
): Promise<CompareResponse> {
  return fetchJSON<CompareResponse>(`${API_BASE}/compare`, {
    method: 'POST',
    body: JSON.stringify({ product_a: productA, product_b: productB }),
  });
}

export async function chatWithAI(message: string, topK: number = 5): Promise<ChatResponse> {
  return fetchJSON<ChatResponse>(`${API_BASE}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message, top_k: topK }),
  });
}

export async function triggerIngest(): Promise<Record<string, unknown>> {
  return fetchJSON(`${API_BASE}/ingest/trigger`, { method: 'POST' });
}

export async function getPipelineStatus(): Promise<Record<string, unknown>> {
  return fetchJSON(`${API_BASE}/pipeline/status`);
}

// ──────────────────────────────────────────────────────────────
// Semantic Search (legacy POST)
// ──────────────────────────────────────────────────────────────

export async function semanticSearch(
  query: string,
  topK: number = 8
): Promise<SearchResponse> {
  return fetchJSON<SearchResponse>(`${API_BASE}/search`, {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export async function quickSearch(
  query: string,
  k: number = 5
): Promise<SearchResponse> {
  const encoded = encodeURIComponent(query);
  return fetchJSON<SearchResponse>(`${API_BASE}/search-quick?q=${encoded}&k=${k}`);
}

// ──────────────────────────────────────────────────────────────
// Product Details
// ──────────────────────────────────────────────────────────────

export async function getProduct(productId: string) {
  return fetchJSON<{
    product_id: string;
    product_name: string;
    category: string;
    price: string;
    original_price: string;
    rating: number;
    rating_count: string;
    description: string;
  }>(`${API_BASE}/product/${productId}`);
}

// ──────────────────────────────────────────────────────────────
// Recommendations
// ──────────────────────────────────────────────────────────────

export async function getRecommendations(
  productId: string,
  topK: number = 5,
  userId?: string
): Promise<RecommendationResponse> {
  return fetchJSON<RecommendationResponse>(`${API_BASE}/recommend`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, top_k: topK, user_id: userId }),
  });
}

export async function getHybridRecommendations(
  userId: string,
  topK: number = 12,
  country: string = 'US'
): Promise<HybridRecommendationBundle> {
  return fetchJSON<HybridRecommendationBundle>(
    `${API_BASE}/recommendations/hybrid/${encodeURIComponent(userId)}?k=${topK}&country=${encodeURIComponent(country)}`
  );
}

// ──────────────────────────────────────────────────────────────
// Review Intelligence
// ──────────────────────────────────────────────────────────────

export async function analyzeReviews(
  productId: string,
  reviews: string[]
): Promise<ReviewIntelligenceResponse> {
  return fetchJSON<ReviewIntelligenceResponse>(`${API_BASE}/analyze-reviews`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, reviews }),
  });
}

// ──────────────────────────────────────────────────────────────
// AI Copilot / RAG
// ──────────────────────────────────────────────────────────────

export async function getCopilotAdvice(
  query: string,
  topK: number = 5,
  context?: Record<string, unknown>
): Promise<CopilotResponse> {
  return fetchJSON<CopilotResponse>(`${API_BASE}/copilot-advice`, {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK, context }),
  });
}

// ──────────────────────────────────────────────────────────────
// Auth Types & Helpers
// ──────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  created_at: string;
  is_active: boolean;
}

export interface AuthResponse {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function saveAuth(res: AuthResponse): void {
  localStorage.setItem(TOKEN_KEY, res.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(res.user));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function authHeader(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function refreshAccessTokenInternal(): Promise<boolean> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearAuth();
      return false;
    }

    const payload = (await response.json()) as AuthResponse;
    saveAuth(payload);
    return true;
  } catch {
    clearAuth();
    return false;
  }
}

export async function refreshSession(): Promise<AuthResponse> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    throw new APIError(401, 'No refresh token available');
  }
  const res = await fetchJSON<AuthResponse>(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  saveAuth(res);
  return res;
}

// ──────────────────────────────────────────────────────────────
// Auth Endpoints
// ──────────────────────────────────────────────────────────────

export async function signUp(data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}): Promise<AuthResponse> {
  return fetchJSON<AuthResponse>(`${API_BASE}/auth/signup`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function signIn(data: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  return fetchJSON<AuthResponse>(`${API_BASE}/auth/signin`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getCurrentUser(): Promise<AuthUser> {
  return fetchJSON<AuthUser>(`${API_BASE}/auth/me`, {
    headers: authHeader(),
  });
}

export async function signOut(): Promise<void> {
  const refreshToken = getStoredRefreshToken();
  if (refreshToken && getStoredToken()) {
    try {
      await fetchJSON(`${API_BASE}/auth/signout`, {
        method: 'POST',
        headers: authHeader(),
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // continue local logout even if remote revoke fails
    }
  }
  clearAuth();
}

export async function getDashboard(): Promise<DashboardPayload> {
  return fetchJSON<DashboardPayload>(`${API_BASE}/dashboard/me`, {
    headers: authHeader(),
  });
}

export async function updateProfile(data: {
  first_name?: string;
  last_name?: string;
  email?: string;
  profile_image?: string;
  membership_type?: string;
  theme_preference?: string;
  notification_settings?: Record<string, unknown>;
  shopping_preferences?: Record<string, unknown>;
}): Promise<{ user: AuthUser }> {
  return fetchJSON<{ user: AuthUser }>(`${API_BASE}/auth/profile`, {
    method: 'PUT',
    headers: authHeader(),
    body: JSON.stringify(data),
  });
}

export async function updatePassword(currentPassword: string, newPassword: string): Promise<{ ok: boolean }> {
  return fetchJSON<{ ok: boolean }>(`${API_BASE}/auth/change-password`, {
    method: 'POST',
    headers: authHeader(),
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

// ──────────────────────────────────────────────────────────────
// API Status Helper (for UI health indicator)
// ──────────────────────────────────────────────────────────────

export type BackendStatus = 'online' | 'loading' | 'offline';

export async function getBackendStatus(): Promise<{
  status: BackendStatus;
  modelsLoaded: boolean;
  stats?: BackendStats;
}> {
  try {
    const [health, stats] = await Promise.all([
      checkHealth(),
      getStats().catch(() => null),
    ]);
    return {
      status: health.status === 'healthy' ? 'online' : 'online',
      modelsLoaded: health.models_loaded,
      stats: stats ?? undefined,
    };
  } catch {
    return { status: 'offline', modelsLoaded: false };
  }
}
