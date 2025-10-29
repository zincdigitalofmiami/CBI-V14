# CBI-V14 Next.js Dashboard

Professional TradingView-style dashboard for soybean oil futures forecasting with Vertex AI AutoML integration.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:3000
```

## 📦 Installed Packages

### **Core Framework**
- **Next.js 15** - Latest stable version with App Router
- **React 18** - Latest React with concurrent features
- **TypeScript** - Full type safety

### **Styling & UI**
- **Tailwind CSS 3.4** - TradingView-inspired color scheme
- **Tailwind Typography** - Rich text styling
- **Class Variance Authority** - Component variants
- **Framer Motion** - Smooth animations

### **Charts & Graphics (TradingView Style)**
- **Lightweight Charts** - TradingView's own charting library
- **React Financial Charts** - Professional financial charting
- **@visx/visx** - Low-level visualization primitives
- **D3.js** - Data visualization toolkit
- **Recharts** - React-specific charts
- **Victory** - Data visualization components
- **Plotly.js** - Scientific plotting library
- **TradingView Charting Library** - Full TradingView integration

### **Icons & Graphics**
- **Lucide React** - Modern icon library
- **Heroicons** - Tailwind-designed icons

### **State Management & Data**
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **Axios** - HTTP client
- **React Hook Form** - Form management
- **Zod** - Schema validation

### **UI Components**
- **Radix UI** - Headless accessible components:
  - Dropdown Menu
  - Dialog/Modal
  - Tooltip
  - Select
  - Tabs
  - Slider
  - Switch

### **Development**
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Type checking

## 🎨 Design Features

### **TradingView-Inspired Theme**
- **Dark Mode**: Professional trading interface
- **Color Scheme**: 
  - Background: `#0D1421` (primary), `#131722` (secondary)
  - Bull/Bear: Green (#22c55e) / Red (#ef4444)
  - Charts: Authentic TradingView colors

### **Typography**
- **Font**: TradingView-style system fonts
- **Sizing**: Consistent scale (2xs to 4xl)
- **Weight**: Light to bold for hierarchy

### **Components**
- **Forecast Cards**: Professional gauges with confidence metrics
- **Live Price Widget**: Real-time price display
- **Chart Integration**: Full TradingView charts
- **Responsive**: Mobile-first design

## 🔧 Configuration

### **API Integration**
Edit `next.config.js` to point to your backend:

```javascript
env: {
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
}
```

### **Environment Variables**
Create `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
# Add your backend URL here
```

## 📁 Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Homepage/Dashboard
│   ├── globals.css     # Global styles
│   └── providers.tsx   # React Query provider
├── components/
│   ├── layout/         # Layout components
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   ├── dashboard/      # Dashboard components
│   │   ├── ForecastCards.tsx
│   │   └── MarketOverview.tsx
│   ├── charts/         # Chart components
│   │   └── TradingViewChart.tsx
│   └── widgets/        # Widget components
│       └── LivePriceWidget.tsx
```

## 🎯 Key Features

### **Professional Dashboard**
- ✅ TradingView-style dark theme
- ✅ Real-time price updates
- ✅ Forecast cards with confidence metrics
- ✅ Full TradingView chart integration
- ✅ Responsive design

### **Data Integration Ready**
- ✅ React Query for API calls
- ✅ Automatic refetching
- ✅ Loading states
- ✅ Error handling
- ✅ Caching

### **Chart Capabilities**
- ✅ TradingView Advanced Charts
- ✅ Multiple chart libraries available
- ✅ Custom financial visualizations
- ✅ Interactive components

## 🔄 API Integration

Replace mock data in components with real API calls:

```typescript
// Example: Update ForecastCards.tsx
async function fetchForecasts(): Promise<ForecastData[]> {
  const response = await fetch('/api/v3/forecast/all')
  return response.json()
}
```

## 🎨 Customization

### **Colors**
Edit `tailwind.config.js` to customize the color scheme:

```javascript
colors: {
  background: {
    primary: '#0D1421',      // Your primary color
    secondary: '#131722',    // Your secondary color
  },
  bull: { 500: '#22c55e' },  // Your bull color
  bear: { 500: '#ef4444' },  // Your bear color
}
```

### **Components**
All components use Tailwind classes and are fully customizable.

## 🚀 Production Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## ✨ Why This Setup?

### **Advantages Over Vite**
- ✅ **Rock Solid**: Next.js is production-proven
- ✅ **Zero Conflicts**: Single UI approach (no competing frameworks)
- ✅ **Perfect TradingView Integration**: Optimized for financial widgets
- ✅ **Built-in Optimization**: Automatic performance optimizations
- ✅ **Easy Deployment**: Vercel, Netlify, or any platform

### **Chart Library Coverage**
- **TradingView**: Full integration with professional charts
- **Lightweight Charts**: TradingView's own lightweight library
- **Financial Charts**: Specialized financial visualizations
- **D3/Visx**: Custom visualizations
- **Plotly**: Scientific/statistical plots

This setup gives you **EVERYTHING** needed for a professional trading dashboard with TradingView-quality charts and graphics.
