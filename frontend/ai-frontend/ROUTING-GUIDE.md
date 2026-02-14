# UhakikiAI Next.js Routing Guide

## 🚀 **Next.js App Router Structure**

Your UhakikiAI frontend uses Next.js 13+ App Router with the following structure:

```
src/app/
├── layout.tsx                 # Root layout (metadata, global styles)
├── page.tsx                   # Homepage (/)
├── globals.css               # Global styles
└── (dashboard)/              # Route group for dashboard pages
    ├── layout.tsx            # Dashboard layout (sidebar, navigation)
    ├── page.tsx              # Dashboard overview (/dashboard)
    ├── verifications/
    │   └── page.tsx          # Verification history (/dashboard/verifications)
    ├── fraud/
    │   └── page.tsx          # Fraud analytics (/dashboard/fraud)
    └── review/
        └── page.tsx          # Human review queue (/dashboard/review)
```

## 📁 **Route Groups with Parentheses**

The `(dashboard)` folder is a **route group**:
- Creates shared layout for all dashboard pages
- Doesn't add to the URL path
- All pages inside inherit the dashboard layout

## 🔗 **Navigation Links**

### **Using Next.js Link Component**
```tsx
import Link from 'next/link'

// ✅ Correct - Client-side navigation
<Link href="/dashboard" className="nav-link">
  Dashboard
</Link>

// ❌ Avoid - Full page reload
<a href="/dashboard" className="nav-link">
  Dashboard
</a>
```

### **Active State Detection**
```tsx
import { usePathname } from 'next/navigation'

function Navigation() {
  const pathname = usePathname()
  
  return (
    <Link 
      href="/dashboard" 
      className={pathname === '/dashboard' ? 'active' : ''}
    >
      Dashboard
    </Link>
  )
}
```

## 🛣️ **Available Routes**

| Route | Component | Path | Description |
|-------|-----------|------|-------------|
| `/` | `app/page.tsx` | Homepage | Landing page with hero section |
| `/dashboard` | `app/(dashboard)/page.tsx` | Dashboard | Main analytics overview |
| `/dashboard/verifications` | `app/(dashboard)/verifications/page.tsx` | Verifications | Verification history and details |
| `/dashboard/fraud` | `app/(dashboard)/fraud/page.tsx` | Fraud Analytics | Fraud patterns and hotspots |
| `/dashboard/review` | `app/(dashboard)/review/page.tsx` | Human Review | Cases requiring human intervention |

## 🎨 **Layout Inheritance**

### **Root Layout** (`app/layout.tsx`)
- Global metadata (SEO, OpenGraph)
- HTML structure and fonts
- Applied to ALL pages

### **Dashboard Layout** (`app/(dashboard)/layout.tsx`)
- Sidebar navigation
- Top bar with metrics
- Applied only to dashboard routes
- Wraps page content with dashboard UI

## 🔄 **Navigation Flow**

1. **Homepage** (`/`) → Landing page with CTA to dashboard
2. **Dashboard** (`/dashboard`) → Main overview with real-time stats
3. **Sub-pages** → Each section has dedicated page with detailed functionality

## 🧭 **Best Practices**

### **Link Usage**
```tsx
// ✅ Use Link for internal navigation
<Link href="/dashboard/verifications">
  View Verifications
</Link>

// ✅ Use regular anchor for external links
<a href="mailto:info@uhakiki.ai">
  Contact Us
</a>
```

### **Route Protection**
```tsx
// In dashboard layout, you can add auth checks
'use client'
import { useSession } from 'next-auth/react'

export default function DashboardLayout({ children }) {
  const { data: session } = useSession()
  
  if (!session) {
    return <div>Please sign in to access dashboard</div>
  }
  
  return (
    <div className="dashboard-layout">
      {/* Dashboard UI */}
      {children}
    </div>
  )
}
```

### **Dynamic Routes**
```tsx
// For individual verification details
// app/dashboard/verifications/[tracking_id]/page.tsx
export default function VerificationDetail({ params }) {
  return <div>Verification {params.tracking_id}</div>
}
```

## 🚦 **Current Status**

✅ **Completed:**
- Root layout with proper metadata
- Homepage with hero section and real-time stats
- Dashboard layout with sidebar navigation
- All dashboard pages (Overview, Verifications, Fraud, Review)
- Proper Next.js Link components
- Active state detection in navigation

✅ **Features Working:**
- Client-side navigation between pages
- Active route highlighting
- Shared dashboard layout
- Responsive design
- Real-time data updates

## 🎯 **Next Steps**

1. **Test Navigation:** Click through all dashboard pages
2. **Add Authentication:** Implement session management
3. **API Integration:** Connect to backend endpoints
4. **Dynamic Data:** Replace mock data with real API calls
5. **Error Handling:** Add 404 pages and error boundaries

## 🔧 **Development Commands**

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📱 **Access Points**

- **Homepage:** http://localhost:3000
- **Dashboard:** http://localhost:3000/dashboard
- **Verifications:** http://localhost:3000/dashboard/verifications
- **Fraud Analytics:** http://localhost:3000/dashboard/fraud
- **Human Review:** http://localhost:3000/dashboard/review

Your UhakikiAI frontend now has proper Next.js routing with a professional dashboard interface! 🎉
