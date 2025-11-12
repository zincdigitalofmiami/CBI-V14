# Dashboard Coding Standards

Component patterns, TypeScript types, styling guidelines.

## Structure

- **active/** - Current coding standards
- **old/** - Deprecated patterns
- **new/** - Proposed standards

## Topics

### Component Patterns
- Functional components
- Custom hooks
- Server vs Client components (Next.js 14)
- Error boundaries
- Loading states

### TypeScript Standards
- Interface vs Type
- Prop types
- API response types
- Utility types

### Styling Guidelines
- Tailwind conventions
- Component-specific styles
- Responsive design patterns
- Dark mode

### State Management
- React Context
- URL state
- Local storage
- Server state (React Query, SWR)

### API Patterns
- Route handlers
- Error handling
- Loading states
- Caching strategies

### Testing Standards
- Unit test patterns
- Component testing
- Integration testing
- E2E testing

## Example Documents

### Component Pattern:
```markdown
# Custom Hook Pattern

**Status:** Active  
**Category:** React Patterns

## Usage
```typescript
const useFeature = () => {
  // implementation
}
```

## Examples
- useVegasData()
- useForecast()

## Best Practices
1. Always memoize
2. Handle loading states
3. Error boundaries
```

### TypeScript Standard:
```markdown
# API Response Types

**Status:** Active  
**Category:** TypeScript

## Pattern
```typescript
interface ApiResponse<T> {
  data: T;
  error?: string;
  loading: boolean;
}
```

## Usage in Project
- Forecast API
- BigQuery responses
```







