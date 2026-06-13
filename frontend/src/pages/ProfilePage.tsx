import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  User, Heart, ShoppingCart, Search, Clock, Settings,
  Star, TrendingUp, Package, ChevronRight, Edit3, LogOut, RefreshCw,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Footer } from '../components/layout/Footer';
import {
  getAmazonProductCategoryList,
  getDashboard,
  signOut,
  updatePassword,
  updateProfile,
  type DashboardPayload,
} from '../services/api';
import { useStore } from '../store/useStore';

type TabId = 'overview' | 'wishlist' | 'history' | 'preferences';

type WishlistItem = {
  product_id: string;
  name: string;
  price: number;
  category?: string;
  thumbnail?: string;
  deal_savings?: number;
};

type HistoryOrder = {
  order_id: string;
  created_at: string;
  total: number;
  items_count: number;
  status: string;
};

const TABS: Array<{ id: TabId; label: string; icon: React.ElementType }> = [
  { id: 'overview', label: 'Overview', icon: User },
  { id: 'wishlist', label: 'Wishlist', icon: Heart },
  { id: 'history', label: 'History', icon: Clock },
  { id: 'preferences', label: 'Preferences', icon: Settings },
];

const emptyDashboard: DashboardPayload = {
  profile: {
    name: 'User',
    first_name: '',
    last_name: '',
    email: '',
    profile_image: '',
    role: 'user',
    membership_type: 'standard',
    registered_at: new Date().toISOString(),
    last_login: new Date().toISOString(),
  },
  metrics: {
    total_saved: 0,
    orders_count: 0,
    ai_chats_count: 0,
    wishlist_count: 0,
    cart_count: 0,
  },
  favorite_categories: [],
  recent_searches: [],
  cart: { count: 0, items: [] },
  wishlist: { count: 0, items: [] },
  history: { orders: [] },
  analytics: {
    shopping_activity: {},
    search_trends: [],
    ai_usage_last_30d: 0,
    recommendation_accuracy: 0,
    most_viewed_categories: [],
    most_purchased_categories: [],
  },
  settings: {
    theme_preference: 'dark',
    notification_settings: {},
    shopping_preferences: {},
  },
};

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setCurrentUser } = useStore();

  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [country, setCountry] = useState('US');
  const [categories, setCategories] = useState<string[]>([]);
  const [categoryLoading, setCategoryLoading] = useState(false);
  const [categoryMessage, setCategoryMessage] = useState('');
  const [categoryFetchedAt, setCategoryFetchedAt] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [settingsStatus, setSettingsStatus] = useState('');

  const [settingsForm, setSettingsForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    profile_image: '',
    membership_type: 'standard',
    theme_preference: 'dark',
    notifications_price_drop: true,
    notifications_ai: true,
    notifications_email_newsletters: false,
    shopping_budget_range: '',
    current_password: '',
    new_password: '',
  });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard-me'],
    queryFn: getDashboard,
    refetchInterval: 8000,
    staleTime: 4000,
  });

  const dashboard = data ?? emptyDashboard;

  useEffect(() => {
    if (!data) return;
    setSettingsForm((prev) => ({
      ...prev,
      first_name: data.profile.first_name,
      last_name: data.profile.last_name,
      email: data.profile.email,
      profile_image: data.profile.profile_image || '',
      membership_type: data.profile.membership_type || 'standard',
      theme_preference: data.settings.theme_preference || 'dark',
      notifications_price_drop: Boolean(data.settings.notification_settings?.price_drop_alerts ?? true),
      notifications_ai: Boolean(data.settings.notification_settings?.ai_recommendations ?? true),
      notifications_email_newsletters: Boolean(data.settings.notification_settings?.email_newsletters ?? false),
      shopping_budget_range: String(data.settings.shopping_preferences?.budget_range || ''),
      current_password: '',
      new_password: '',
    }));
  }, [data]);

  const displayInitial = useMemo(() => {
    const name = dashboard.profile.name?.trim();
    if (name) return name.charAt(0).toUpperCase();
    return 'U';
  }, [dashboard.profile.name]);

  const extractCategoryNames = (payload: unknown): string[] => {
    const names: string[] = [];
    const walk = (node: unknown) => {
      if (!node) return;
      if (Array.isArray(node)) return node.forEach(walk);
      if (typeof node !== 'object') return;
      const obj = node as Record<string, unknown>;
      ['category_name', 'name', 'display_name', 'title'].forEach((k) => {
        const v = obj[k];
        if (typeof v === 'string') {
          const clean = v.trim();
          if (clean.length > 1 && clean.length < 80) names.push(clean);
        }
      });
      Object.values(obj).forEach(walk);
    };
    walk(payload);
    return [...new Set(names)].slice(0, 30);
  };

  const loadCategories = async () => {
    setCategoryLoading(true);
    setCategoryMessage('');
    try {
      const res = await getAmazonProductCategoryList(country);
      setCategories(extractCategoryNames(res.data));
      setCategoryFetchedAt(res.fetched_at);
      setCategoryMessage((res as { message?: string }).message || '');
    } catch {
      setCategories([]);
      setCategoryMessage('Live data temporarily unavailable. Displaying cached categories.');
    } finally {
      setCategoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'overview') {
      loadCategories();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, country]);

  const signOutMutation = useMutation({
    mutationFn: signOut,
    onSuccess: () => {
      setCurrentUser(null);
      queryClient.clear();
      navigate('/signin');
    },
  });

  const saveSettingsMutation = useMutation({
    mutationFn: async () => {
      await updateProfile({
        first_name: settingsForm.first_name,
        last_name: settingsForm.last_name,
        email: settingsForm.email,
        profile_image: settingsForm.profile_image,
        membership_type: settingsForm.membership_type,
        theme_preference: settingsForm.theme_preference,
        notification_settings: {
          price_drop_alerts: settingsForm.notifications_price_drop,
          ai_recommendations: settingsForm.notifications_ai,
          email_newsletters: settingsForm.notifications_email_newsletters,
        },
        shopping_preferences: {
          budget_range: settingsForm.shopping_budget_range,
        },
      });
      if (settingsForm.current_password && settingsForm.new_password) {
        await updatePassword(settingsForm.current_password, settingsForm.new_password);
      }
    },
    onSuccess: async () => {
      setSettingsStatus('Settings updated successfully.');
      await queryClient.invalidateQueries({ queryKey: ['dashboard-me'] });
      await queryClient.invalidateQueries({ queryKey: ['navbar-dashboard-summary'] });
      setSettingsForm((prev) => ({ ...prev, current_password: '', new_password: '' }));
    },
    onError: () => {
      setSettingsStatus('Unable to update settings right now. Please retry.');
    },
  });

  const favorites = dashboard.favorite_categories;
  const searches = dashboard.recent_searches;
  const wishlistItems = dashboard.wishlist.items as WishlistItem[];
  const historyOrders = dashboard.history.orders as HistoryOrder[];

  if (isLoading) {
    return (
      <div className="page-wrapper" style={{ display: 'grid', placeItems: 'center', minHeight: '80vh' }}>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Loading dashboard...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="page-wrapper" style={{ display: 'grid', placeItems: 'center', minHeight: '80vh', gap: 12 }}>
        <div style={{ fontSize: 13, color: '#EF4444' }}>Unable to load your dashboard.</div>
        <button className="btn-primary" onClick={() => refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div style={{ background: 'linear-gradient(180deg, #0D1117 0%, var(--bg-primary) 100%)', paddingBottom: 72 }}>
        <div className="container" style={{ paddingTop: 48 }}>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative' }}>
              {dashboard.profile.profile_image ? (
                <img src={dashboard.profile.profile_image} alt={dashboard.profile.name} style={{ width: 84, height: 84, borderRadius: 2, objectFit: 'cover' }} />
              ) : (
                <div style={{ width: 84, height: 84, borderRadius: 2, background: '#FF9900', color: '#0D1117', display: 'grid', placeItems: 'center', fontWeight: 800, fontSize: 32 }}>{displayInitial}</div>
              )}
              <button onClick={() => setShowSettings((v) => !v)} style={{ position: 'absolute', bottom: -4, right: -4, width: 26, height: 26, borderRadius: 2, border: '1px solid #d5d9d9', background: 'white' }}>
                <Edit3 size={11} color="#0D1117" />
              </button>
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                <h1 style={{ margin: 0, fontSize: 26, color: 'white' }}>{dashboard.profile.name}</h1>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 2, background: '#FF9900', color: '#0D1117' }}>{dashboard.profile.membership_type.toUpperCase()}</span>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 2, border: '1px solid rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.9)' }}>{dashboard.profile.role.toUpperCase()}</span>
              </div>
              <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 13, margin: 0 }}>{dashboard.profile.email}</p>
              <p style={{ color: 'rgba(255,255,255,0.25)', fontSize: 12, margin: '3px 0 0' }}>Member since {new Date(dashboard.profile.registered_at).toLocaleDateString()}</p>
              <p style={{ color: 'rgba(255,255,255,0.25)', fontSize: 12, margin: '3px 0 0' }}>Last login {new Date(dashboard.profile.last_login).toLocaleString()}</p>
            </div>

            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button className="btn-ghost" onClick={() => setShowSettings((v) => !v)} style={{ borderRadius: 2 }}><Settings size={13} /> Settings</button>
              <button className="btn-ghost" onClick={() => signOutMutation.mutate()} style={{ borderRadius: 2, color: '#EF4444' }}><LogOut size={13} /> Sign Out</button>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }} style={{ display: 'flex', gap: 10, marginTop: 28, flexWrap: 'wrap' }}>
            {[
              { label: 'Total Saved', value: `₹${dashboard.metrics.total_saved.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, icon: TrendingUp, color: '#10B981' },
              { label: 'Orders Placed', value: dashboard.metrics.orders_count, icon: Package, color: '#6366F1' },
              { label: 'AI Chats', value: dashboard.metrics.ai_chats_count, icon: Star, color: '#FF9900' },
              { label: 'Wishlist Items', value: dashboard.metrics.wishlist_count, icon: Heart, color: '#EF4444' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', borderLeft: `3px solid ${color}`, borderRadius: 2, padding: '12px 16px' }}>
                <div style={{ width: 32, height: 32, borderRadius: 2, background: `${color}18`, display: 'grid', placeItems: 'center' }}><Icon size={14} color={color} /></div>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'white' }}>{value}</div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase' }}>{label}</div>
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>

      <div className="container" style={{ marginTop: -36, paddingBottom: 80 }}>
        <div style={{ display: 'flex', gap: 0, marginBottom: 20, background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 2, overflow: 'hidden', width: 'fit-content' }}>
          {TABS.map(({ id, label, icon: Icon }, i) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '10px 18px', borderRadius: 0, border: 'none',
                borderRight: i < TABS.length - 1 ? '1px solid var(--border-color)' : 'none',
                borderBottom: activeTab === id ? '2px solid #FF9900' : '2px solid transparent',
                cursor: 'pointer', background: activeTab === id ? 'rgba(255,153,0,0.08)' : 'transparent',
                color: activeTab === id ? '#FF9900' : 'var(--text-secondary)', fontWeight: 700, fontSize: 12,
              }}
            >
              <Icon size={13} /> {label}
            </button>
          ))}
        </div>

        {showSettings && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderTop: '2px solid #FF9900', borderRadius: 2, padding: 16, marginBottom: 20 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 14, textTransform: 'uppercase' }}>User Settings</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
              <input className="auth-input" placeholder="First name" value={settingsForm.first_name} onChange={(e) => setSettingsForm((p) => ({ ...p, first_name: e.target.value }))} />
              <input className="auth-input" placeholder="Last name" value={settingsForm.last_name} onChange={(e) => setSettingsForm((p) => ({ ...p, last_name: e.target.value }))} />
              <input className="auth-input" placeholder="Email" value={settingsForm.email} onChange={(e) => setSettingsForm((p) => ({ ...p, email: e.target.value }))} />
              <input className="auth-input" placeholder="Profile image URL" value={settingsForm.profile_image} onChange={(e) => setSettingsForm((p) => ({ ...p, profile_image: e.target.value }))} />
              <input className="auth-input" placeholder="Membership type" value={settingsForm.membership_type} onChange={(e) => setSettingsForm((p) => ({ ...p, membership_type: e.target.value }))} />
              <input className="auth-input" placeholder="Theme preference" value={settingsForm.theme_preference} onChange={(e) => setSettingsForm((p) => ({ ...p, theme_preference: e.target.value }))} />
              <input className="auth-input" placeholder="Shopping budget range" value={settingsForm.shopping_budget_range} onChange={(e) => setSettingsForm((p) => ({ ...p, shopping_budget_range: e.target.value }))} />
              <input className="auth-input" type="password" placeholder="Current password" value={settingsForm.current_password} onChange={(e) => setSettingsForm((p) => ({ ...p, current_password: e.target.value }))} />
              <input className="auth-input" type="password" placeholder="New password" value={settingsForm.new_password} onChange={(e) => setSettingsForm((p) => ({ ...p, new_password: e.target.value }))} />
            </div>
            <div style={{ marginTop: 10, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <label style={{ fontSize: 12 }}><input type="checkbox" checked={settingsForm.notifications_price_drop} onChange={(e) => setSettingsForm((p) => ({ ...p, notifications_price_drop: e.target.checked }))} /> Price drop alerts</label>
              <label style={{ fontSize: 12 }}><input type="checkbox" checked={settingsForm.notifications_ai} onChange={(e) => setSettingsForm((p) => ({ ...p, notifications_ai: e.target.checked }))} /> AI recommendations</label>
              <label style={{ fontSize: 12 }}><input type="checkbox" checked={settingsForm.notifications_email_newsletters} onChange={(e) => setSettingsForm((p) => ({ ...p, notifications_email_newsletters: e.target.checked }))} /> Email newsletters</label>
            </div>
            <div style={{ marginTop: 10, display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn-primary" onClick={() => saveSettingsMutation.mutate()} disabled={saveSettingsMutation.isPending}>{saveSettingsMutation.isPending ? 'Saving...' : 'Save Settings'}</button>
              {settingsStatus && <span style={{ fontSize: 12, color: settingsStatus.includes('successfully') ? '#10B981' : '#EF4444' }}>{settingsStatus}</span>}
            </div>
          </div>
        )}

        {activeTab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderTop: '2px solid #FF9900', borderRadius: 2, padding: '22px' }}>
              <h3 style={{ fontSize: 14, marginBottom: 14, textTransform: 'uppercase' }}>Favorite Categories</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(favorites.length ? favorites : [{ name: 'No activity yet', score: 0 }]).map((cat, i) => {
                  const pct = Math.max(5, Math.min(100, Math.round((cat.score || 0) * 10) || (80 - i * 10)));
                  return (
                    <div key={`${cat.name}-${i}`}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 12 }}>{cat.name}</span>
                        <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{pct}%</span>
                      </div>
                      <div style={{ height: 3, background: 'rgba(255,153,0,0.1)' }}>
                        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ delay: i * 0.08, duration: 0.6 }} style={{ height: 3, background: '#FF9900' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderTop: '2px solid #6366F1', borderRadius: 2, padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <h3 style={{ fontSize: 14, margin: 0, textTransform: 'uppercase' }}>Recent Searches</h3>
                <Link to="/products" style={{ fontSize: 11, color: '#FF9900', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 2 }}>
                  Search <ChevronRight size={11} />
                </Link>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(searches.length ? searches : ['No searches yet']).map((search, i) => (
                  <div key={`${search}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', borderRadius: 2, background: 'rgba(255,153,0,0.03)', border: '1px solid rgba(255,153,0,0.07)' }}>
                    <Search size={11} color="#FF9900" />
                    <span style={{ fontSize: 12 }}>{search}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderTop: '2px solid #10B981', borderRadius: 2, padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <h3 style={{ fontSize: 14, margin: 0, textTransform: 'uppercase' }}>Cart ({dashboard.cart.count})</h3>
                {dashboard.cart.count > 0 && <button className="btn-primary" style={{ padding: '5px 14px', fontSize: 11 }}>Checkout</button>}
              </div>
              {dashboard.cart.count === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <ShoppingCart size={32} style={{ opacity: 0.2, margin: '0 auto 10px' }} />
                  <p style={{ fontSize: 13 }}>Your cart is empty</p>
                  <Link to="/products" style={{ color: '#FF9900', fontSize: 12, textDecoration: 'none' }}>Start Shopping →</Link>
                </div>
              ) : (
                dashboard.cart.items.map((item) => (
                  <div key={`${item.product_id}-${item.quantity}`} style={{ display: 'flex', gap: 8, marginBottom: 8, padding: '7px', borderRadius: 2, border: '1px solid var(--border-color)' }}>
                    {item.thumbnail ? <img src={item.thumbnail} alt={item.name} style={{ width: 40, height: 40, borderRadius: 2, objectFit: 'cover' }} /> : <div style={{ width: 40, height: 40, background: 'rgba(255,153,0,0.1)' }} />}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</div>
                      <div style={{ fontSize: 12, color: '#FF9900', fontWeight: 700 }}>₹{item.price.toLocaleString('en-IN')} × {item.quantity}</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderTop: '2px solid #FF9900', borderRadius: 2, padding: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 10, flexWrap: 'wrap' }}>
                <h3 style={{ fontSize: 14, margin: 0, textTransform: 'uppercase' }}>Live Amazon Categories</h3>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <select value={country} onChange={(e) => setCountry(e.target.value)} style={{ padding: '6px 10px', borderRadius: 2, border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 12 }}>
                    <option value="US">US</option>
                    <option value="IN">IN</option>
                    <option value="GB">GB</option>
                    <option value="DE">DE</option>
                    <option value="JP">JP</option>
                  </select>
                  <button onClick={loadCategories} disabled={categoryLoading} style={{ width: 30, height: 30, borderRadius: 2, border: '1px solid var(--border-color)', background: 'transparent' }}>
                    <RefreshCw size={13} style={{ animation: categoryLoading ? 'spin 1s linear infinite' : 'none' }} />
                  </button>
                </div>
              </div>

              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 12 }}>
                Source: RapidAPI via backend proxy
                {categoryFetchedAt ? ` • ${new Date(categoryFetchedAt).toLocaleTimeString()}` : ''}
              </p>

              {categoryMessage ? (
                <div style={{ border: '1px solid rgba(255,153,0,0.25)', background: 'rgba(255,153,0,0.08)', borderRadius: 2, padding: '10px 12px', fontSize: 12, color: '#FF9900', marginBottom: 8 }}>{categoryMessage}</div>
              ) : null}

              {categoryLoading ? (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Loading categories...</div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 8 }}>
                  {(categories.length ? categories : ['No categories available']).map((cat) => (
                    <div key={cat} style={{ padding: '7px 9px', borderRadius: 2, border: '1px solid rgba(255,153,0,0.15)', background: 'rgba(255,153,0,0.05)', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={cat}>{cat}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'wishlist' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {dashboard.wishlist.count === 0 ? (
              <div style={{ textAlign: 'center', padding: '72px 0' }}>
                <Heart size={44} style={{ opacity: 0.15, marginBottom: 14, display: 'block', margin: '0 auto 14px' }} />
                <h3 style={{ fontSize: 20, marginBottom: 6 }}>No saved products yet</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: 14 }}>Click wishlist on products to save them here</p>
                <Link to="/products" className="btn-primary">Browse Products</Link>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
                {wishlistItems.map((item) => (
                  <div key={`${item.product_id}-${item.name}`} style={{ border: '1px solid var(--border-color)', borderRadius: 2, padding: 10, background: 'var(--bg-card)' }}>
                    <div style={{ fontSize: 13, fontWeight: 700 }}>{item.name}</div>
                    <div style={{ fontSize: 12, color: '#FF9900', marginTop: 4 }}>₹{item.price.toLocaleString('en-IN')}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>{item.category || 'General'}</div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'history' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Order History</h2>
            {historyOrders.length === 0 ? (
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>No order history found.</div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {historyOrders.map((order) => (
                  <div key={order.order_id} style={{ border: '1px solid var(--border-color)', borderRadius: 2, padding: 12, background: 'var(--bg-card)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                      <div style={{ fontSize: 12 }}>Order: {order.order_id}</div>
                      <div style={{ fontSize: 12, color: '#10B981' }}>{order.status.toUpperCase()}</div>
                    </div>
                    <div style={{ fontSize: 12, marginTop: 6 }}>Items: {order.items_count} • Total: ₹{order.total.toLocaleString('en-IN')}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>{new Date(order.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'preferences' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16 }}>
              {[
                { label: 'AI Recommendations', description: 'Personalized product suggestions based on your browsing', enabled: settingsForm.notifications_ai },
                { label: 'Price Drop Alerts', description: 'Get notified when wishlist items go on sale', enabled: settingsForm.notifications_price_drop },
                { label: 'Email Newsletters', description: 'Weekly AI-curated deals and new arrivals', enabled: settingsForm.notifications_email_newsletters },
                { label: 'AI Usage', description: `AI chats this period: ${dashboard.metrics.ai_chats_count}`, enabled: true },
                { label: 'Theme Preference', description: `Current theme: ${settingsForm.theme_preference}`, enabled: true },
              ].map(({ label, description, enabled }) => (
                <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderLeft: `3px solid ${enabled ? '#FF9900' : 'var(--border-color)'}`, borderRadius: 2, padding: '18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1, paddingRight: 14 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 3, textTransform: 'uppercase' }}>{label}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{description}</div>
                    </div>
                    <div style={{ width: 40, height: 22, borderRadius: 2, background: enabled ? '#FF9900' : 'rgba(255,255,255,0.08)', border: `1px solid ${enabled ? '#FF9900' : 'var(--border-color)'}`, position: 'relative' }}>
                      <div style={{ position: 'absolute', top: 2, left: enabled ? 20 : 2, width: 16, height: 16, borderRadius: 1, background: 'white', transition: 'left 0.15s' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
      <Footer />
    </div>
  );
};

export default ProfilePage;
