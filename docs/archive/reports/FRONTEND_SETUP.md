# ShopMind AI - React Frontend Setup

This guide covers setting up the React + TypeScript frontend for ShopMind AI.

## Prerequisites
- Node.js 16+ and npm
- VS Code or favorite editor

## Quick Start

### 1. Create React App with TypeScript
```bash
npx create-react-app shopmind-ui --template typescript
cd shopmind-ui
```

### 2. Install Dependencies
```bash
# UI & Styling
npm install -D tailwindcss postcss autoprefixer
npm install axios react-router-dom

# State Management
npm install zustand
npm install -D @types/react-router-dom

# UI Components (optional but recommended)
npm install @headlessui/react @heroicons/react

# Charting
npm install chart.js react-chartjs-2

# Forms & Validation
npm install react-hook-form zod

# API
npm install dotenv
```

### 3. Setup Tailwind CSS
```bash
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        amazon: {
          orange: '#FF9900',
          navy: '#131A22',
          blue: '#232F3E',
        }
      }
    },
  },
  plugins: [],
}
```

### 4. Project Structure
```
shopmind-ui/
├── public/
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── SearchBar.tsx
│   │   ├── ProductCard.tsx
│   │   ├── Navbar.tsx
│   │   └── Footer.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Search.tsx
│   │   ├── ProductDetail.tsx
│   │   ├── Recommendations.tsx
│   │   ├── AIAssistant.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Profile.tsx
│   │   └── Login.tsx
│   ├── services/
│   │   ├── api.ts (Axios instance)
│   │   ├── authService.ts
│   │   ├── productService.ts
│   │   └── copilotService.ts
│   ├── store/
│   │   ├── userStore.ts (Zustand store)
│   │   ├── cartStore.ts
│   │   └── searchStore.ts
│   ├── types/
│   │   └── index.ts (TypeScript interfaces)
│   ├── App.tsx
│   ├── App.css
│   └── index.tsx
├── .env
├── .env.example
├── package.json
└── tsconfig.json
```

### 5. Environment Variables
Create `.env`:
```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=ShopMind AI
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

### 6. Key Components

**SearchBar.tsx** - Main search interface
- Text input with autocomplete
- Search suggestions
- Filter options

**ProductCard.tsx** - Reusable product display
- Product image
- Name, price, rating
- "Add to cart", "Add to wishlist" buttons
- Quick view

**AIAssistant.tsx** - Copilot chat interface
- Chat message display
- Text input
- Product recommendations in chat
- Real-time streaming responses

**Dashboard.tsx** - User homepage
- Featured products
- Personalized recommendations
- Search trends
- Analytics

### 7. Styling with TailwindCSS

Example ProductCard component:
```tsx
export const ProductCard = ({ product }) => (
  <div className="bg-white rounded-lg shadow hover:shadow-lg transition p-4">
    <img src={product.image} className="w-full h-48 object-cover rounded" />
    <h3 className="mt-2 font-semibold text-amazon-navy">{product.name}</h3>
    <p className="text-amazon-orange font-bold text-lg">₹{product.price}</p>
    <div className="flex justify-between mt-4">
      <button className="bg-amazon-orange text-white px-4 py-2 rounded hover:bg-amber-600">
        Add to Cart
      </button>
    </div>
  </div>
);
```

### 8. API Integration

**api.ts**:
```typescript
import axios from 'axios';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add token to requests if logged in
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const endpoints = {
  search: (query: string, k: number = 5) => 
    apiClient.post('/search', { query, top_k: k }),
  recommend: (productId: string, k: number = 5) => 
    apiClient.post('/recommend', { product_id: productId, top_k: k }),
  analyzeReviews: (productId: string, reviews: string[]) => 
    apiClient.post('/analyze-reviews', { product_id: productId, reviews }),
  copilotAdvice: (query: string, k: number = 5) => 
    apiClient.post('/copilot-advice', { query, top_k: k }),
};
```

### 9. State Management with Zustand

**userStore.ts**:
```typescript
import { create } from 'zustand';

interface User {
  id: string;
  email: string;
  name: string;
}

interface UserStore {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user, token) => {
    localStorage.setItem('token', token);
    set({ user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, isAuthenticated: false });
  }
}));
```

### 10. Running the Frontend

```bash
npm start
```

The app will run on `http://localhost:3000`

## Pages Overview

### Home.tsx
- Hero section with search
- Featured products
- Popular categories
- Personalized recommendations

### Search.tsx
- Search results display
- Filters (price, rating, category)
- Sort options
- Pagination

### ProductDetail.tsx
- Product images (carousel)
- Specifications
- Price & availability
- Reviews & ratings
- Similar products
- "Add to Cart" / "Wishlist"

### Recommendations.tsx
- Personalized product recommendations
- "Because you viewed X"
- Popular in your categories
- Trending products

### AIAssistant.tsx
- Chat interface
- Send/receive messages
- Product cards in chat
- Comparison tables
- Shopping advice

### Dashboard.tsx
- User profile summary
- Recent searches
- Order history
- Wishlist
- Analytics (if admin)

## Authentication Flow

1. User clicks "Login" or "Sign Up"
2. Show modal with email/password or Google OAuth button
3. Call backend `/auth/login` or `/auth/register`
4. Store JWT token in localStorage
5. Set Authorization header for future requests
6. Redirect to dashboard

## Deployment

### Build for production
```bash
npm run build
```

### Deploy to Vercel (recommended)
```bash
npm i -g vercel
vercel
```

Or use AWS S3 + CloudFront (Phase 7)

## Key Features Implemented in Frontend

✅ Semantic search with results display
✅ Product detail pages with reviews
✅ Personalized recommendations engine
✅ AI shopping copilot chat
✅ User authentication (JWT + Google OAuth)
✅ Shopping cart and wishlist
✅ User profile and preferences
✅ Analytics dashboard
✅ Review sentiment display
✅ Responsive mobile-first design

## Next Steps

1. Implement each component following TypeScript best practices
2. Add form validation with Zod
3. Implement error boundaries and loading states
4. Add testing with Jest + React Testing Library
5. Performance optimization (code splitting, lazy loading)
6. Deploy to production

---

Ready for Phase 7: AWS Deployment + MLflow!
